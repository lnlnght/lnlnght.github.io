import yfinance as yf
import json
import math
import os
import io
import zipfile
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# ── DART API (한국 주식 재무데이터) ──────────────────────────────
DART_API_KEY = os.environ.get('DART_API_KEY', '')

# ── Supabase ─────────────────────────────────────────────────
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')

def supabase_upsert(table, rows):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates,return=minimal',
    }
    res = requests.post(f'{SUPABASE_URL}/rest/v1/{table}', json=rows, headers=headers, timeout=30)
    if res.status_code not in (200, 201):
        print(f'[Supabase] {table} upsert 실패: {res.status_code} {res.text[:200]}')
    else:
        print(f'[Supabase] {table} {len(rows)}개 upsert 완료')

# ── 네이버 금융 컨센서스 ────────────────────────────────────────
_NAVER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://finance.naver.com/',
}
_NAVER_BLOCKED = False  # 첫 403/차단 감지 시 이후 호출 건너뜀

def naver_get_forward_eps(code):
    """네이버 finance/summary에서 분기별 EPS 합산으로 연간 forward EPS 반환 (원/주)"""
    global _NAVER_BLOCKED
    if _NAVER_BLOCKED:
        return None
    url = f'https://m.stock.naver.com/api/stock/{code}/finance/summary'
    try:
        res = requests.get(url, headers=_NAVER_HEADERS, timeout=5)
        if res.status_code in (403, 401, 429):
            _NAVER_BLOCKED = True
            return None
        if res.status_code != 200:
            return None
        data = res.json()
        eps_data = data.get('chartEps') if isinstance(data, dict) else None
        if not eps_data or not isinstance(eps_data, dict):
            return None
        # columns: [['x', 'Q1', 'Q2', ...], ['EPS', v1, v2, ...]]
        cols = eps_data.get('columns', [])
        if len(cols) < 2:
            return None
        eps_row = cols[1]  # ['EPS', '733', '1783', ...]
        if not eps_row or eps_row[0] != 'EPS':
            return None
        vals = []
        for v in eps_row[1:]:
            try:
                vals.append(int(str(v).replace(',', '')))
            except (ValueError, TypeError):
                pass
        if len(vals) < 4:
            return None
        # 최근 4분기 합산 = 연간 forward EPS
        annual_eps = sum(vals[-4:])
        print(f'  [NAVER] {code} chartEps 4Q={vals[-4:]} 연간EPS={annual_eps}')
        return annual_eps if annual_eps != 0 else None
    except Exception as e:
        print(f'  [NAVER] {code} 조회 실패: {e}')
    return None

def dart_load_corp_codes(api_key):
    """DART 기업코드 목록 다운로드 (stock_code → corp_code 매핑)"""
    try:
        res = requests.get(
            f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={api_key}",
            timeout=30
        )
        with zipfile.ZipFile(io.BytesIO(res.content)) as z:
            with z.open('CORPCODE.xml') as f:
                tree = ET.parse(f)
        mapping = {}
        for item in tree.getroot().findall('list'):
            stock_code = item.findtext('stock_code', '').strip()
            corp_code  = item.findtext('corp_code', '').strip()
            if stock_code:
                mapping[stock_code] = corp_code
        print(f"[DART] 기업코드 {len(mapping)}개 로드")
        return mapping
    except Exception as e:
        print(f"[DART] 기업코드 로드 실패: {e}")
        return {}

