import requests
from bs4 import BeautifulSoup
import time
import os
from datetime import datetime
'''
content_1YWBm
category-wrap_iQLoo horizontal_1eKyQ
'''


# ====================== 全局配置 ======================
current_file = __file__
current_path = os.path.abspath(os.path.join(current_file, os.pardir))
news_title_path = os.path.abspath(os.path.join(current_path, 'news_title'))
news_papers_path = os.path.abspath(os.path.join(current_path, 'news_papers'))


def get_news_list(url):
    """
        抓取百度热榜新闻，返回{title: 新闻标题, contents: 新闻摘要}的字典列表
        :param url: 目标网页URL（百度热榜页）
        :return: 新闻字典列表（失败时返回空列表）
        """
    # 1. 配置请求头：模拟浏览器访问，避免被反爬拦截
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Referer": "https://www.baidu.com/",
        "Connection": "keep-alive"
    }

    news_list = []  # 存储最终新闻结果的列表

    try:
        # 2. 发送GET请求：添加超时控制（10秒）
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # 若状态码非200，抛出异常

        # 3. 处理编码
        response.encoding = "utf-8"
        html_content = response.text

        # 4. 解析HTML
        soup = BeautifulSoup(html_content, "lxml")

        # 5. 定位新闻容器：百度热榜新闻条目在class为“category-wrap_iQLoo horizontal_1eKyQ”的div标签中
        news_items = soup.find_all("div", class_="category-wrap_iQLoo horizontal_1eKyQ")

        if not news_items:
            print("警告：未找到新闻条目容器，请检查HTML标签/类名是否正确！")
            return news_list

        # 6. 遍历提取每篇新闻的标题和摘要
        for item in news_items:
            try:
                # 提取标题：标题在content_1YWBm下的title_dIF3B中的c-single-text-ellipsis
                content_div = item.find("div", class_="content_1YWBm")
                if not content_div:
                    continue

                title_tag = content_div.find("a", class_="title_dIF3B").find("div", class_="c-single-text-ellipsis")
                title = title_tag.get_text(strip=True) if title_tag else "未知标题"

                # 提取摘要：使用更灵活的类名匹配方式
                contents = "无摘要"

                # 1. 尝试获取完整版本摘要（large_nSuFU类）- 更灵活的匹配方式
                full_desc_tag = content_div.find("div",
                                                 class_=lambda c: c and "hot-desc_1m_jR" in c and "large_nSuFU" in c)
                # 2. 如果没有完整版本，再尝试短版本（small_Uvkd3类）
                if not full_desc_tag:
                    full_desc_tag = content_div.find("div", class_=lambda
                        c: c and "hot-desc_1m_jR" in c and "small_Uvkd3" in c)

                # 提取并清理摘要内容
                if full_desc_tag:
                    # 获取标签内所有文本（包括子标签）
                    raw_text = full_desc_tag.get_text(strip=True)
                    # 移除结尾的"查看更多>"
                    if raw_text.endswith("查看更多>"):
                        raw_text = raw_text[:-5].strip()
                    # 处理可能的重复空格
                    raw_text = " ".join(raw_text.split())

                    if raw_text:
                        contents = raw_text

                # 过滤无效数据
                if title != "未知标题":
                    news_dict = {"title": title, "contents": contents}
                    news_list.append(news_dict)

                # 延迟0.5秒：降低请求频率
                time.sleep(0.5)

            except Exception as e:
                print(f"单条新闻提取失败：{str(e)}，已跳过该条目")
                continue

        print(f"抓取完成！共获取{len(news_list)}条有效新闻")

    except requests.exceptions.RequestException as e:
        print(f"网页请求失败：{str(e)}（可能是网络问题或反爬拦截）")
    except Exception as e:
        print(f"程序异常：{str(e)}")

    return news_list


def save_titles(news_list, middle_part):
    current_time = datetime.now().strftime("%Y%m%d_%H-%M")
    count = len(news_list)
    filename = os.path.join(news_title_path, f"{middle_part}_{current_time}_{count}.txt")
    news_str = ""
    for news in news_list:
        # 从字典中分别取出不同键对应的值
        title = news.get("title", "未知标题")  # 如果键不存在，则返回"未知标题"
        desc = news.get("contents", "无摘要")  # 如果键不存在，则返回"无摘要"
        news_str += f"标题: {title}\n摘要: {desc}\n\n"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(news_str)

    return filename, count


def main(search_news_title_url):
    base_url = search_news_title_url
    news_list = get_news_list(base_url)
    count = len(news_list)

    # 处理标题并保存
    domain = base_url.split('://')[-1].split('/')[0]  # 得到 'www.baidu.com'
    middle_part = domain.split('.')[1]  # 输出：baidu
    filename, count = save_titles(news_list, middle_part)
    print(f"已处理{count}条新闻。")
    print(f"标题和摘要列表已保存至：{filename}")

    news_final_list = []
    # 将原字典列表转换为元组列表
    news_list = [(d["title"], d["contents"]) for d in news_list].copy()
    for title, desc in news_list:
        news_str = f"标题: {title}|摘要: {desc}"
        news_final_list.append(news_str)

    # 返回指定的条数的新闻列表
    n = 20
    news_final_list = news_final_list[-n:]
    print(f"共返回{len(news_final_list)}条新闻")

    return news_final_list


if __name__ == "__main__":
    search_news_title_url = "https://top.baidu.com/board?tab=realtime"
    main(search_news_title_url)