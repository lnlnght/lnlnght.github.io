import requests
from bs4 import BeautifulSoup

def get_security_news():
    try:
        url = "https://www.boannews.com/media/list.asp"
        res = requests.get(url, timeout=10)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        news_items = soup.select('.news_list')[:5]
        result = ""
        for item in news_items:
            title = item.select_one('.news_txt').text.strip()
            link = "https://www.boannews.com" + item.find('a')['href']
            result += f'<li><a href="{link}" target="_blank">{title}</a></li>\n'
        return result
    except:
        return "<li>보안 뉴스 로딩 실패</li>"

def get_ent_news():
    try:
        # 네이버 연예 뉴스 메인 (예시)
        url = "https://entertain.naver.com/now" 
        headers = {'User-Agent': 'Mozilla/5.0'} # 네이버는 차단 방지를 위해 헤더가 필요할 수 있음
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 최신 뉴스 리스트 추출 (사이트 구조에 따라 선택자는 변경될 수 있음)
        news_items = soup.select('.news_lst li')[:5]
        result = ""
        for item in news_items:
            title = item.select_one('.tit').text.strip()
            link = item.select_one('a')['href']
            # 상대 경로일 경우 절대 경로로 변환
            if not link.startswith('http'):
                link = "https://entertain.naver.com" + link
            result += f'<li><a href="{link}" target="_blank">{title}</a></li>\n'
        return result
    except:
        return "<li>연예 뉴스 로딩 실패</li>"

def update_html(sec_content, ent_content):
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # 보안 뉴스 업데이트
    s_tag, e_tag = '<!-- security_start -->', '<!-- security_end -->'
    html = html[:html.find(s_tag)+len(s_tag)] + "\n" + sec_content + html[html.find(e_tag):]

    # 연예 뉴스 업데이트
    s_tag, e_tag = '<!-- ent_start -->', '<!-- ent_end -->'
    html = html[:html.find(s_tag)+len(s_tag)] + "\n" + ent_content + html[html.find(e_tag):]
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    sec = get_security_news()
    ent = get_ent_news()
    update_html(sec, ent)
    print("모든 카테고리 업데이트 완료!")
