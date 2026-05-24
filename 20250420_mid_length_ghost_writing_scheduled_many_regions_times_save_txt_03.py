import os
import time
import schedule
import ast
from volcenginesdkarkruntime import Ark
from datetime import datetime
from wxpusher import WxPusher
import baidu_news_crwal_08 as news_crwal

# 全局配置
current_file = __file__
current_path = os.path.abspath(os.path.join(current_file, os.pardir))
news_papers_path = os.path.abspath(os.path.join(current_path, 'novels'))

# 地区列表
regions = [' 澳门 ', ' 台湾省 ', ' 乌鲁木齐市 ', ' 江西省 ', ' 福州市 ', ' 菲律宾 ', ' 青海省 ', ' 乌兹别克斯坦 ', ' 云南省 ', ' 河南省 ', ' 兰州市 ', ' 安徽省 ', ' 济南市 ', ' 北京市 ', ' 日本 ', ' 太原市 ', ' 哈尔滨市 ', ' 泰国 ', ' 湖南省 ', ' 呼和浩特市 ', ' 吉林省 ', ' 重庆市 ', ' 香港特别行政区 ', ' 武汉市 ', ' 大洋洲 ', ' 新加坡 ', ' 沙特阿拉伯 ', ' 浙江省 ', ' 印度尼西亚 ', ' 江苏省 ', ' 西藏自治区 ', ' 贵阳市 ', ' 银川市 ', ' 西安市 ', ' 河北省 ', ' 意大利 ', ' 上海市 ', ' 瑞典 ', ' 长春市 ', ' 西宁市 ', ' 肯尼亚 ', ' 天津市 ', ' 哈萨克斯坦 ', ' 甘肃省 ', ' 广东省 ', ' 新疆维吾尔自治区 ', ' 辽宁省 ', ' 澳大利亚 ', ' 南京市 ', ' 湖北省 ', ' 南昌市 ', ' 新西兰 ', ' 马来西亚 ', ' 巴西 ', ' 拉萨市 ', ' 南美洲 ', ' 郑州市 ', ' 四川省 ', ' 丹麦 ', ' 香港 ', ' 贵州省 ', ' 南亚 ', ' 广西壮族自治区 ', ' 昆明市 ', ' 海南省 ', ' 北美洲 ', ' 长沙市 ', ' 福州市 ', ' 埃及 ', ' 智利 ', ' 波兰 ', ' 阿根廷 ', ' 福建省 ', ' 中东 ', ' 孟加拉国 ', ' 秘鲁 ', ' 东南亚 ', ' 北欧 ', ' 太原市 ', ' 印度 ', ' 山西省 ', ' 英国 ', ' 内蒙古自治区 ', ' 加拿大 ', ' 挪威 ', ' 乌鲁木齐市 ', ' 乌克兰 ', ' 合肥市 ', ' 俄罗斯 ', ' 德国 ', ' 青海省 ', ' 广西壮族自治区 ', ' 大洋洲 ', ' 兰州市 ', ' 石家庄市 ', ' 哈尔滨市 ', ' 济南市 ', ' 河南省 ', ' 武汉市 ', ' 呼和浩特市 ', ' 长春市 ', ' 西宁市 ', ' 银川市 ', ' 西安市 ', ' 江苏省 ', ' 浙江省 ', ' 安徽省 ', ' 福建省 ', ' 江西省 ', ' 山东省 ', ' 湖北省 ', ' 湖南省 ', ' 广东省 ', ' 海南省 ', ' 四川省 ', ' 贵州省 ', ' 云南省 ', ' 重庆市 ', ' 西藏自治区 ', ' 陕西省 ', ' 甘肃省 ', ' 宁夏回族自治区 ', ' 新疆维吾尔自治区 ', ' 香港特别行政区 ', ' 澳门特别行政区 ', ' 台湾省 ', ' 北京市 ', ' 天津市 ', ' 上海市 ', ' 北美 ', ' 加拿大 ', ' 东亚 ', ' 中国 ', ' 日本 ', ' 西欧 ', ' 英国 ', ' 法国 ', ' 德国 ', ' 意大利 ', ' 北欧 ', ' 瑞典 ', ' 挪威 ', ' 丹麦 ', ' 东欧 ', ' 俄罗斯 ', ' 乌克兰 ', ' 波兰 ', ' 中东 ', ' 沙特阿拉伯 ', ' 伊朗 ', ' 伊拉克 ', ' 以色列 ', ' 土耳其 ', ' 中亚 ', ' 哈萨克斯坦 ', ' 吉尔吉斯斯坦 ', ' 乌兹别克斯坦 ', ' 南亚 ', ' 印度 ', ' 巴基斯坦 ', ' 孟加拉国 ', ' 东南亚 ', ' 印度尼西亚 ', ' 马来西亚 ', ' 泰国 ', ' 菲律宾 ', ' 澳大利亚 ', ' 大洋洲 ', ' 新西兰 ', ' 南非 ', ' 非洲 ', ' 埃及 ', ' 尼日利亚 ', ' 肯尼亚 ', ' 南美洲 ', ' 巴西 ', ' 阿根廷 ', ' 智利 ', ' 秘鲁 ', ' 哥伦比亚 ', ' 委内瑞拉 ']

