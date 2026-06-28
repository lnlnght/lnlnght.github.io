import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')

# ── 인물 정의 ─────────────────────────────────────────────────
PEOPLE = [
    {
        'id': 'sam_altman',
        'name': 'Sam Altman',
        'name_ko': '샘 올트먼',
        'title': 'CEO, OpenAI',
        'avatar': 'SA',
        'color': '#10b981',
        'youtube_channels': [
            'UCXZCJLdBC09xxGZ6gcdrc6A',  # OpenAI
            'UCSHZKyawb77ixDdsGog4iWA',  # Lex Fridman (인터뷰)
        ],
        'news_queries': ['Sam Altman', '샘 올트먼', 'OpenAI CEO'],
    },
    {
        'id': 'jensen_huang',
        'name': 'Jensen Huang',
        'name_ko': '젠슨 황',
        'title': 'CEO, NVIDIA',
        'avatar': 'JH',
        'color': '#76b900',
        'youtube_channels': [
            'UCHuiy8bXnmK5nisYHUd1J5g',  # NVIDIA
        ],
        'news_queries': ['Jensen Huang', '젠슨 황', 'NVIDIA CEO AI'],
    },
    {
        'id': 'dario_amodei',
        'name': 'Dario Amodei',
        'name_ko': '다리오 아모데이',
        'title': 'CEO, Anthropic',
        'avatar': 'DA',
        'color': '#d97706',
        'youtube_channels': [
            'UCG2PZaakRMlN_Y39mGR-YjA',  # Anthropic
            'UCSHZKyawb77ixDdsGog4iWA',  # Lex Fridman
        ],
        'news_queries': ['Dario Amodei', '다리오 아모데이', 'Anthropic CEO'],
    },
    {
        'id': 'elon_musk',
        'name': 'Elon Musk',
        'name_ko': '일론 머스크',
        'title': 'CEO, xAI / Tesla',
        'avatar': 'EM',
        'color': '#6366f1',
        'youtube_channels': [
            'UCSHZKyawb77ixDdsGog4iWA',  # Lex Fridman
        ],
        'news_queries': ['Elon Musk AI', 'xAI Grok', '일론 머스크 AI'],
    },
    {
        'id': 'geoffrey_hinton',
        'name': 'Geoffrey Hinton',
        'name_ko': '제프리 힌튼',
        'title': 'Godfather of AI',
        'avatar': 'GH',
        'color': '#ec4899',
        'youtube_channels': [
            'UCSHZKyawb77ixDdsGog4iWA',  # Lex Fridman
        ],
        'news_queries': ['Geoffrey Hinton', '제프리 힌튼', 'Hinton AI warning'],
    },
    {
        'id': 'demis_hassabis',
        'name': 'Demis Hassabis',
        'name_ko': '데미스 하사비스',
        'title': 'CEO, Google DeepMind',
        'avatar': 'DH',
        'color': '#3b82f6',
        'youtube_channels': [
            'UCnUYZLuoy1rq1aVMwx4aTzw',  # Google DeepMind
        ],
        'news_queries': ['Demis Hassabis', '데미스 하사비스', 'DeepMind CEO'],
    },
]

# ── 추가 공통 AI 채널 (모든 인물 탭의 영상 풀 보완) ──────────
COMMON_CHANNELS = [
    'UCSHZKyawb77ixDdsGog4iWA',  # Lex Fridman Podcast
    'UCbmNph6atAoGfqLoCL_duAg',  # TED Talks
]

HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; AI-News-Fetcher/1.0)'}


def fetch_youtube_rss(channel_id):
    url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f'  [YT] {channel_id} HTTP {r.status_code}')
            return []
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'yt': 'http://www.youtube.com/xml/schemas/2015',
            'media': 'http://search.yahoo.com/mrss/',
        }
        root = ET.fromstring(r.text)
        items = []
        for entry in root.findall('atom:entry', ns)[:10]:
            vid_id = entry.findtext('yt:videoId', namespaces=ns) or ''
            title = entry.findtext('atom:title', namespaces=ns) or ''
            published = entry.findtext('atom:published', namespaces=ns) or ''
            channel_name = root.findtext('atom:title', namespaces=ns) or ''
            thumb = f'https://i.ytimg.com/vi/{vid_id}/mqdefault.jpg' if vid_id else ''
            items.append({
                'type': 'video',
                'title': title,
                'url': f'https://www.youtube.com/watch?v={vid_id}',
                'thumbnail': thumb,
                'source': channel_name,
                'published_at': published[:19] if published else '',
            })
        return items
    except Exception as e:
        print(f'  [YT] {channel_id} error: {e}')
        return []