def dart_fetch_report(api_key, corp_code, year, reprt_code):
    """DART API 단일 보고서 조회. 손익계산서 항목만 반환 (단위: 원)"""
    try:
        res = requests.get(
            "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json",
            params={
                'crtfc_key': api_key,
                'corp_code':  corp_code,
                'bsns_year':  str(year),
                'reprt_code': reprt_code,
                'fs_div':     'CFS',
            },
            timeout=30
        )
        data = res.json()
        if data.get('status') != '000':
            if reprt_code == '11013':  # Q1 조회 실패만 로그
                print(f"  [DART] {corp_code} {year}/Q1 status={data.get('status')} msg={data.get('message','')}")
            return None
        operating_income = net_income = revenue = total_equity = None
        revenue_fuzzy = None
        for item in data.get('list', []):
            sj  = item.get('sj_div', '').strip()
            nm  = item.get('account_nm', '').strip()
            raw = item.get('thstrm_amount', '').replace(',', '').strip()
            if not raw:
                continue
            try:
                val = int(raw)  # DART 단위: 원(KRW)
            except ValueError:
                continue
            if sj in ('IS', 'CIS'):
                if operating_income is None and '영업이익' in nm:
                    operating_income = val
                if net_income is None and '당기순이익' in nm and '지배기업' not in nm and '비지배' not in nm:
                    net_income = val
                if nm in ('수익(매출액)', '매출액', '영업수익'):
                    revenue = val
                elif revenue_fuzzy is None and '매출' in nm and '원가' not in nm:
                    revenue_fuzzy = val
            elif sj == 'BS':
                if total_equity is None and nm in ('자본총계', '지배기업 소유주지분'):
                    total_equity = val
        if revenue is None:
            revenue = revenue_fuzzy
        return {
            'operating_income': operating_income,
            'net_income':       net_income,
            'revenue':          revenue,
            'total_equity':     total_equity,
        }
    except Exception as e:
        print(f"[DART] {corp_code} {year}/{reprt_code} 조회 실패: {e}")
        return None

def dart_get_financials(api_key, corp_code, annual_year):
    """연간 데이터 + Q1 조정으로 TTM 산출.
    TTM = FY(annual_year) + Q1(annual_year+1) - Q1(annual_year)
    Q1 데이터가 없으면 연간 데이터를 그대로 반환.
    """
    annual = dart_fetch_report(api_key, corp_code, annual_year, '11011')
    if annual is None:
        return None

    # Q1(올해) - Q1(작년) 차분으로 TTM 보정
    q1_curr = dart_fetch_report(api_key, corp_code, annual_year + 1, '11013')
    q1_prev = dart_fetch_report(api_key, corp_code, annual_year,     '11013')

    result = dict(annual)  # annual 기본값

    if q1_curr and q1_prev:
        for key in ('operating_income', 'net_income', 'revenue'):
            a = annual.get(key)
            c = q1_curr.get(key)
            p = q1_prev.get(key)
            if a is not None and c is not None and p is not None:
                result[key] = a + c - p  # TTM 보정
        ni_ttm = result.get('net_income')
        ni_annual = annual.get('net_income')
        ni_q1c = q1_curr.get('net_income')
        ni_q1p = q1_prev.get('net_income')
        print(f"  [DART TTM] {corp_code} FY{annual_year}={ni_annual} Q1{annual_year+1}={ni_q1c} Q1{annual_year}={ni_q1p} TTM={ni_ttm}")
    else:
        print(f"  [DART TTM] {corp_code} Q1데이터없음(q1_curr={'OK' if q1_curr else 'None'} q1_prev={'OK' if q1_prev else 'None'}) → FY{annual_year}만사용={annual.get('net_income')}")

    return result

# DART 기업코드 매핑 로드 (API 키가 있을 때만)
dart_corp_map = dart_load_corp_codes(DART_API_KEY) if DART_API_KEY else {}
current_year = datetime.now().year

