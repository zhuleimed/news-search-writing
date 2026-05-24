import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
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
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        "Referer": url  # 修改 Referer 为当前请求的 URL
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, "html.parser")

        news_list = []
        # 定位新闻列表容器
        news_containers = soup.find_all("div", class_="content_1YWBm")
        for container in news_containers:
            # 获取标题
            title_div = container.find("div", class_="c-single-text-ellipsis")
            if title_div:
                title = title_div.get_text(strip=True)
            else:
                title = None
            # 获取摘要
            desc_div = container.find("div", class_="hot-desc_1m_jR small_Uvkd3")
            if desc_div:
                desc = desc_div.get_text(strip=True)
                # 删除从 <a class= 至 查看更多> 的内容
                start_index = desc.find('<a class=')
                if start_index != -1:
                    desc = desc[:start_index].strip()
                    # 删除 "查看更多>"
                desc = desc.replace("查看更多>", "")
            else:
                desc = None
            if title or desc:  # and 为仅添加非空标题和摘要的记录，or 为添加只要标题或摘要不为空的记录
                news_list.append((title, desc))
        return news_list
    except Exception as e:
        print(f"获取新闻列表失败: {e}")
        return []


def save_titles(news, middle_part):
    current_time = datetime.now().strftime("%Y%m%d_%H-%M")
    count = len(news)
    filename = os.path.join(news_title_path, f"{middle_part}_{current_time}_{count}.txt")
    news_str = ""
    for title, desc in news:
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
    print(f"已处理{len(news_list)}条新闻。")
    print(f"标题和摘要列表已保存至：{filename}")

    news_final_list = []
    for title, desc in news_list:
        news_str = f"标题: {title}|摘要: {desc}"
        news_final_list.append(news_str)


    return news_final_list


if __name__ == "__main__":
    search_news_title_url = "https://top.baidu.com/board?tab=realtime"
    main(search_news_title_url)