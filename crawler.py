﻿import requests
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
        # 네이버 연예 뉴스 최신순 페이지
        url = "https://entertain.naver.com/now"
        
        # 봇 차단을 방지하기 위한 필수 헤더 (크롬 브라우저인 척 합니다)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status() # 접속 오류 시 예외 발생
        
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 네이버 연예 최신 뉴스 리스트 선택자 (현재 기준: .news_lst 내의 li)
        news_items = soup.select('.news_lst li')[:5]
        
        result = ""
        for item in news_items:
            # 제목과 링크가 있는 <a> 태그 찾기
            a_tag = item.select_one('.tit')
            if a_tag:
                title = a_tag.get_text().strip()
                link = a_tag['href']
                # 주소가 상대 경로일 경우를 대비해 도메인 결합
                if not link.startswith('http'):
                    link = "https://entertain.naver.com" + link
                result += f'<li><a href="{link}" target="_blank">{title}</a></li>\n'
        
        if not result:
            return "<li>가져온 뉴스 항목이 없습니다. (구조 변경 확인 필요)</li>"
        return result

    except Exception as e:
        return f"<li>연예 뉴스 로딩 실패: {str(e)}</li>"

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