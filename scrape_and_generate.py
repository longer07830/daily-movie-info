# scrape_and_generate.py
import datetime
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

# --- A. 数据抓取部分 ---
def scrape_maoyan_board(url, title):
    """
    通用抓取函数，用于抓取猫眼电影榜单的数据。
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    chrome_options.add_argument(f'user-agent={user_agent}')

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except WebDriverException as e:
        print(f"WebDriver 初始化失败: {e}")
        return []

    data_list = []

    try:
        print(f"使用 Selenium 访问 {title} 榜单页面...")
        driver.get(url)
        time.sleep(5)  # 等待页面加载

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        items = soup.find_all('dd')
        for item in items:
            try:
                item_data = {
                    'title': '未知',
                    'rating': '暂无评分',
                    'image': '',
                    'director': '未知',
                    'actors': '未知',
                    'summary': '暂无简介'
                }

                # 找到电影标题
                title_tag = item.find('p', class_='name')
                if title_tag:
                    item_data['title'] = title_tag.get_text(strip=True)

                # 找到评分
                score_tag = item.find('i', class_='integer')
                score_decimal_tag = item.find('i', class_='fraction')
                if score_tag and score_decimal_tag:
                    item_data['rating'] = f"{score_tag.get_text(strip=True)}{score_decimal_tag.get_text(strip=True)}"

                # 找到海报图片
                image_tag = item.find('img', class_='board-img')
                if image_tag:
                    image_url = image_tag.get('data-src') or image_tag.get('src')
                    if image_url and image_url.startswith('//'):
                        image_url = 'https:' + image_url
                    item_data['image'] = image_url

                data_list.append(item_data)

            except Exception as e:
                print(f"解析单个信息失败: {e}")
                continue

    except (WebDriverException, TimeoutException) as e:
        print(f"抓取过程中发生错误: {e}")
    finally:
        driver.quit()

    return data_list

def scrape_iqiyi_series():
    """
    抓取爱奇艺热播连续剧。
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    chrome_options.add_argument(f'user-agent={user_agent}')

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except WebDriverException as e:
        print(f"WebDriver 初始化失败: {e}")
        return []

    data_list = []
    url = "https://www.iqiyi.com/channel/tv/"

    try:
        print("正在抓取爱奇艺热播连续剧...")
        driver.get(url)
        time.sleep(5)  # 等待页面加载

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # 找到爱奇艺热播榜单的容器
        chart_container = soup.find('div', class_='iqiyi-recommend-list')
        if not chart_container:
            print("未找到爱奇艺推荐列表容器。")
            return []

        items = chart_container.find_all('a', class_='recommend-list-item')
        for item in items:
            try:
                title_tag = item.find('p', class_='recommend-list-item-title')
                image_tag = item.find('img')

                item_data = {
                    'title': title_tag.get_text(strip=True) if title_tag else '未知',
                    'image': image_tag.get('src') if image_tag else '',
                    'rating': '暂无评分', # 爱奇艺榜单没有直接评分
                    'director': '未知',
                    'actors': '未知',
                    'summary': '暂无简介'
                }
                data_list.append(item_data)
            except Exception as e:
                print(f"解析单个爱奇艺剧集信息失败: {e}")
                continue
    except (WebDriverException, TimeoutException) as e:
        print(f"抓取爱奇艺时发生错误: {e}")
    finally:
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
        'domestic_series': [],
        'iqiyi_series': []
    }

    # 抓取猫眼榜单
    all_data['domestic_movies'] = scrape_maoyan_board("https://www.maoyan.com/board/1", "国内热映电影")
    all_data['foreign_movies'] = scrape_maoyan_board("https://www.maoyan.com/board/2", "海外热映电影")
    all_data['domestic_series'] = scrape_maoyan_board("https://www.maoyan.com/board/4", "国内热播连续剧")
    
    # 抓取爱奇艺榜单
    all_data['iqiyi_series'] = scrape_iqiyi_series()
    
    if any(all_data.values()):
        print("已成功抓取所有榜单信息。")
        generate_html_page(all_data)
        print("网页已成功生成：index.html")
    else:
        print("未能抓取到任何影视信息，请检查脚本和网络连接。")

