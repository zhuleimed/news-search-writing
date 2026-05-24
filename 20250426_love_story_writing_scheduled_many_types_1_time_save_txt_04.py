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
news_papers_path = os.path.abspath(os.path.join(current_path, 'news_papers'))

# 类型列表
types = ['家庭亲情类', '职场成长类', '教育代际类', '兴趣理想类', '邻里温情类', '职场人际类', '代际沟通类', '自我成长类', '婚姻观察类', '老年生活类', '友情变迁类', '职场选择类', '生活哲理类', '代际冲突类', '老年孤独类', '再婚家庭类', '异地养老类', '职场师徒类', '老年相亲类', '留守儿童类', '病友互助类', '非遗传承类', '单亲妈妈类', '职场转型类', '临终书信类', '校园霸凌类', '职场压力类', '宠物纪念类', '退休适应类', '网络时代类']
# 记录当前选取的列表索引
current_index = 0

# 新闻保存模块
def save_news_to_txt(current_date, current_hour, news_text, n):
    # 构建子目录路径
    sub_dir = os.path.join(news_papers_path, current_date)

    # 如果子目录不存在，则创建
    if not os.path.exists(sub_dir):
        os.makedirs(sub_dir)

    # 构建文件名
    file_name = f"{current_date}_{current_hour}_love_story_{n}.txt"
    file_path = os.path.join(sub_dir, file_name)

    # 保存新闻文本到文件
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(news_text)
        print(f"情感{n}故事已成功保存到 {file_path}")
    except Exception as e:
        print(f"保存文件时出现错误: {e}")

# 消息推送模块
def send_message(current_date, current_hour, news_text):
    words = current_date + current_hour + '情感故事：\n' + news_text

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
    # 选取5个地方
    selected_types = []

    for _ in range(5):
        selected_types.append(types[current_index].strip())
        current_index = (current_index + 1) % len(types)

    n = 1
    for story in selected_types:
        # 构建请求内容
        content = f"请再仿写一篇{story}的网文。注意！不要重复已创作的题材，请选择新的创作素材。"

        # 模型调用
        client = Ark(api_key=os.environ.get("ARK_API_KEY"))
        completion = client.bot_chat.completions.create(
            model='bot-20250426115716-l8x6w',
            messages=[
                {"role": "user", "content": content},
            ]
        )

        text = completion.choices[0].message.content
        lines = text.splitlines()
        non_empty_lines = [line for line in lines if line.strip()]
        news_text = '\n'.join(non_empty_lines)
        save_news_to_txt(current_date, current_hour, news_text, n)  # 保存新闻文本到文件
        n += 1
        #send_message(current_date, current_hour, news_text)  # 发送消息

def scheduled_task():
    print("开始执行定时任务...")
    # 获取当前日期和小时
    now = datetime.now()
    current_date = now.strftime("%Y%m%d")
    current_hour = now.strftime("%H")
    try:
        print(f'准备撰写{current_date}_{current_hour}时间的情感故事')
        news_writing(current_date, current_hour)
    except Exception as e:
        print(f"撰写情感故事发生错误: {e}")

# 主程序入口
if __name__ == "__main__":
    # 设置定时任务
    schedule.every().day.at("05:00").do(scheduled_task)


    # 立即执行一次
    scheduled_task()

    # 任务循环
    while True:
        schedule.run_pending()
        time.sleep(600)