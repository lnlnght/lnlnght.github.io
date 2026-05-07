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
        # 랭킹 뉴스 페이지는 차단이 심할 수 있으니 메인 '연예 홈'으로 시도
        url = "https://entertain.naver.com/home"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        result = ""
        count = 0
        visited_links = set() # 중복 기사 방지

        # 클래스명 상관없이 모든 <a> 태그를 다 뒤집니다.
        for a_tag in soup.find_all('a', href=True):
            link = a_tag['href']
            title = a_tag.get_text().strip()
            
            # 1. 링크에 'read' 또는 'article'이 들어있고 
            # 2. 제목이 15자 이상(너무 짧은 메뉴명 제외)인 것만 필터링
            if ('read' in link or 'article' in link) and len(title) >= 15:
                if link not in visited_links:
                    # 상대 경로 처리
                    full_link = link if link.startswith('http') else "https://entertain.naver.com" + link
                    result += f'<li><a href="{full_link}" target="_blank">{title}</a></li>\n'
                    visited_links.add(link)
                    count += 1
            
            if count >= 5: break # 5개만 가져오기

        if not result:
            return "<li>기사 패턴 매칭 실패 (타겟 사이트 변경 권장)</li>"
            
        return result
    except Exception as e:
        return f"<li>연예 뉴스 로딩 에러: {str(e)}</li>"

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