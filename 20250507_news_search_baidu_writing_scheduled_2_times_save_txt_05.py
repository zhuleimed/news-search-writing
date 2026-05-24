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
def save_news_to_txt(new_title, news_text, n):
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
    file_name = f"{current_date}_{current_hour}_{n}.txt"
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
def news_writing(new_title, n):
    # 模型调用
    client = Ark(api_key=os.environ.get("ARK_API_KEY"))
    completion = client.bot_chat.completions.create(
        model='bot-20250410082948-vkvwk',
        messages=[
                        {"role": "system", "content": '''
                            # 角色
            你是一位具有丰富新闻行业从业经验的资深综合类新闻分析、述评专家、总编。能迅速跟踪突发事件，全面、综合运用相关线索，准确定位新闻发生的前因后果，并通过与事件相关的线索进行统一集中分析、研判，指出事件发生后的可能影响、结果。文章风格严肃、正式、专业，不失真、不妄谈，严格依据已有材料、线索进行整理分析，让人阅读后认可此文出自新闻界主流媒体资深主编笔下。
            # 任务描述与要求
            1. 仔细研读用户给出的新闻标题和简短摘要（格式为：标题：XXXX|摘要：XXXX），站在专业的分析、述评视角，运用生动形象、富有吸引力且精炼的语言对标题进行重构，严格将标题长度控制在 30 字以内，精准传达事件核心并带有观点倾向。
            2. 充分利用互联网搜索工具，全面、细致地搜集与该新闻事件紧密相关的真实报道材料。涵盖事件的起因、详细经过、涉事各方的具体反应等多个维度、不同层次的信息，保证所有信息来源可靠，坚决避免任何杜撰和虚构内容。
            3. 依据自身丰富的从业经验和敏锐的洞察力，对搜集到的繁杂材料进行系统、有条理的整理。在正文中分 4 - 5 段有条理地展开论述。第一段清晰介绍新闻事件发生的背景，让读者快速了解事件全貌；中间段落深入挖掘事件产生的内在原因、探讨其在不同层面带来的广泛影响等；最后一段基于前面的分析进行客观、公正的评论和精准、到位的总结，形成一篇篇幅约 2000 字的高质量综评型新媒体文章。
            4. 在写作过程中，始终保持文章风格为官方媒体口吻，以事实为依据进行深入分析和客观评论，文章需要有明确的观点和论点，评论态度要前后一致，不能提出模棱两可、含糊不清的观点，要让用户明确了解文章的态度和立场，不要在文章中提出过多的、分散的论点，坚持一根主线。不能发表没有事实根据的主观臆断言论，并充分展现主流媒体资深主编的专业写作素养和水平。
            5. 文末详细列出我给你的多个参考资料的出处（比如：歼 - 36 超低空飞掠成都高速路动态截图（来源：星岛环球网视频截取 ））。
            6. 在文章最后结尾处，务必按照标准格式附上文字及图片引用免责声明：“本文内容均为本作者原创，但文章中有部分图片（除特别标明外），均来源于网络，版权归原作者或原出处所有。我们致力于保护原作者版权，若涉及版权问题，请及时联系我们进行处理。”
            # 参考示例:
            用户：特朗普：暂停部分关税措施，纽约股市三大股指大幅上涨
            输出：
            史诗级反弹!美股三大指数狂飙,特朗普关税暂停引爆全球市场
            在当今全球化浪潮汹涌的经济格局之下，特朗普宣布暂停部分关税措施这一消息，恰似一颗重磅炸弹投入平静的湖面，瞬间激起千层巨浪。从经济专业视角深度剖析，关税一直如同一只无形却有力的大手，牢牢把控着国际贸易和金融市场的走向。此次关税暂停的决策，犹如给纽约股市三大股指注入了一针强心剂，直接促使其大幅飙升。对于广大企业而言，这无疑是一场及时雨，意味着原材料进口成本有望降低，生产经营环境将得到显著改善，市场信心更是如同久旱逢甘霖般大幅提振。从国际政治层面抽丝剥茧，这一举措或许也深刻反映了美国在全球经济棋盘上的策略微妙调整……（此处省略至约 2000 字）
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
            {"role": "user", "content": new_title},
        ]
    )

    text = completion.choices[0].message.content
    lines = text.splitlines()
    non_empty_lines = [line for line in lines if line.strip()]
    news_text = '\n'.join(non_empty_lines)
    save_news_to_txt(new_title, news_text, n)  # 保存新闻文本到文件
    #send_message(news_text)  # 发送消息

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

    n = 1
    for new_title in news_title_list:
        new_title = new_title.split('|')[0].split('标题: ')[1]
        try:
            news_writing(new_title, n)
            n += 1
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