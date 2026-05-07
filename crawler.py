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
        # 네이버 연예 '최신 뉴스' 페이지
        url = "https://m.entertain.naver.com/now" # 모바일 페이지가 구조가 더 단순하여 크롤링에 유리합니다.
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8',
            'Referer': 'https://www.naver.com/'
        }
        
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 현재 네이버 연예 모바일 최신 뉴스 리스트 선택자
        # 사이트 구조가 바뀌었을 경우를 대비해 여러 후보를 탐색합니다.
        news_list = soup.select('.news_list_item') or soup.select('.lst_item') or soup.select('.item_area')
        
        result = ""
        count = 0
        for item in news_list:
            if count >= 5: break
            
            # 제목과 링크가 담긴 <a> 태그 찾기
            a_tag = item.find('a')
            title_tag = item.select_one('.title') or item.select_one('.tit')
            
            if a_tag and title_tag:
                title = title_tag.get_text().strip()
                link = a_tag['href']
                
                # 상대 경로 처리
                if not link.startswith('http'):
                    link = "https://m.entertain.naver.com" + link
                
                result += f'<li><a href="{link}" target="_blank">{title}</a></li>\n'
                count += 1
        
        if not result:
            # 최종 수단: 모든 <a> 태그 중 연예 뉴스 본문 링크를 추측해서 가져오기
            all_links = soup.find_all('a', href=True)
            for l in all_links:
                if '/article/' in l['href'] and count < 5:
                    t = l.get_text().strip()
                    if len(t) > 10: # 너무 짧은 텍스트 제외
                        result += f"<li><a href='{l['href']}' target='_blank'>{t}</a></li>\n"
                        count += 1
                        
        return result if result else "<li>현재 수집 가능한 연예 기사가 없습니다.</li>"
        
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
    update_html(sec_content, ent_content, eco_content)
    print("업데이트 완료!")