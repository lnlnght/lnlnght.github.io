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
        # 가장 안정적인 Google 뉴스 RSS (연예 섹션)
        url = "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5S架WFlSQUFpS0Fid0o4R2dNRW9BQVAB?hl=ko&gl=KR&ceid=KR:ko"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'xml') # RSS는 XML 형식이므로 'xml' 파서 사용
        
        items = soup.find_all('item')[:5]
        result = ""
        
        for item in items:
            title = item.title.text
            # 구글 뉴스는 '제목 - 언론사' 형식이므로 제목만 추출
            clean_title = title.split(' - ')[0]
            link = item.link.text
            result += f'<li><a href="{link}" target="_blank">{clean_title}</a></li>\n'
        
        if not result:
            return "<li>가져온 연예 소식이 없습니다.</li>"
        return result
    except Exception as e:
        print(f"연예 뉴스 에러 상세: {e}")
        return "<li>연예 뉴스 서비스를 일시적으로 이용할 수 없습니다.</li>"

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