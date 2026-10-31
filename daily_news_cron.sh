#!/bin/bash
# ============================================================
# 百度热榜新闻解读 —— 每日定时任务
#
# 由 crontab 每天 5:00 启动：
#   0 5 * * * /public/home/hpc/zhulei/superman/quant/code/news_search_writing/daily_news_cron.sh
#
# 特点：
#   - flock 防止同一时间跑两个任务；
#   - 日志按日期写到 logs/cron/；
#   - timeout 3 小时，防止卡死；
#   - 支持 DRY_RUN=1 干跑，只打印将要执行的命令。
# ============================================================

set -uo pipefail

# ---------- 固定路径与运行环境 ----------
PROJECT_DIR="/public/home/hpc/zhulei/superman/quant/code/news_search_writing"
CLAUDE_BIN="/home/zhulei/.npm-global/bin/claude"
LOG_DIR="$PROJECT_DIR/logs/cron"

# cron 的 PATH 通常很短，这里显式补上 python 和 claude 的路径
export PATH="/home/zhulei/anaconda3/bin:/home/zhulei/.npm-global/bin:/usr/local/bin:/usr/bin:/bin"
export HOME="/home/zhulei"
export LANG="C.UTF-8"

# 认证环境：cron 不会继承交互式登录 shell 的 ANTHROPIC_AUTH_TOKEN。
# 这个文件在仓库之外、权限 600，不能提交到 git。
CLAUDE_ENV_FILE="/home/zhulei/.config/news_search_writing/claude_env.sh"
if [ ! -f "$CLAUDE_ENV_FILE" ]; then
    echo "错误：缺少认证环境文件 $CLAUDE_ENV_FILE"
    echo "请在有登录环境的终端重新生成（见 NEWS_WORKFLOW_OPERATIONS_GUIDE.md 第 11.10 节）"
    exit 1
fi
# shellcheck disable=SC1090
. "$CLAUDE_ENV_FILE"

if [ -z "${ANTHROPIC_AUTH_TOKEN:-}" ] || [ -z "${ANTHROPIC_BASE_URL:-}" ]; then
    echo "错误：认证变量未设置（ANTHROPIC_AUTH_TOKEN/ANTHROPIC_BASE_URL）"
    exit 1
fi
echo "认证环境：已加载（base_url=${ANTHROPIC_BASE_URL}）"

# 预检 1：claude 必须存在
if [ ! -x "$CLAUDE_BIN" ]; then
    echo "错误：找不到可执行的 claude：$CLAUDE_BIN"
    exit 1
fi

# 预检 2：deepseek 代理没起来的话，claude 会失败；尝试拉起
if ! pgrep -f "deepseek_proxy.py" >/dev/null 2>&1; then
    echo "警告：deepseek_proxy 未运行，尝试启动..."
    nohup python3 /home/zhulei/.claude/deepseek_proxy.py >/tmp/deepseek_proxy.log 2>&1 &
    sleep 3
fi

mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/news_$(date +%Y%m%d_%H%M).log"
exec >> "$LOG_FILE" 2>&1

echo "============================================================"
echo "开始时间：$(date '+%Y-%m-%d %H:%M:%S')"
echo "工作目录：$PROJECT_DIR"

cd "$PROJECT_DIR" || {
    echo "错误：无法进入项目目录 $PROJECT_DIR"
    exit 1
}

# ---------- 防止重叠运行 ----------
exec 9>"/tmp/news_search_writing_daily.lock"
if ! flock -n 9; then
    echo "已有任务在运行，本次跳过。"
    exit 0
fi

# ---------- 给 Claude Code 的指令 ----------
PROMPT='读取并严格执行 /public/home/hpc/zhulei/superman/quant/code/news_search_writing/.claude/commands/news-write.md 的完整流程：抓取百度热榜、过滤涉政和股市实时行情，然后从过滤后的全部候选里按 TOPIC_SELECTION_GUIDE.md 评审并选出10条+备选（不要直接取前10条），再写作、配图、生成docx、质检、生成索引。正文1200～1500字，4～5段；正文不出现参考资料，来源另存 _sources.json；文末只保留一句图片版权声明。不要询问，直接执行完。'

if [ "${DRY_RUN:-0}" = "1" ]; then
    echo "[DRY_RUN] 将要执行："
    echo "$CLAUDE_BIN -p \"$PROMPT\" --dangerously-skip-permissions"
    exit 0
fi

# ---------- 预检 3：认证是否真的可用 ----------
echo "claude 认证预检..."
if ! timeout 60 "$CLAUDE_BIN" -p "只回答两个字：正常" --dangerously-skip-permissions >/tmp/news_claude_preflight.log 2>&1; then
    echo "错误：claude 认证预检失败，见 /tmp/news_claude_preflight.log"
    tail -5 /tmp/news_claude_preflight.log
    exit 1
fi
echo "claude 认证预检：通过"

if [ "${PREFLIGHT_ONLY:-0}" = "1" ]; then
    echo "[PREFLIGHT_ONLY] 认证预检通过，退出。"
    exit 0
fi

# ---------- 正式执行（最长 3 小时） ----------
timeout 10800 "$CLAUDE_BIN" -p "$PROMPT" --dangerously-skip-permissions
status=$?

echo "结束时间：$(date '+%Y-%m-%d %H:%M:%S')"
echo "退出码：$status"
echo "$(date '+%Y-%m-%d %H:%M:%S') exit=$status" > "$LOG_DIR/last_status.txt"

exit $status
