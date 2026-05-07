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

def get_youtube_trending():
    try:
        # 구글 뉴스 기반 유튜브 트렌드 RSS
        url = "https://news.google.com/rss/search?q=유튜브+인기+급상승&hl=ko&gl=KR&ceid=KR:ko"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        res = requests.get(url, headers=headers, timeout=15)
        res.encoding = 'utf-8'
        
        # 'Couldn't find a tree' 에러 방지를 위해 데이터가 있는지 먼저 확인
        if not res.text.strip():
            return "<li>데이터가 비어있습니다.</li>"

        # lxml 대신 기본 html.parser를 사용하고 형식을 명시함
        soup = BeautifulSoup(res.text, "html.parser")
        
        items = soup.find_all('item')[:5]
        result = ""
        
        for item in items:
            title_tag = item.find('title')
            # 구글 RSS의 link 태그는 가끔 속성 없이 텍스트로만 존재합니다.
            link_tag = item.find('link')
            
            if title_tag and link_tag:
                title = title_tag.get_text().split(' - ')[0]
                
                # 링크를 가져오는 3단계 필터
                # 1. 태그 내부 텍스트, 2. string 속성, 3. 다음 요소 확인
                link = link_tag.get_text() or link_tag.string or ""
                
                # 만약 그래도 비어있다면, item 자식 중 가장 긴 텍스트를 링크로 추정 (RSS 특성)
                if not link:
                    link = item.text.split('http')[-1].split(' ')[0]
                    link = 'http' + link if link else ""

                if link:
                    result += f'<li><a href="{link}" target="_blank">📺 {title}</a></li>\n'
        
        return result if result else "<li>인기 영상을 찾을 수 없습니다.</li>"
        
    except Exception as e:
        # 에러 발생 시 로그에 상세 원인 출력 (디버깅용)
        print(f"상세 에러: {e}")
        return "<li>유튜브 로딩 중 오류 발생</li>"

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
    ent_content = get_youtube_trending()
    eco_content = get_economy_index()

   # 디버깅용: 수집된 연예 뉴스 내용을 로그에 출력
    print("--- 수집된 연예 뉴스 ---")
    print(ent_content)
    print("------------------------")
    update_html(sec_content, ent_content, eco_content)

    print("업데이트 완료!")