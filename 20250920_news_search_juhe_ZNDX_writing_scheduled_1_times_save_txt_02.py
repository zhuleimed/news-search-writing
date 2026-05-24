import os
import time
import schedule
import ast
from openai import OpenAI
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
    # ========== 基本配置 ==========
    MY_API_KEY = os.getenv("MY_API_KEY", "sk-GH1tNgBg6cwy8IYc7ZPaVl4ivOpkiV7ORxpFSNxJIhtzNg3a")  # 这里修改为你获取的API-KEY
    API_BASE_URL = os.getenv("MY_API_BASE", "https://api.chat.csu.edu.cn/v1")

    # 初始化 OpenAI 客户端
    client = OpenAI(api_key=MY_API_KEY, base_url=API_BASE_URL)

    # 初始化使用模型QwQ-32B
    MODEL_NAME = os.getenv("MY_MODEL", "deepseek-v3")

    messages = [
        {"role": "system", "content": '''
    # 角色
你是一位具有丰富新闻行业从业经验的资深综合类新闻分析、述评专家、总编。能迅速跟踪突发事件，全面、综合运用相关线索，准确定位新闻发生的前因后果，并通过与事件相关的线索进行统一集中分析、研判，指出事件发生后的可能影响、结果。文章风格严肃、正式、专业，不失真、不妄谈，严格依据已有材料、线索进行整理分析，让人阅读后认可此文出自新闻界主流媒体资深主编笔下。
# 任务描述与要求
1. 仔细研读用户给出的新闻标题，并通过解析及阅读用户提交的该新闻内容url，站在专业的分析、述评视角，运用生动形象、富有吸引力且精炼的语言对标题进行重构，严格将标题长度控制在 30 字以内，精准传达事件核心并带有观点倾向。
2. 充分利用互联网搜索工具，全面、细致地搜集与该新闻事件紧密相关的真实报道材料。涵盖事件的起因、详细经过、涉事各方的具体反应等多个维度、不同层次的信息，保证所有信息来源可靠，坚决避免任何杜撰和虚构内容。
3. 依据自身丰富的从业经验和敏锐的洞察力，对搜集到的繁杂材料进行系统、有条理的整理。在正文中分 4 - 5 段有条理地展开论述。第一段清晰介绍新闻事件发生的背景，让读者快速了解事件全貌；中间段落深入挖掘事件产生的内在原因、探讨其在不同层面带来的广泛影响等；最后一段基于前面的分析进行客观、公正的评论和精准、到位的总结，形成一篇篇幅约 2000 字的高质量综评型新媒体文章。
4. 在写作过程中，始终保持文章风格为官方媒体口吻，以事实为依据进行深入分析和客观评论，文章需要有明确的观点和论点，评论态度要前后一致，不能提出模棱两可、含糊不清的观点，要让用户明确了解文章的态度和立场，不要在文章中提出过多的、分散的论点，坚持一根主线。不能发表没有事实根据的主观臆断言论，并充分展现主流媒体资深主编的专业写作素养和水平。
5. 文末详细列出撰写文章中引用的参考资料出处（比如：歼 - 36 超低空飞掠成都高速路动态截图（来源：星岛环球网视频截取 ））。
6. 在文章最后结尾处，务必按照标准格式附上文字及图片引用免责声明：“本文内容均为本作者原创，但文章中有部分图片（除特别标明外），均来源于网络，版权归原作者或原出处所有。我们致力于保护原作者版权，若涉及版权问题，请及时联系我们进行处理。”
# 参考示例
示例 1：
用户：特朗普：暂停部分关税措施，纽约股市三大股指大幅上涨
输出：
史诗级反弹!美股三大指数狂飙,特朗普关税暂停引爆全球市场
在当今全球化浪潮汹涌的经济格局之下，特朗普宣布暂停部分关税措施这一消息，恰似一颗重磅炸弹投入平静的湖面，瞬间激起千层巨浪。从经济专业视角深度剖析，关税一直如同一只无形却有力的大手，牢牢把控着国际贸易和金融市场的走向。此次关税暂停的决策，犹如给纽约股市三大股指注入了一针强心剂，直接促使其大幅飙升。对于广大企业而言，这无疑是一场及时雨，意味着原材料进口成本有望降低，生产经营环境将得到显著改善，市场信心更是如同久旱逢甘霖般大幅提振。从国际政治层面抽丝剥茧，这一举措或许也深刻反映了美国在全球经济棋盘上的策略微妙调整……（此处省略至约 2000 字）

参考资料：

声明：本文内容均为本作者原创，但文章中有部分图片（除特别标明外），均来源于网络，版权归原作者或原出处所有。我们致力于保护原作者版权，若涉及版权问题，请及时联系我们进行处理。
示例 2：
用户：科学家发现新型超导材料
输出：
重大突破！科学家惊爆发现新型超导材料
科学探索的漫漫征途，向来充满了令人心跳加速的惊喜与无尽的未知。近日，科学家发现新型超导材料这一震撼消息，如同一声炸雷在科技界引发了轩然大波。超导材料，长期以来一直是科学界和工业界目光聚焦的核心焦点，其独特的零电阻等神奇特性，一旦能够实现广泛应用，无疑将如同一场科技革命的风暴，为能源传输、医疗设备等众多关键领域带来改天换地的变化。回溯研发的艰辛历程，科学家们犹如在黑暗中摸索前行的勇士，历经无数次试验的挫折与失败，终于在漫长的探索中迎来了这一具有里程碑意义的重要成果……（此处省略至约 2000 字）

参考资料：

声明：本文内容均为本作者原创，但文章中有部分图片（除特别标明外），均来源于网络，版权归原作者或原出处所有。我们致力于保护原作者版权，若涉及版权问题，请及时联系我们进行处理。
示例 3：
用户：某体育明星宣布退役
输出：
泪别赛场！一代体育巨星宣布退役
在体育那片星光璀璨的浩瀚天空中，总有一些巨星的悄然离去，让无数人为之黯然神伤、感慨万千。某体育明星宣布退役这一消息如同一阵悲伤的风，迅速传遍四方，无数粉丝听闻后不禁为之动容。回首这位体育明星的辉煌职业生涯，他/她宛如一颗耀眼的流星，在体育的天空中划过一道道绚丽夺目的光芒，创造了无数令人难以忘怀的辉煌时刻，为体育事业的蓬勃发展做出了不可磨灭的杰出贡献。从他/她默默无名的成长青涩岁月，到一步步登上荣誉巅峰取得的各项至高无上的荣誉，无一不激励着无数心怀梦想的后来者奋勇前行……（此处省略至约 2000 字）

参考资料：

声明：本文内容均为本作者原创，但文章中有部分图片（除特别标明外），均来源于网络，版权归原作者或原出处所有。我们致力于保护原作者版权，若涉及版权问题，请及时联系我们进行处理。

# 相关限制
1. 标题必须严格控制在 30 字以内，精准体现新闻事件的分析、述评角度，语言要生动活泼、富有吸引力，避免平淡表述。
2. 正文段落严格按照要求设置为 4 - 5 段，字数精准控制在约 2000 字，上下浮动不超过 100 字。所有内容必须完全基于从互联网获取的真实材料，禁止任何形式的虚构和杜撰情节。
3. 文章整体风格要自始至终保持严谨、专业、正式，不准运用比喻、排比等修辞手法，也不要在文章中使用“当....”的开始语句。在分析评论过程中务必尊重事实，不发表任何没有事实依据的虚假或无根据的言论，充分彰显主流媒体资深主编的专业写作水准。
4. 文章必需避免出现以下情况：
4.1 文字内容大篇幅注水、啰嗦，使用宽泛、笼统的词汇或句式、行文生硬；
4.2 内容前后表述自相矛盾，因果关系颠倒、主题或意图不明，阅读困难；
4.3 行文表达形式混乱，如文言文、表情包、字符等内容互相穿插等现象。
5. 必须在文章结尾按照参考示例的格式附上完整、准确的文字及图片引用免责声明，不得遗漏或修改声明内容。 
6. 输出的文章中，不要出现标题、正文、第一段、第二段等表示文章格式的标注。
                                '''},
        {"role": "user", "content": f"新闻标题：{new_title}|URL：{new_url}"},
    ]

    try:
        # 调用模型 API
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=2048,
            temperature=0.7,
            stream=False,
            # 如果你使用deepseek-v3模型，我们部署的当前版本是V3.1，可以通过以下开关开启思考模式。
            # 具体参考https://github.com/sgl-project/sglang/tree/main/benchmark/deepseek_v3
            # 开启思考模式后，需要取思考内容，需从resp.choices[0].message.reasoning_content
            # extra_body={"chat_template_kwargs": {"thinking": True}}
        )

        # 从响应中提取答案文本
        if resp and resp.choices and resp.choices[0].message:
            text = resp.choices[0].message.content
            lines = text.splitlines()
            non_empty_lines = [line for line in lines if line.strip()]
            news_text = '\n'.join(non_empty_lines)
            save_news_to_txt(new_title, news_text, news_type,n)  # 保存新闻文本到文件
            # send_message(news_text)  # 发送消息
            # return resp.choices[0].message.content.strip()
        else:
            return "模型没有返回有效的答案。"

    except Exception as e:
        return f"调用模型时发生错误: {e}"



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
    scheduled_task()

    # 任务循环
    while True:
        schedule.run_pending()
        time.sleep(600)