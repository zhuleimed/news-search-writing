import os
import time
import schedule
import ast
from volcenginesdkarkruntime import Ark
from datetime import datetime
from wxpusher import WxPusher
import baidu_news_crwal_08 as news_crwal


# ====================== 全局配置 ======================
current_file = __file__
current_path = os.path.abspath(os.path.join(current_file, os.pardir))
news_papers_path = os.path.abspath(os.path.join(current_path, 'news_papers'))

# ====================== 新闻保存模块 ======================
def save_news_to_txt(new_title, news_text):
    # 获取当前日期和小时
    now = datetime.now()
    current_date = now.strftime("%Y%m%d")
    current_hour = now.strftime("%H")

    # 构建子目录路径
    sub_dir = os.path.join(news_papers_path, current_date)

    # 如果子目录不存在，则创建
    if not os.path.exists(sub_dir):
        os.makedirs(sub_dir)

    new_title = new_title.replace(' ', '_')
    # 构建文件名
    file_name = f"{current_date}_{current_hour}_{new_title}.txt"
    file_path = os.path.join(sub_dir, file_name)

    # 保存新闻文本到文件
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(news_text)
        print(f"新闻文本已成功保存到 {file_path}")
    except Exception as e:
        print(f"保存文件时出现错误: {e}")


# ====================== 消息推送模块 ======================
def send_message(news_text):
    """完整保留消息推送逻辑"""
    # 获取今天的日期
    today = datetime.today()
    today_str = today.strftime("%Y-%m-%d")

    now = datetime.now()
    print(now.hour)
    if now.hour >= 5 and now.hour < 7:
        time_str = '晨间'
    elif now.hour >= 16 and now.hour < 17:
        time_str = '午后'
    else:
        time_str = ''
    words = today_str + time_str + '新闻：\n' + news_text

    WxPusher.send_message(
        words,
        uids=['<uids>'],
        topic_ids=['39277'],
        token='AT_hKGG0UfwrCP7bpcsO8cbQkrc4bZ9G3RX'
    )
    print('消息推送完成')


# ====================== 新闻写作模块 ======================
def news_writing(new_title):
    # 模型调用
    client = Ark(api_key=os.environ.get("ARK_API_KEY"))
    completion = client.bot_chat.completions.create(
        model='bot-20250425080402-2fc7c',
        messages=[

            {"role": "user", "content": new_title},
        ]
    )

    text = completion.choices[0].message.content
    lines = text.splitlines()
    non_empty_lines = [line for line in lines if line.strip()]
    news_text = '\n'.join(non_empty_lines)
    save_news_to_txt(new_title, news_text)  # 保存新闻文本到文件
    send_message(news_text)  # 发送消息

# ====================== 定时任务模块 ======================
def doubao_news_search(search_news_title_url):
    input_strategy = f"请搜索以下网址的新闻标题：{search_news_title_url}"
    client = Ark(api_key=os.environ.get("ARK_API_KEY"))
    completion = client.bot_chat.completions.create(
        model='bot-20250409171650-68clj',
        messages=[
#             {"role": "system", "content": '''
#                 # 角色
# 你是一位能力卓越的网络媒体工作者和网络数据搜索分析师，拥有自主研发的智能算法与垂直领域知识库，致力于为用户提供精准化新闻标题筛选服务。
# # 任务描述与要求
# 1. 多模态数据抓取：
#     - 针对指定网页、新闻 API 接口以及社交媒体平台展开实时数据采集工作。
#     - 熟练支持 HTML/JSON/XML 等多种格式解析，能够迅速且准确地自动识别诸如 JS 动态渲染、IP 封禁等反爬机制，并运用智能规避策略确保数据抓取顺利进行。
# 2. 智能清洗与过滤：
#     - 利用自然语言处理（NLP）技术精心构建标题质量评估模型：
#         - 广告识别：借助正则表达式匹配以及关键词黑名单过滤，精准识别并剔除包含“限时优惠”“点击领取”等关键词的广告标题。
#         - 重复检测：通过 SimHash 算法计算文本指纹，对相似度过 85% 的重复标题进行有效识别。
#         - 语义校验：运用 BERT 模型实施情感分析，去除带有“震惊！”“痛心！”等情绪化表达的标题。
# 3. 标题规范化处理：
#     - 执行标准化操作：
#         - 格式统一：将日期等数字统一使用阿拉伯数字，如“2025 年”；规范标点符号使用，统一采用全角标点。
#         - 冗余去除：果断删除“最新消息：”“重磅！”等冗余前缀。
#         - 信息补全：对于缺失时间、地点等关键要素的标题，通过语义推断进行合理补充。
# 4. 多维筛选机制：
#     - 构建三级筛选体系：
#         - 基础层：基于 TF-IDF 算法准确提取关键词，严格过滤娱乐八卦、明星绯闻等非新闻类内容。
#         - 价值层：通过事件影响力模型，综合传播广度、媒体转载量、专家评分等因素，客观评估新闻的重要性。
#         - 传播层：运用情感分析与传播预测模型，筛选出具有争议性、突破性等强话题性的标题。
# 5. 领域覆盖要求：
#     - 严格依照新闻价值五要素（及时性、重要性、显著性、接近性、趣味性）开展工作，确保：
#         - 国际与国内新闻比例控制在 4:6 至 6:4 之间。
#         - 领域分布合理：政治领域占比 15%，经济领域占比 15%，军事领域占比 15%，科技领域占比 20%，体育领域占比 15%，娱乐领域占比 10%，民生领域占比 10%。
#         - 地域均衡：全面覆盖五大洲主要国家，在国内重点关注京津冀、长三角、粤港澳大湾区的新闻。
# 6. 输出规范：
#     - 采用列表形式输出，标题需遵循特定格式：
#         - 主标题：实词首字母大写，使用冒号分隔核心信息，例如“国防部：解放军台海演训震慑分裂势力”。
#         - 副标题：必要时添加，使用破折号引导，例如“中国量子计算机突破：算力达谷歌 54 倍”。
# 7. 数量控制:
#        -严格按照领域覆盖要求，输出新闻标题数量控制在15个以内，若不足15个，按实际数量输出。
#                 '''},
            {"role": "user", "content": input_strategy},
        ]
    )
    return ast.literal_eval(completion.choices[0].message.content)


def scheduled_task():
    search_news_title_url = "https://top.baidu.com/board?tab=realtime"
    """定时任务入口"""
    print("开始执行定时任务...")
    try:
        news_title_list = news_crwal.main(search_news_title_url)
        print(f'推荐的新闻标题是：{news_title_list}')
    except Exception as e:
        print(f"搜索新闻标题时发生错误: {e}")

    for new_title in news_title_list:
        new_title = new_title.split('|')[0].split('标题: ')[1]
        try:
            news_writing(new_title)
            print(f'已撰写完成新闻：{new_title}')
        except Exception as e:
            print(f"撰写新闻时发生错误: {e}")


# ====================== 主程序入口 ======================
if __name__ == "__main__":
    # 设置定时任务，每天上午05:30、下午16:00执行
    schedule.every().day.at("05:30").do(scheduled_task)
    schedule.every().day.at("16:00").do(scheduled_task)


    # 立即执行一次
    scheduled_task()

    # 任务循环
    while True:
        schedule.run_pending()
        time.sleep(600)