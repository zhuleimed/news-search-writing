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
def save_news_to_txt(current_date, current_hour, news_text):
    # 构建子目录路径
    sub_dir = os.path.join(news_papers_path, current_date)

    # 如果子目录不存在，则创建
    if not os.path.exists(sub_dir):
        os.makedirs(sub_dir)

    # 构建文件名
    file_name = f"{current_date}_{current_hour}_doubao.txt"
    file_path = os.path.join(sub_dir, file_name)

    # 保存新闻文本到文件
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(news_text)
        print(f"新闻文本已成功保存到 {file_path}")
    except Exception as e:
        print(f"保存文件时出现错误: {e}")


# ====================== 消息推送模块 ======================
def send_message(current_date, current_hour, news_text):
    words = current_date + current_hour + '新闻：\n' + news_text

    WxPusher.send_message(
        words,
        uids=['<uids>'],
        topic_ids=['39277'],
        token='AT_hKGG0UfwrCP7bpcsO8cbQkrc4bZ9G3RX'
    )
    print('消息推送完成')


# ====================== 新闻写作模块 ======================
def news_writing(current_date, current_hour):
    # 模型调用
    client = Ark(api_key=os.environ.get("ARK_API_KEY"))
    completion = client.bot_chat.completions.create(
        model='bot-20250418100105-z2jnp',
        messages=[
            {"role": "user", "content": "请按要求撰写3篇不同主题类型的文章。"},
        ]
    )

    text = completion.choices[0].message.content
    lines = text.splitlines()
    non_empty_lines = [line for line in lines if line.strip()]
    news_text = '\n'.join(non_empty_lines)
    save_news_to_txt(current_date, current_hour, news_text)  # 保存新闻文本到文件
    send_message(current_date, current_hour, news_text)  # 发送消息


def scheduled_task():
    print("开始执行定时任务...")
    # 获取当前日期和小时
    now = datetime.now()
    current_date = now.strftime("%Y%m%d")
    current_hour = now.strftime("%H")
    try:
        print(f'准备撰写{current_date}_{current_hour}时间新闻')
        news_writing(current_date, current_hour)
    except Exception as e:
        print(f"撰写新闻时发生错误: {e}")


# ====================== 主程序入口 ======================
if __name__ == "__main__":
    # 设置定时任务
    schedule.every().day.at("01:00").do(scheduled_task)
    schedule.every().day.at("03:00").do(scheduled_task)
    schedule.every().day.at("05:00").do(scheduled_task)
    schedule.every().day.at("07:30").do(scheduled_task)
    schedule.every().day.at("10:30").do(scheduled_task)
    schedule.every().day.at("11:30").do(scheduled_task)
    schedule.every().day.at("13:00").do(scheduled_task)
    schedule.every().day.at("14:30").do(scheduled_task)
    schedule.every().day.at("15:00").do(scheduled_task)
    schedule.every().day.at("16:00").do(scheduled_task)
    schedule.every().day.at("17:00").do(scheduled_task)
    schedule.every().day.at("18:00").do(scheduled_task)
    schedule.every().day.at("19:00").do(scheduled_task)


    # 立即执行一次
    scheduled_task()

    # 任务循环
    while True:
        schedule.run_pending()
        time.sleep(600)