# scrape_and_generate.py
import requests
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader
import datetime
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException

# --- A. 数据抓取部分 ---
def get_movie_details(movie_url):
    """
    访问单个电影的详情页，抓取更详细的信息。
    """
    # 伪装成浏览器访问，避免被拒绝
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    details = {
        'director': '未知',
        'actors': '未知',
        'summary': '暂无简介'
    }
    
    try:
        response = requests.get(movie_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 抓取导演和主演信息
        info_tags = soup.find_all('li', class_='p-item')
        if info_tags:
            for item in info_tags:
                # 查找导演
                if '导演' in item.text:
                    details['director'] = item.find('a').get_text(strip=True) if item.find('a') else '未知'
                # 查找主演
                elif '主演' in item.text:
                    actors = [a.get_text(strip=True) for a in item.find_all('a')]
                    details['actors'] = ', '.join(actors) if actors else '未知'
        
        # 抓取剧情简介
        summary_tag = soup.find('span', class_='dra')
        if summary_tag:
            details['summary'] = summary_tag.get_text(strip=True)

    except requests.exceptions.RequestException as e:
        print(f"访问详情页失败: {e}")
    except AttributeError as e:
        print(f"解析详情页失败: {e}")
        
    return details


def scrape_board(url, title):
    """
    通用抓取函数，用于抓取不同榜单的数据。
    """
    # 配置 Selenium WebDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    chrome_options.add_argument(f'user-agent={user_agent}')

    try:
        # 自动安装和管理 Chrome 驱动
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except WebDriverException as e:
        print(f"WebDriver 初始化失败: {e}")
        return []
    
    data_list = []

    try:
        print(f"使用 Selenium 访问 {title} 榜单页面...")
        driver.get(url)
        
        # 等待页面加载，特别是动态内容
        time.sleep(5)  
        
        # 获取完整的页面HTML内容
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # 根据猫眼电影的热映口碑榜的HTML结构来解析
        items = soup.find_all('dd')
        for item in items:
            try:
                # 找到电影标题
                title_tag = item.find('p', class_='name')
                item_title = title_tag.get_text(strip=True) if title_tag else '未知'

                # 找到评分
                score_tag = item.find('i', class_='integer')
                score_decimal_tag = item.find('i', class_='fraction')
                item_score = f"{score_tag.get_text(strip=True)}{score_decimal_tag.get_text(strip=True)}" if score_tag and score_decimal_tag else '暂无评分'

                # 找到海报图片
                image_tag = item.find('img', class_='board-img')
                image_url = image_tag.get('data-src') if image_tag else ''

                # 获取电影详情页的链接
                item_link_tag = item.find('a', class_='image-link')
                item_link = f"https://www.maoyan.com{item_link_tag.get('href')}" if item_link_tag else None

                item_data = {
                    'title': item_title,
                    'rating': item_score,
                    'image': image_url,
                    'director': '未知',
                    'actors': '未知',
                    'summary': '暂无简介'
                }
                
                # 如果有详情页链接，就去抓取详情
                if item_link:
                    print(f"  正在抓取 '{item_title}' 的详情页...")
                    details = get_movie_details(item_link)
                    item_data.update(details)
                    time.sleep(1) # 增加延迟，避免被封禁
                
                data_list.append(item_data)

            except (NoSuchElementException, AttributeError) as e:
                print(f"解析单个信息失败: {e}")
                continue
                
    except (WebDriverException, TimeoutException) as e:
        print(f"抓取过程中发生错误: {e}")
    finally:
        # 确保浏览器被关闭，释放资源
        driver.quit()
            
    return data_list

# --- B. 网页生成部分 ---
def generate_html_page(data):
    """
    使用 Jinja2 模板将抓取到的数据生成 HTML 页面。
    """
    env = Environment(loader=FileSystemLoader('.'))
    try:
        template = env.get_template('template.html')
        output_html = template.render(data=data, now=datetime.datetime.now())
        with open("index.html", "w", encoding='utf-8') as f:
            f.write(output_html)
    except Exception as e:
        print(f"模板渲染或文件写入失败: {e}")


# --- C. 主执行逻辑 ---
if __name__ == "__main__":
    print("开始抓取热门影视信息...")
    
    all_data = {
        'domestic_movies': [],
        'foreign_movies': [],
        'domestic_series': []
    }

    # 抓取国内电影
    all_data['domestic_movies'] = scrape_board("https://www.maoyan.com/board/1", "国内热映电影")

    # 抓取海外电影
    all_data['foreign_movies'] = scrape_board("https://www.maoyan.com/board/2", "海外热映电影")

    # 抓取国内连续剧
    all_data['domestic_series'] = scrape_board("https://www.maoyan.com/board/4", "国内热播连续剧")
    
    if any(all_data.values()):
        print("已成功抓取所有榜单信息。")
        generate_html_page(all_data)
        print("网页已成功生成：index.html")
    else:
        print("未能抓取到任何影视信息，请检查脚本和网络连接。")
