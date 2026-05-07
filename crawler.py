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
        # 다음 연예 뉴스 (구조가 명확하여 크롤링이 안정적입니다)
        url = "https://news.daum.net/entertain"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 다음 뉴스 메인 하이라이트 기사 추출
        news_items = soup.select('.item_bundle .tit_g')[:5]
        if not news_items: # 구조가 다를 경우 대비한 보조 선택자
            news_items = soup.select('.list_newsissue li .tit_g')[:5]

        result = ""
        for item in news_items:
            a_tag = item.find('a')
            title = a_tag.text.strip()
            link = a_tag['href']
            result += f'<li><a href="{link}" target="_blank">{title}</a></li>\n'
        
        if not result:
            return "<li>가져온 연예 기사가 없습니다.</li>"
        return result
    except Exception as e:
        return f"<li>연예 뉴스 로딩 실패: {str(e)}</li>"

def update_html(sec_content, ent_content):
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            html = f.read()

        # 보안 뉴스 업데이트
        if '<!-- security_start -->' in html:
            s_tag, e_tag = '<!-- security_start -->', '<!-- security_end -->'
            start_part = html.split(s_tag)[0]
            end_part = html.split(e_tag)[1]
            html = start_part + s_tag + "\n" + sec_content + e_tag + end_part

        # 연예 뉴스 업데이트
        if '<!-- ent_start -->' in html:
            s_tag, e_tag = '<!-- ent_start -->', '<!-- ent_end -->'
            start_part = html.split(s_tag)[0]
            end_part = html.split(e_tag)[1]
            html = start_part + s_tag + "\n" + ent_content + e_tag + end_part
        
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html)
    except Exception as e:
        print(f"HTML 업데이트 중 오류 발생: {e}")

if __name__ == "__main__":
    sec = get_security_news()
    ent = get_ent_news()
    update_html(sec, ent)
    print("업데이트 완료!")