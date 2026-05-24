import os
import time
import schedule
import ast
from volcenginesdkarkruntime import Ark
from datetime import datetime
from wxpusher import WxPusher
import juhe_news_01 as news_crwal


# ====================== 全局配置 ======================
current_file = __file__
current_path = os.path.abspath(os.path.join(current_file, os.pardir))
news_papers_path = os.path.abspath(os.path.join(current_path, 'juhe_news_papers'))

# ====================== 新闻保存模块 ======================
def save_news_to_txt(new_title, news_text, news_type, n):
    # 获取当前日期和小时
    now = datetime.now()
    current_date = now.strftime("%Y%m%d")
    current_hour = now.strftime("%H")

    # 构建子目录路径
    sub_dir = os.path.join(news_papers_path, current_date)

    # 如果子目录不存在，则创建
    if not os.path.exists(sub_dir):
        os.makedirs(sub_dir)

    # 构建子目录路径
    type_sub_dir = os.path.join(news_papers_path, current_date, news_type)

    # 如果子目录不存在，则创建
    if not os.path.exists(type_sub_dir):
        os.makedirs(type_sub_dir)


    # 构建文件名
    file_name = f"{news_type}_{current_date}_{current_hour}_{n}.txt"
    file_path = os.path.join(type_sub_dir, file_name)

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
def news_writing(new_title, new_url, news_type, n):
    # 模型调用
    client = Ark(api_key=os.environ.get("ARK_API_KEY"))
    completion = client.bot_chat.completions.create(
        model='bot-20250612100351-kr28l',
        messages=[
            {"role": "user", "content": f"新闻标题：{new_title}|URL：{new_url}"},
        ],
    )

    text = completion.choices[0].message.content
    lines = text.splitlines()
    non_empty_lines = [line for line in lines if line.strip()]
    news_text = '\n'.join(non_empty_lines)
    save_news_to_txt(new_title, news_text, news_type, n)  # 保存新闻文本到文件
    # send_message(news_text)  # 发送消息

def scheduled_task():
    # types = ['top','guonei','guoji','yule','tiyu','caijing','jiankang']
    types = ['guoji','yule','tiyu','caijing','jiankang', 'junshi']
    """定时任务入口"""
    print("开始执行定时任务...")

    for news_type in types:
        try:
            news_title_list = news_crwal.main(news_type)
            print(f'取回_{news_type}_新闻，共有{len(news_title_list)}条。')
        except Exception as e:
            print(f"取回_{news_type}_新闻时发生错误: {e}")

        n =1
        for new in news_title_list:
            new_title = new['title']
            new_url = new['url']
            try:
                news_writing(new_title, new_url, news_type, n)
                n += 1
                print(f'已撰写完成新闻：{new_title}')
            except Exception as e:
                print(f"撰写新闻时发生错误: {e}")


# ====================== 主程序入口 ======================
if __name__ == "__main__":
    # 设置定时任务，每天上午02:30、下午14:30执行
    schedule.every().day.at("02:30").do(scheduled_task)
    schedule.every().day.at("14:30").do(scheduled_task)


    # 立即执行一次
    #scheduled_task()

    # 任务循环
    while True:
        schedule.run_pending()
        time.sleep(600)