STOCKS = [
    # ============================================================
    # 미국 주요 종목
    # ============================================================

    # 기술
    {"yf": "AAPL",  "code": "AAPL",  "name": "애플",           "sector": "기술",    "market": "US"},
    {"yf": "MSFT",  "code": "MSFT",  "name": "마이크로소프트",  "sector": "기술",    "market": "US"},
    {"yf": "NVDA",  "code": "NVDA",  "name": "엔비디아",        "sector": "기술",    "market": "US"},
    {"yf": "GOOGL", "code": "GOOGL", "name": "알파벳 (구글)",   "sector": "기술",    "market": "US"},
    {"yf": "META",  "code": "META",  "name": "메타",            "sector": "기술",    "market": "US"},
    {"yf": "AMZN",  "code": "AMZN",  "name": "아마존",          "sector": "기술",    "market": "US"},
    {"yf": "TSLA",  "code": "TSLA",  "name": "테슬라",          "sector": "기술",    "market": "US"},
    {"yf": "TSM",   "code": "TSM",   "name": "TSMC",            "sector": "기술",    "market": "US"},
    {"yf": "AVGO",  "code": "AVGO",  "name": "브로드컴",        "sector": "기술",    "market": "US"},
    {"yf": "ORCL",  "code": "ORCL",  "name": "오라클",          "sector": "기술",    "market": "US"},
    {"yf": "CRM",   "code": "CRM",   "name": "세일즈포스",      "sector": "기술",    "market": "US"},
    {"yf": "AMD",   "code": "AMD",   "name": "AMD",             "sector": "기술",    "market": "US"},
    {"yf": "MU",    "code": "MU",    "name": "마이크론",         "sector": "기술",    "market": "US"},
    {"yf": "INTC",  "code": "INTC",  "name": "인텔",            "sector": "기술",    "market": "US"},

    # 금융
    {"yf": "BRK-B", "code": "BRK-B", "name": "버크셔 해서웨이", "sector": "금융",   "market": "US"},
    {"yf": "JPM",   "code": "JPM",   "name": "JP모건",          "sector": "금융",    "market": "US"},
    {"yf": "V",     "code": "V",     "name": "비자",            "sector": "금융",    "market": "US"},
    {"yf": "MA",    "code": "MA",    "name": "마스터카드",      "sector": "금융",    "market": "US"},
    {"yf": "BAC",   "code": "BAC",   "name": "뱅크오브아메리카","sector": "금융",    "market": "US"},
    {"yf": "GS",    "code": "GS",    "name": "골드만삭스",      "sector": "금융",    "market": "US"},

    # 헬스케어
    {"yf": "UNH",   "code": "UNH",   "name": "유나이티드헬스",  "sector": "헬스케어","market": "US"},
    {"yf": "JNJ",   "code": "JNJ",   "name": "존슨앤드존슨",    "sector": "헬스케어","market": "US"},
    {"yf": "LLY",   "code": "LLY",   "name": "일라이 릴리",     "sector": "헬스케어","market": "US"},
    {"yf": "ABBV",  "code": "ABBV",  "name": "애브비",          "sector": "헬스케어","market": "US"},
    {"yf": "MRK",   "code": "MRK",   "name": "머크",            "sector": "헬스케어","market": "US"},

    # 소비재
    {"yf": "WMT",   "code": "WMT",   "name": "월마트",          "sector": "소비재",  "market": "US"},
    {"yf": "COST",  "code": "COST",  "name": "코스트코",        "sector": "소비재",  "market": "US"},
    {"yf": "MCD",   "code": "MCD",   "name": "맥도날드",        "sector": "소비재",  "market": "US"},
    {"yf": "KO",    "code": "KO",    "name": "코카콜라",        "sector": "소비재",  "market": "US"},
    {"yf": "PG",    "code": "PG",    "name": "P&G",             "sector": "소비재",  "market": "US"},

    # 에너지
    {"yf": "XOM",   "code": "XOM",   "name": "엑슨모빌",        "sector": "에너지",  "market": "US"},
    {"yf": "CVX",   "code": "CVX",   "name": "셰브론",          "sector": "에너지",  "market": "US"},

    # 산업재
    {"yf": "CAT",   "code": "CAT",   "name": "캐터필러",        "sector": "산업재",  "market": "US"},
    {"yf": "GE",    "code": "GE",    "name": "GE 에어로스페이스","sector": "산업재",  "market": "US"},
    {"yf": "BA",    "code": "BA",    "name": "보잉",            "sector": "산업재",  "market": "US"},

    # 기술 추가
    {"yf": "NFLX",  "code": "NFLX",  "name": "넷플릭스",          "sector": "기술",    "market": "US"},
    {"yf": "UBER",  "code": "UBER",  "name": "우버",              "sector": "기술",    "market": "US"},
    {"yf": "ABNB",  "code": "ABNB",  "name": "에어비앤비",        "sector": "기술",    "market": "US"},
    {"yf": "PLTR",  "code": "PLTR",  "name": "팔란티어",          "sector": "기술",    "market": "US"},
    {"yf": "SNOW",  "code": "SNOW",  "name": "스노우플레이크",    "sector": "기술",    "market": "US"},
    {"yf": "NOW",   "code": "NOW",   "name": "서비스나우",        "sector": "기술",    "market": "US"},
    {"yf": "SHOP",  "code": "SHOP",  "name": "쇼피파이",          "sector": "기술",    "market": "US"},
    {"yf": "COIN",  "code": "COIN",  "name": "코인베이스",        "sector": "기술",    "market": "US"},
    {"yf": "HOOD",  "code": "HOOD",  "name": "로빈후드",          "sector": "기술",    "market": "US"},
    {"yf": "SPOT",  "code": "SPOT",  "name": "스포티파이",        "sector": "기술",    "market": "US"},
    {"yf": "DELL",  "code": "DELL",  "name": "델 테크놀로지스",   "sector": "기술",    "market": "US"},
    {"yf": "ACN",   "code": "ACN",   "name": "액센추어",          "sector": "기술",    "market": "US"},
    {"yf": "IBM",   "code": "IBM",   "name": "IBM",               "sector": "기술",    "market": "US"},
    {"yf": "AMAT",  "code": "AMAT",  "name": "어플라이드 머티리얼즈", "sector": "기술", "market": "US"},
    {"yf": "LRCX",  "code": "LRCX",  "name": "램리서치",          "sector": "기술",    "market": "US"},
    {"yf": "KLAC",  "code": "KLAC",  "name": "KLA 코퍼레이션",    "sector": "기술",    "market": "US"},
    {"yf": "QCOM",  "code": "QCOM",  "name": "퀄컴",              "sector": "기술",    "market": "US"},
    {"yf": "TXN",   "code": "TXN",   "name": "텍사스인스트루먼트","sector": "기술",    "market": "US"},
    {"yf": "PANW",  "code": "PANW",  "name": "팰로알토 네트웍스", "sector": "기술",    "market": "US"},
    {"yf": "CRWD",  "code": "CRWD",  "name": "크라우드스트라이크","sector": "기술",    "market": "US"},

    # 금융 추가
    {"yf": "MS",    "code": "MS",    "name": "모건스탠리",        "sector": "금융",    "market": "US"},
    {"yf": "C",     "code": "C",     "name": "씨티그룹",          "sector": "금융",    "market": "US"},
    {"yf": "WFC",   "code": "WFC",   "name": "웰스파고",          "sector": "금융",    "market": "US"},
    {"yf": "AXP",   "code": "AXP",   "name": "아메리칸 익스프레스","sector": "금융",   "market": "US"},
    {"yf": "BLK",   "code": "BLK",   "name": "블랙록",            "sector": "금융",    "market": "US"},
    {"yf": "SCHW",  "code": "SCHW",  "name": "찰스 슈왑",         "sector": "금융",    "market": "US"},
    {"yf": "CME",   "code": "CME",   "name": "CME 그룹",          "sector": "금융",    "market": "US"},
    {"yf": "ICE",   "code": "ICE",   "name": "인터콘티넨탈 익스체인지","sector": "금융","market": "US"},

    # 헬스케어 추가
    {"yf": "PFE",   "code": "PFE",   "name": "화이자",            "sector": "헬스케어","market": "US"},
    {"yf": "BMY",   "code": "BMY",   "name": "브리스톨-마이어스",  "sector": "헬스케어","market": "US"},
    {"yf": "AMGN",  "code": "AMGN",  "name": "암젠",              "sector": "헬스케어","market": "US"},
    {"yf": "GILD",  "code": "GILD",  "name": "길리어드 사이언스", "sector": "헬스케어","market": "US"},
    {"yf": "TMO",   "code": "TMO",   "name": "써모 피셔 사이언티픽","sector": "헬스케어","market": "US"},
    {"yf": "ABT",   "code": "ABT",   "name": "애보트 래버러토리스","sector": "헬스케어","market": "US"},
    {"yf": "ISRG",  "code": "ISRG",  "name": "인튜이티브 서지컬", "sector": "헬스케어","market": "US"},
    {"yf": "MDT",   "code": "MDT",   "name": "메드트로닉",        "sector": "헬스케어","market": "US"},

    # 소비재 추가
    {"yf": "NKE",   "code": "NKE",   "name": "나이키",            "sector": "소비재",  "market": "US"},
    {"yf": "SBUX",  "code": "SBUX",  "name": "스타벅스",          "sector": "소비재",  "market": "US"},
    {"yf": "HD",    "code": "HD",    "name": "홈디포",            "sector": "소비재",  "market": "US"},
    {"yf": "TGT",   "code": "TGT",   "name": "타겟",              "sector": "소비재",  "market": "US"},
    {"yf": "DIS",   "code": "DIS",   "name": "월트 디즈니",        "sector": "소비재",  "market": "US"},
    {"yf": "BKNG",  "code": "BKNG",  "name": "부킹 홀딩스",       "sector": "소비재",  "market": "US"},
    {"yf": "MAR",   "code": "MAR",   "name": "메리어트",          "sector": "소비재",  "market": "US"},

    # 에너지 추가
    {"yf": "COP",   "code": "COP",   "name": "코노코필립스",      "sector": "에너지",  "market": "US"},
    {"yf": "SLB",   "code": "SLB",   "name": "슐럼버거",          "sector": "에너지",  "market": "US"},
    {"yf": "OXY",   "code": "OXY",   "name": "옥시덴탈 페트롤리엄","sector": "에너지",  "market": "US"},

    # 산업재 추가
    {"yf": "RTX",   "code": "RTX",   "name": "RTX (레이시온)",    "sector": "산업재",  "market": "US"},
    {"yf": "HON",   "code": "HON",   "name": "허니웰",            "sector": "산업재",  "market": "US"},
    {"yf": "LMT",   "code": "LMT",   "name": "록히드 마틴",       "sector": "산업재",  "market": "US"},
    {"yf": "UPS",   "code": "UPS",   "name": "UPS",               "sector": "산업재",  "market": "US"},
    {"yf": "DE",    "code": "DE",    "name": "존 디어",           "sector": "산업재",  "market": "US"},

    # 유틸리티·리츠
    {"yf": "NEE",   "code": "NEE",   "name": "넥스트에라 에너지", "sector": "유틸리티","market": "US"},
    {"yf": "AMT",   "code": "AMT",   "name": "아메리칸 타워 (리츠)","sector": "리츠",  "market": "US"},
    {"yf": "PLD",   "code": "PLD",   "name": "프로로지스 (리츠)", "sector": "리츠",    "market": "US"},

    # 우주
    {"yf": "SPCX",  "code": "SPCX",  "name": "스페이스X",        "sector": "우주",    "market": "US"},
    {"yf": "RKLB",  "code": "RKLB",  "name": "로켓랩",           "sector": "우주",    "market": "US"},
    {"yf": "LUNR",  "code": "LUNR",  "name": "인튜이티브 머신스", "sector": "우주",    "market": "US"},
    {"yf": "ASTS",  "code": "ASTS",  "name": "AST 스페이스모바일","sector": "우주",    "market": "US"},

    # ============================================================
    # 한국 주요 종목
    # ============================================================

    # 반도체·IT
    {"yf": "005930.KS", "code": "005930", "name": "삼성전자",       "sector": "반도체·IT", "market": "KR"},
    {"yf": "000660.KS", "code": "000660", "name": "SK하이닉스",     "sector": "반도체·IT", "market": "KR"},
    {"yf": "066570.KS", "code": "066570", "name": "LG전자",         "sector": "반도체·IT", "market": "KR"},
    {"yf": "035420.KS", "code": "035420", "name": "NAVER",          "sector": "반도체·IT", "market": "KR"},
    {"yf": "035720.KS", "code": "035720", "name": "카카오",         "sector": "반도체·IT", "market": "KR"},
    {"yf": "042700.KS", "code": "042700", "name": "한미반도체",     "sector": "반도체·IT", "market": "KR"},
    {"yf": "000990.KS", "code": "000990", "name": "DB하이텍",       "sector": "반도체·IT", "market": "KR"},
    {"yf": "058470.KS", "code": "058470", "name": "리노공업",       "sector": "반도체·IT", "market": "KR"},
    {"yf": "402340.KS", "code": "402340", "name": "SK스퀘어",       "sector": "반도체·IT", "market": "KR"},
    {"yf": "377300.KS", "code": "377300", "name": "카카오페이",     "sector": "반도체·IT", "market": "KR"},
    {"yf": "323410.KS", "code": "323410", "name": "카카오뱅크",     "sector": "반도체·IT", "market": "KR"},

    # 자동차
    {"yf": "005380.KS", "code": "005380", "name": "현대차",         "sector": "자동차",    "market": "KR"},
    {"yf": "000270.KS", "code": "000270", "name": "기아",           "sector": "자동차",    "market": "KR"},
    {"yf": "012330.KS", "code": "012330", "name": "현대모비스",     "sector": "자동차",    "market": "KR"},
    {"yf": "011210.KS", "code": "011210", "name": "현대위아",       "sector": "자동차",    "market": "KR"},
    {"yf": "204320.KS", "code": "204320", "name": "HL만도",         "sector": "자동차",    "market": "KR"},

    # 배터리·화학
    {"yf": "373220.KS", "code": "373220", "name": "LG에너지솔루션", "sector": "배터리·화학","market": "KR"},
    {"yf": "006400.KS", "code": "006400", "name": "삼성SDI",        "sector": "배터리·화학","market": "KR"},
    {"yf": "051910.KS", "code": "051910", "name": "LG화학",         "sector": "배터리·화학","market": "KR"},
    {"yf": "096770.KS", "code": "096770", "name": "SK이노베이션",   "sector": "배터리·화학","market": "KR"},
    {"yf": "047050.KS", "code": "047050", "name": "포스코퓨처엠",   "sector": "배터리·화학","market": "KR"},
    {"yf": "010130.KS", "code": "010130", "name": "고려아연",       "sector": "배터리·화학","market": "KR"},

    # 철강·소재
    {"yf": "005490.KS", "code": "005490", "name": "POSCO홀딩스",   "sector": "철강·소재", "market": "KR"},
    {"yf": "004020.KS", "code": "004020", "name": "현대제철",       "sector": "철강·소재", "market": "KR"},

    # 바이오·헬스
    {"yf": "207940.KS", "code": "207940", "name": "삼성바이오로직스","sector": "바이오·헬스","market": "KR"},
    {"yf": "068270.KS", "code": "068270", "name": "셀트리온",       "sector": "바이오·헬스","market": "KR"},
    {"yf": "326030.KS", "code": "326030", "name": "SK바이오팜",     "sector": "바이오·헬스","market": "KR"},
    {"yf": "128940.KS", "code": "128940", "name": "한미약품",       "sector": "바이오·헬스","market": "KR"},
    {"yf": "000100.KS", "code": "000100", "name": "유한양행",       "sector": "바이오·헬스","market": "KR"},
    {"yf": "185750.KS", "code": "185750", "name": "종근당",         "sector": "바이오·헬스","market": "KR"},
    {"yf": "069620.KS", "code": "069620", "name": "대웅제약",       "sector": "바이오·헬스","market": "KR"},

    # 금융
    {"yf": "105560.KS", "code": "105560", "name": "KB금융",         "sector": "금융",      "market": "KR"},
    {"yf": "055550.KS", "code": "055550", "name": "신한지주",       "sector": "금융",      "market": "KR"},
    {"yf": "086790.KS", "code": "086790", "name": "하나금융지주",   "sector": "금융",      "market": "KR"},
    {"yf": "316140.KS", "code": "316140", "name": "우리금융지주",   "sector": "금융",      "market": "KR"},
    {"yf": "000810.KS", "code": "000810", "name": "삼성화재",       "sector": "금융",      "market": "KR"},
    {"yf": "032830.KS", "code": "032830", "name": "삼성생명",       "sector": "금융",      "market": "KR"},
    {"yf": "139480.KS", "code": "139480", "name": "이마트",         "sector": "유통",      "market": "KR"},

    # 엔터·미디어
    {"yf": "352820.KS", "code": "352820", "name": "HYBE",           "sector": "엔터·미디어","market": "KR"},
    {"yf": "041510.KS", "code": "041510", "name": "SM엔터테인먼트", "sector": "엔터·미디어","market": "KR"},
    {"yf": "035900.KS", "code": "035900", "name": "JYP엔터테인먼트","sector": "엔터·미디어","market": "KR"},
    {"yf": "122870.KS", "code": "122870", "name": "와이지엔터테인먼트","sector": "엔터·미디어","market": "KR"},

    # 통신
    {"yf": "017670.KS", "code": "017670", "name": "SK텔레콤",       "sector": "통신",      "market": "KR"},
    {"yf": "030200.KS", "code": "030200", "name": "KT",             "sector": "통신",      "market": "KR"},
    {"yf": "032640.KS", "code": "032640", "name": "LG유플러스",     "sector": "통신",      "market": "KR"},

    # 지주·유통
    {"yf": "028260.KS", "code": "028260", "name": "삼성물산",       "sector": "지주·유통", "market": "KR"},
    {"yf": "003550.KS", "code": "003550", "name": "LG",             "sector": "지주·유통", "market": "KR"},
    {"yf": "034730.KS", "code": "034730", "name": "SK",             "sector": "지주·유통", "market": "KR"},
    {"yf": "000880.KS", "code": "000880", "name": "한화",           "sector": "지주·유통", "market": "KR"},
    {"yf": "010950.KS", "code": "010950", "name": "S-Oil",          "sector": "에너지",    "market": "KR"},
    {"yf": "015760.KS", "code": "015760", "name": "한국전력",       "sector": "유틸리티",  "market": "KR"},
]