# 记录当前选取的列表索引
current_index = 0

# 新闻保存模块
def save_news_to_txt(current_date, current_hour, news_text):
    # 构建子目录路径
    sub_dir = os.path.join(news_papers_path, current_date)

    # 如果子目录不存在，则创建
    if not os.path.exists(sub_dir):
        os.makedirs(sub_dir)

    # 构建文件名
    file_name = f"{current_date}_{current_hour}_doubao_mid_ghost.txt"
    file_path = os.path.join(sub_dir, file_name)

    # 保存新闻文本到文件
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(news_text)
        print(f"中篇故事已成功保存到 {file_path}")
    except Exception as e:
        print(f"保存文件时出现错误: {e}")

# 消息推送模块
def send_message(current_date, current_hour, news_text):
    words = current_date + current_hour + '中篇故事：\n' + news_text

    WxPusher.send_message(
        words,
        uids=['<uids>'],
        topic_ids=['39277'],
        token='AT_hKGG0UfwrCP7bpcsO8cbQkrc4bZ9G3RX'
    )
    print('消息推送完成')

# 新闻写作模块
def news_writing(current_date, current_hour):
    global current_index
    # 选取4个地方
    selected_regions = []
    for _ in range(1):
        selected_regions.append(regions[current_index].strip())
        current_index = (current_index + 1) % len(regions)

    # 构建请求内容
    content = f"好的，请继续选取{', '.join(selected_regions)}地方的题材，严格按照文章撰写及输出要求，各生成1篇不同地域、不同时期、不同案例的，独立中篇故事，投稿平台为知乎，故事正文字数一定要在5000汉字以上。要求每个故事的题材均为未撰写过的题材。"

    # 模型调用
    client = Ark(api_key=os.environ.get("ARK_API_KEY"))
    completion = client.bot_chat.completions.create(
        model='bot-20250418220914-d4d84',
        messages=[
            {"role": "user", "content": content},
        ]
    )

    text = completion.choices[0].message.content
    lines = text.splitlines()
    non_empty_lines = [line for line in lines if line.strip()]
    news_text = '\n'.join(non_empty_lines)
    save_news_to_txt(current_date, current_hour, news_text)  # 保存新闻文本到文件
    #send_message(current_date, current_hour, news_text)  # 发送消息

def scheduled_task():
    print("开始执行定时任务...")
    # 获取当前日期和小时
    now = datetime.now()
    current_date = now.strftime("%Y%m%d")
    current_hour = now.strftime("%H_%M")
    try:
        print(f'准备撰写{current_date}_{current_hour}时间的中篇故事')
        news_writing(current_date, current_hour)
    except Exception as e:
        print(f"撰写中篇故事发生错误: {e}")

# 主程序入口
if __name__ == "__main__":
    # 设置定时任务
    schedule.every().day.at("07:10").do(scheduled_task)
    schedule.every().day.at("07:20").do(scheduled_task)
    schedule.every().day.at("07:30").do(scheduled_task)
    schedule.every().day.at("07:40").do(scheduled_task)
    schedule.every().day.at("07:50").do(scheduled_task)
    #schedule.every().day.at("11:50").do(scheduled_task)
    #schedule.every().day.at("12:30").do(scheduled_task)
    #schedule.every().day.at("13:00").do(scheduled_task)

    # 立即执行一次
    scheduled_task()

    # 任务循环
    while True:
        schedule.run_pending()
        time.sleep(600)