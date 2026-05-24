import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import os
from datetime import datetime
'''
1-18:
reset-row-margin(row reset-row-margin)
col-lg-4 col-12 list-block no-gutters row
9-18:
col-xl-8 float-lg-left float-none col-lg-8 col-12 list-container order-3
col-lg-4 col-12 list-block no-gutters row

'''

# ====================== 全局配置 ======================
current_file = __file__
current_path = os.path.abspath(os.path.join(current_file, os.pardir))
news_title_path = os.path.abspath(os.path.join(current_path, 'news_title'))
news_papers_path = os.path.abspath(os.path.join(current_path, 'news_papers'))


def get_news_list(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        "Referer": "https://www.zaobao.com/realtime/world"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, "html.parser")

        news_list = []
        # 定位新闻列表容器（根据最新网页结构修正，假设用户提供的class正确）
        news_containers = soup.find_all("div", class_="row reset-row-margin")
        for container in news_containers:
            news_items = container.find_all("a", class_="col-lg-4 col-12 list-block no-gutters row")
            for item in news_items:
                title = item.find("div", class_="f18 m-eps").get_text(strip=True)
                # link = urljoin(url, item["href"])
                news_list.append((title))
        return news_list
    except Exception as e:
        print(f"获取新闻列表失败: {e}")
        return []


def save_titles(news, middle_part):
    current_time = datetime.now().strftime("%Y%m%d_%H-%M")
    count = len(news)
    filename = os.path.join(news_title_path, f"{middle_part}_{current_time}_{count}.txt")
    news_str = "\n".join(news)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(news_str)

    return filename, count

def main(search_news_title_url):
    base_url = search_news_title_url
    news_list = get_news_list(base_url)
    count = 0
    unique_titles = set()  # 去重已处理的标题
    for title in news_list:
        if count >= 100:
            break
        if title in unique_titles:
            continue  # 跳过重复标题
        unique_titles.add(title)
        count += 1  # 只要标题和链接有效即计数
    news_title_list = [news for news in unique_titles]
    news = []
    for new_title in news_title_list:
        new_title = new_title.replace(' ', '，')
        news.append(new_title)

    # 处理标题并保存
    domain = base_url.split('://')[-1].split('/')[0]  # 得到 'www.zaobao.com'
    middle_part = domain.split('.')[1]  # 输出：zaobao
    filename, count = save_titles(news, middle_part)
    print(f"已处理{len(news)}条新闻。")
    print(f"标题列表已保存至：{filename}")

    return news


if __name__ == "__main__":
    search_news_title_url = "https://www.zaobao.com/realtime/world"
    main(search_news_title_url)