def fetch_google_news(query, lang='en'):
    if lang == 'ko':
        url = f'https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=ko&gl=KR&ceid=KR:ko'
    else:
        url = f'https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=en-US&gl=US&ceid=US:en'
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f'  [NEWS] {query} HTTP {r.status_code}')
            return []
        root = ET.fromstring(r.text)
        channel = root.find('channel')
        if channel is None:
            return []
        items = []
        for item in channel.findall('item')[:8]:
            title = item.findtext('title') or ''
            link = item.findtext('link') or ''
            pub = item.findtext('pubDate') or ''
            source_el = item.find('source')
            source = source_el.text if source_el is not None else 'Google News'
            try:
                dt = parsedate_to_datetime(pub).astimezone(timezone.utc)
                pub_iso = dt.strftime('%Y-%m-%dT%H:%M:%S')
            except Exception:
                pub_iso = ''
            items.append({
                'type': 'news',
                'title': title,
                'url': link,
                'thumbnail': '',
                'source': source,
                'published_at': pub_iso,
            })
        return items
    except Exception as e:
        print(f'  [NEWS] {query} error: {e}')
        return []


def title_matches_person(title, person):
    title_lower = title.lower()
    checks = [person['name'].lower()] + [q.lower() for q in person['news_queries']]
    return any(c in title_lower for c in checks)


def supabase_upsert(table, rows):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates,return=minimal',
    }
    on_conflict = 'url' if table == 'ai_news' else ''
    url = f'{SUPABASE_URL}/rest/v1/{table}' + (f'?on_conflict={on_conflict}' if on_conflict else '')
    res = requests.post(url, json=rows, headers=headers, timeout=30)
    if res.status_code not in (200, 201):
        print(f'[Supabase] {table} upsert 실패: {res.status_code} {res.text[:200]}')
    else:
        print(f'[Supabase] {table} {len(rows)}개 upsert 완료')


def main():
    all_rows = []
    seen_urls = set()

    # 채널 → 인물 매핑 (Lex Fridman 등 공통 채널 필터용)
    channel_to_people = {}
    for p in PEOPLE:
        for ch in p['youtube_channels']:
            channel_to_people.setdefault(ch, []).append(p['id'])

    # 1) YouTube RSS 수집
    fetched_channels = set()
    for person in PEOPLE:
        print(f'\n[{person["name"]}] YouTube 수집...')
        for ch_id in person['youtube_channels']:
            if ch_id in fetched_channels:
                continue
            fetched_channels.add(ch_id)
            videos = fetch_youtube_rss(ch_id)
            print(f'  채널 {ch_id}: {len(videos)}개')
            for v in videos:
                if v['url'] in seen_urls:
                    continue
                # 공통 채널(Lex 등)이면 제목으로 인물 필터
                people_for_ch = channel_to_people.get(ch_id, [])
                assigned = []
                if len(people_for_ch) > 1 or ch_id in [p2['id'] for p2 in PEOPLE for _ in [1]]:
                    for pid in people_for_ch:
                        p_obj = next((x for x in PEOPLE if x['id'] == pid), None)
                        if p_obj and title_matches_person(v['title'], p_obj):
                            assigned.append(pid)
                    if not assigned:
                        assigned = people_for_ch  # 매칭 없으면 채널 소유자 전체
                else:
                    assigned = people_for_ch

                seen_urls.add(v['url'])
                for pid in assigned:
                    row = {**v, 'person_id': pid}
                    all_rows.append(row)

    # 2) Google News RSS 수집
    for person in PEOPLE:
        print(f'\n[{person["name"]}] 뉴스 수집...')
        for q in person['news_queries']:
            lang = 'ko' if any(ord(c) > 127 for c in q) else 'en'
            articles = fetch_google_news(q, lang=lang)
            print(f'  "{q}": {len(articles)}개')
            for a in articles:
                if a['url'] in seen_urls:
                    continue
                seen_urls.add(a['url'])
                row = {**a, 'person_id': person['id']}
                all_rows.append(row)

    # 3) 결과 저장
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    for row in all_rows:
        if not row.get('published_at'):
            row['published_at'] = now_str
        row['updated_at'] = now_str

    print(f'\n총 {len(all_rows)}개 항목 수집')

    # JSON 백업
    with open('ai_news.json', 'w', encoding='utf-8') as f:
        json.dump({'updated': now_str, 'items': all_rows}, f, ensure_ascii=False, separators=(',', ':'))

    # Supabase upsert
    if all_rows:
        supabase_upsert('ai_news', all_rows)


if __name__ == '__main__':
    main()
