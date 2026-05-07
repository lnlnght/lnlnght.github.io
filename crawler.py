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

def get_economy_index():
    try:
        url = "https://finance.naver.com/sise/"
        res = requests.get(url, timeout=10)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        kospi = soup.select_one('#KOSPI_now').text
        kosdaq = soup.select_one('#KOSDAQ_now').text
        result = f"<li>📊 KOSPI: <strong>{kospi}</strong></li>\n"
        result += f"<li>📉 KOSDAQ: <strong>{kosdaq}</strong></li>\n"
        return result
    except:
        return "<li>경제 지표 로딩 실패</li>"

def update_html(sec, ent, eco):
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    def replace_content(source, start_tag, end_tag, new_content):
        if start_tag not in source or end_tag not in source: return source
        start_idx = source.find(start_tag) + len(start_tag)
        end_idx = source.find(end_tag)
        return source[:start_idx] + "\n" + new_content + source[end_idx:]

    html = replace_content(html, '<!-- security_start -->', '<!-- security_end -->', sec)
    html = replace_content(html, '<!-- ent_start -->', '<!-- ent_end -->', ent)
    html = replace_content(html, '<!-- economy_start -->', '<!-- economy_end -->', eco)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    sec_content = get_security_news()
    ent_content = get_ent_news()
    eco_content = get_economy_index()

   # 디버깅용: 수집된 연예 뉴스 내용을 로그에 출력
    print("--- 수집된 연예 뉴스 ---")
    print(ent_content) 
    print("------------------------")
    update_html(sec_content, ent_content, eco_content)

    print("업데이트 완료!")