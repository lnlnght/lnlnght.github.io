import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def card(num, link, title, badge_class, badge_label):
    return f'<div class="card"><span class="card-num">{num}</span><a href="{link}" target="_blank">{title}</a><span class="card-badge {badge_class}">{badge_label}</span></div>\n'

def get_security_news():
    try:
        url = "https://www.boannews.com/media/list.asp"
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('.news_list')[:5]
        result = ""
        for i, item in enumerate(items, 1):
            title = item.select_one('.news_txt').text.strip()
            link = "https://www.boannews.com" + item.find('a')['href']
            result += card(i, link, title, 'badge-security', '보안')
        return result
    except Exception as e:
        print(f"보안 뉴스 에러: {e}")
        return card(1, "https://www.boannews.com", "보안 뉴스 로딩 실패 - 직접 확인하기", 'badge-security', '보안')

def get_youtube_trending():
    try:
        url = "https://news.google.com/rss/search?q=유튜브+인기+급상승&hl=ko&gl=KR&ceid=KR:ko"
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.raise_for_status()

        # XML 파서로 파싱 (html.parser는 <link> 태그를 빈 요소로 처리하는 문제 있음)
        root = ET.fromstring(res.content)
        items = root.findall('.//item')[:5]

        result = ""
        for i, item in enumerate(items, 1):
            title_el = item.find('title')
            link_el = item.find('link')
            guid_el = item.find('guid')

            if title_el is None:
                continue

            title = (title_el.text or '').split(' - ')[0].strip()
            link = ''

            if link_el is not None and link_el.text:
                link = link_el.text.strip()
            elif guid_el is not None and guid_el.text and guid_el.text.startswith('http'):
                link = guid_el.text.strip()

            if title:
                result += card(i, link, title, 'badge-ent', '유튜브')

        return result if result else card(1, "https://www.youtube.com/feed/trending", "유튜브 인기 급상승 보기", 'badge-ent', '유튜브')
    except Exception as e:
        print(f"유튜브 에러: {e}")
        return card(1, "https://www.youtube.com/feed/trending", "유튜브 트렌드 페이지 바로가기", 'badge-ent', '유튜브')

def get_economy_index():
    try:
        indices = [
            ('KOSPI', 'KOSPI'),
            ('KOSDAQ', 'KOSDAQ'),
            ('KPI200', 'KOSPI 200'),
        ]
        result = ""
        for i, (code, label) in enumerate(indices, 1):
            api_url = f"https://m.stock.naver.com/api/index/{code}/basic"
            res = requests.get(api_url, headers=HEADERS, timeout=10)
            data = res.json()

            price = data.get('closePrice', 'N/A')
            change = data.get('compareToPreviousClosePrice', '0')
            ratio = data.get('fluctuationsRatio', '0')

            try:
                change_f = float(str(change).replace(',', ''))
                sign = '+' if change_f >= 0 else ''
                change_str = f"{sign}{change} ({sign}{ratio}%)"
            except Exception:
                change_str = str(change)

            title = f"{label}  {price}  {change_str}"
            result += card(i, "https://finance.naver.com/sise/", title, 'badge-economy', '지수')

        return result
    except Exception as e:
        print(f"경제 지표 에러: {e}")
        return card(1, "https://finance.naver.com/sise/", "경제 지표 로딩 실패 - 직접 확인하기", 'badge-economy', '지수')

def update_html(sec, ent, eco):
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    def replace_between(source, start_tag, end_tag, new_content):
        if start_tag not in source or end_tag not in source:
            return source
        start_idx = source.find(start_tag) + len(start_tag)
        end_idx = source.find(end_tag)
        return source[:start_idx] + "\n" + new_content + source[end_idx:]

    html = replace_between(html, '<!-- security_start -->', '<!-- security_end -->', sec)
    html = replace_between(html, '<!-- ent_start -->', '<!-- ent_end -->', ent)
    html = replace_between(html, '<!-- economy_start -->', '<!-- economy_end -->', eco)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    print("보안 뉴스 수집 중...")
    sec = get_security_news()
    print(sec)

    print("유튜브 트렌드 수집 중...")
    ent = get_youtube_trending()
    print(ent)

    print("경제 지표 수집 중...")
    eco = get_economy_index()
    print(eco)

    update_html(sec, ent, eco)
    print("업데이트 완료!")