def safe_float(val):
    try:
        v = float(val)
        return None if math.isnan(v) or math.isinf(v) else v
    except (TypeError, ValueError):
        return None

result = []
for s in STOCKS:
    try:
        ticker = yf.Ticker(s["yf"])
        info   = ticker.info

        current = safe_float(info.get('currentPrice') or info.get('regularMarketPrice'))
        if current is None:
            print(f"✗ {s['code']}: 현재가 없음"); continue

        prev_close  = safe_float(info.get('previousClose') or info.get('regularMarketPreviousClose')) or current
        change      = round(current - prev_close, 2)
        change_pct  = round((change / prev_close) * 100, 2) if prev_close else 0

        trailing_per = safe_float(info.get('trailingPE'))
        forward_per  = safe_float(info.get('forwardPE'))
        pbr = safe_float(info.get('priceToBook'))
        if pbr is None:
            book_value = safe_float(info.get('bookValue'))
            if book_value and book_value > 0:
                pbr = round(current / book_value, 2)
        psr = safe_float(info.get('priceToSalesTrailing12Months'))
        roe_raw = safe_float(info.get('returnOnEquity'))  # yfinance: 0~1 소수
        roe = round(roe_raw * 100, 2) if roe_raw is not None else None  # % 변환
        eps = safe_float(info.get('trailingEps'))
        forward_eps = safe_float(info.get('forwardEps'))
        shares = safe_float(info.get('sharesOutstanding'))
        forward_net_income = int(forward_eps * shares) if (forward_eps is not None and shares is not None) else None
        operating_income = None
        net_income_ttm   = None

        # 한국 주식: 네이버 finance/summary에서 chartEps로 forward EPS 조회
        naver_forward_eps = None
        if s['market'] == 'KR':
            naver_forward_eps = naver_get_forward_eps(s['code'])

        # 한국 주식: DART 우선 조회
        if s['market'] == 'KR' and dart_corp_map:
            corp_code = dart_corp_map.get(s['code'])
            if corp_code:
                dart = dart_get_financials(DART_API_KEY, corp_code, current_year - 1)
                if dart is None:  # 작년 데이터 없으면 전전년도 시도
                    dart = dart_get_financials(DART_API_KEY, corp_code, current_year - 2)
                if dart:
                    operating_income = dart.get('operating_income')
                    net_income_ttm   = dart.get('net_income')
                    dart_revenue     = dart.get('revenue')
                    dart_equity      = dart.get('total_equity')
                    _mc = info.get('marketCap')
                    try:
                        _mc = int(_mc) if _mc else None
                    except (TypeError, ValueError):
                        _mc = None
                    # Trailing PER = 시가총액 / TTM순이익 (yfinance는 KR PER 미제공)
                    if _mc and net_income_ttm and net_income_ttm > 0:
                        trailing_per = round(_mc / net_income_ttm, 2)
                    # Forward PER = 현재가 / 연간 forward EPS (네이버 chartEps 4분기 합산)
                    forward_per = None
                    if naver_forward_eps and naver_forward_eps > 0:
                        forward_per = round(current / naver_forward_eps, 2)
                        # 예상 순이익 = 시가총액 / forward PER
                        if _mc and forward_per > 0:
                            forward_net_income = int(_mc / forward_per)
                    # PSR = 시가총액 / 매출액
                    if dart_revenue and dart_revenue > 0 and _mc:
                        psr = round(_mc / dart_revenue, 2)
                    # ROE = 순이익 / 자본총계
                    if dart_equity and dart_equity > 0 and net_income_ttm is not None:
                        roe = round(net_income_ttm / dart_equity * 100, 2)
                    # PBR = 시가총액 / 자본총계
                    if dart_equity and dart_equity > 0 and _mc:
                        pbr = round(_mc / dart_equity, 2)
                    if operating_income or net_income_ttm:
                        print(f"  [DART] 영업이익={operating_income} 순이익={net_income_ttm} 매출={dart_revenue} 자본={dart_equity}")

        # DART 없거나 미국 주식: yfinance fallback
        if operating_income is None:
            operating_income = info.get('operatingIncome')
            try:
                operating_income = int(operating_income) if operating_income else None
            except (TypeError, ValueError):
                operating_income = None
            if operating_income is None:
                try:
                    qf = ticker.quarterly_financials
                    if qf is not None and not qf.empty:
                        for label in ['Operating Income', 'Total Operating Income As Reported']:
                            if label in qf.index:
                                vals = qf.loc[label].dropna().iloc[:4]
                                if len(vals) > 0:
                                    operating_income = int(vals.sum())
                                break
                except Exception:
                    pass

        if net_income_ttm is None:
            net_income_ttm = info.get('netIncomeToCommon')
            try:
                net_income_ttm = int(net_income_ttm) if net_income_ttm else None
            except (TypeError, ValueError):
                net_income_ttm = None
            if net_income_ttm is None:
                try:
                    qf = ticker.quarterly_financials
                    if qf is not None and not qf.empty:
                        for label in ['Net Income', 'Net Income Common Stockholders']:
                            if label in qf.index:
                                vals = qf.loc[label].dropna().iloc[:4]
                                if len(vals) > 0:
                                    net_income_ttm = int(vals.sum())
                                break
                except Exception:
                    pass
        market_cap = info.get('marketCap')
        try:
            market_cap = int(market_cap) if market_cap else None
        except (TypeError, ValueError):
            market_cap = None

        currency = info.get('currency', 'USD')

        result.append({
            "code":       s["code"],
            "name":       s["name"],
            "sector":     s["sector"],
            "market":     s["market"],
            "currency":   currency,
            "current":    round(current, 2),
            "change":     change,
            "change_pct": change_pct,
            "trailing_per": round(trailing_per, 2) if trailing_per is not None else None,
            "forward_per":  round(forward_per, 2)  if forward_per  is not None else None,
            "pbr":        round(pbr, 2) if pbr is not None else None,
            "psr":        round(psr, 2) if psr is not None else None,
            "roe":              roe,
            "eps":                round(eps, 2) if eps is not None else None,
            "operating_income":   operating_income,
            "net_income_ttm":     net_income_ttm,
            "forward_net_income": forward_net_income,
            "forward_eps_krw":    naver_forward_eps if s['market'] == 'KR' else None,
            "market_cap":       market_cap,
        })
        cur = "₩" if currency == "KRW" else "$"
        tper_s = f"{trailing_per:.1f}" if trailing_per else "N/A"
        fper_s = f"{forward_per:.1f}"  if forward_per  else "N/A"
        pbr_s  = f"{pbr:.2f}"          if pbr          else "N/A"
        print(f"✓ {s['code']:12s} ({s['name']:16s})  {cur}{current:>12,.2f}  T.PER:{tper_s:>7}  F.PER:{fper_s:>7}  PBR:{pbr_s}")
    except Exception as e:
        print(f"✗ {s['code']}: {e}")

now_str = datetime.now().strftime('%Y-%m-%dT%H:%M')

with open('stocks.json', 'w', encoding='utf-8') as f:
    json.dump({"updated": now_str, "stocks": result}, f, ensure_ascii=False, separators=(',', ':'))

# Supabase upsert: updated_at 필드 추가 후 전송
supabase_rows = [{**r, 'updated_at': now_str} for r in result]
supabase_upsert('stocks', supabase_rows)

print(f"\n총 {len(result)}/{len(STOCKS)}개 업데이트 완료")