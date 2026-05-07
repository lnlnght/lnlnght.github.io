import requests
from bs4 import BeautifulSoup

def get_news():
    try:
        sec_url = "https://www.boannews.com/media/list.asp"
        # GitHub 서버는 클린한 환경이라 verify=True(기본값)로도 잘 작동합니다.
        res = requests.get(sec_url, timeout=10)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        sec_news = ""
        news_items = soup.select('.news_list')[:5]
        for item in news_items:
            title = item.select_one('.news_txt').text.strip()
            link = "https://www.boannews.com" + item.find('a')['href']
            sec_news += f'<li><a href="{link}" target="_blank">{title}</a></li>\n'
        return sec_news
    except Exception as e:
        return f"<li>뉴스 로딩 실패: {e}</li>"

def update_html(new_content):
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    start_tag = '<!-- security_start -->'
    end_tag = '<!-- security_end -->'
    
    start_idx = html.find(start_tag) + len(start_tag)
    end_idx = html.find(end_tag)
    
    # 기존 내용을 새 내용으로 교체
    new_html = html[:start_idx] + "\n" + new_content + html[end_idx:]
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(new_html)

if __name__ == "__main__":
    content = get_news()
    update_html(content)