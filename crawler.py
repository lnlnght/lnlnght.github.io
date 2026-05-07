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
        # 구조가 더 고정적인 '랭킹 뉴스' 페이지를 타겟으로 변경
        url = "https://entertain.naver.com/ranking"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 랭킹 뉴스의 제목과 링크를 찾는 여러 후보 선택자
        # 1순위: rank_lst, 2순위: 뉴스 제목 클래스들
        news_items = soup.select('.rank_lst li') or soup.select('.news_lst li')
        
        result = ""
        count = 0
        for item in news_items:
            if count >= 5: break
            
            # 제목 태그 찾기 (a 태그 혹은 tit 클래스)
            a_tag = item.select_one('.tit') or item.select_one('a')
            
            if a_tag:
                title = a_tag.get_text().strip()
                link = a_tag['href']
                
                # 가끔 제목이 너무 짧거나 무의미한 경우 제외
                if len(title) < 5: continue
                
                if not link.startswith('http'):
                    link = "https://entertain.naver.com" + link
                
                result += f'<li><a href="{link}" target="_blank">{title}</a></li>\n'
                count += 1
        
        if not result:
            return "<li>데이터 추출 성공했으나 항목이 비어있음 (선택자 점검 필요)</li>"
            
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