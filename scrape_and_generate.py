# scrape_and_generate.py
import requests
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader
import datetime

# --- A. 数据抓取部分 ---
def scrape_movie_data():
    """
    从猫眼电影抓取热门影视信息。
    """
    # 猫眼电影的热映口碑榜 URL
    url = "https://www.maoyan.com/board/1" 
    
    # 添加一个 User-Agent 头部信息，伪装成浏览器访问
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 如果请求不成功，会抛出 HTTPError 异常
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    movie_list = []
    
    # 这一部分是核心，根据猫眼电影的热映口碑榜的HTML结构来编写
    # 你需要用浏览器的开发者工具（F12）分析该页面的HTML结构
    for item in soup.find_all('dd'):
        try:
            # 找到电影标题
            title_tag = item.find('p', class_='name')
            title = title_tag.get_text(strip=True) if title_tag else '未知'

            # 找到评分
            score_tag = item.find('i', class_='integer')
            score_decimal_tag = item.find('i', class_='fraction')
            score = f"{score_tag.get_text(strip=True)}{score_decimal_tag.get_text(strip=True)}" if score_tag and score_decimal_tag else '暂无评分'

            # 找到海报图片
            image_tag = item.find('img', class_='board-img')
            image_url = image_tag.get('data-src') if image_tag else ''

            movie_list.append({
                'title': title,
                'rating': score,
                'image': image_url
            })
        except AttributeError as e:
            print(f"解析单个电影信息失败: {e}")
            continue
            
    return movie_list

# --- B. 网页生成部分 ---
def generate_html_page(data):
    """
    使用 Jinja2 模板将抓取到的数据生成 HTML 页面。
    """
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template.html')
    
    output_html = template.render(movies=data, now=datetime.datetime.now())
    
    with open("index.html", "w", encoding='utf-8') as f:
        f.write(output_html)

# --- C. 主执行逻辑 ---
if __name__ == "__main__":
    print("开始抓取热门影视信息...")
    movies_data = scrape_movie_data()
    
    if movies_data:
        print(f"已成功抓取 {len(movies_data)} 部电影信息。")
        generate_html_page(movies_data)
        print("网页已成功生成：index.html")
    else:
        print("未能抓取到任何电影信息，请检查脚本和网络连接。")