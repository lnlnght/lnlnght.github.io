import yfinance as yf
import json
import math
import os
import requests
from datetime import datetime, timedelta

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

def fetch_kr_etf_data():
    """KRX 데이터 API에서 한국 ETF 순자산총액·배당수익률 일괄 조회.
    {종목코드: {'aum': 원, 'dividend_yield': float}} 반환"""
    today = datetime.now()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'http://data.krx.co.kr/contents/MDC/MDI/mdiFunctions/etf/MDCMDI050101.cmd',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ko-KR,ko;q=0.9',
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    }
    # 세션 쿠키 획득 (없으면 HTTP 400 반환됨)
    session = requests.Session()
    try:
        session.get(
            'http://data.krx.co.kr/contents/MDC/MDI/mdiFunctions/etf/MDCMDI050101.cmd',
            headers={'User-Agent': headers['User-Agent']},
            timeout=15,
        )
        print(f"[KRX] 세션 쿠키 획득: {list(session.cookies.keys())}")
    except Exception as e:
        print(f"[KRX] 세션 초기화 실패 (무시): {e}")

    for offset in range(7):
        date_str = (today - timedelta(days=offset)).strftime('%Y%m%d')
        try:
            url = 'http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd'
            payload = {
                'bld': 'dbms/MDC/STAT/standard/MDCSTAT04301',
                'trdDd': date_str,
                'share': '1',
                'csvxls_isNo': 'false',
            }
            res = session.post(url, data=payload, headers=headers, timeout=30)
            if res.status_code != 200:
                print(f"[KRX] {date_str} HTTP {res.status_code} body={res.text[:200]}")
                continue
            data = res.json()
            items = data.get('output', [])
            if not items:
                print(f"[KRX] {date_str} 데이터 없음 (주말/공휴일?)")
                continue
            # 첫 항목의 키 출력 (디버그용, 한 번만)
            if items:
                print(f"[KRX] 응답 필드: {list(items[0].keys())}")
            result = {}
            for item in items:
                code = item.get('ISU_SRT_CD', '').strip()
                if not code:
                    continue
                aum = 0
                raw_aum = item.get('NETASST_TOTAMT', '').replace(',', '').strip()
                if raw_aum:
                    try:
                        v = int(raw_aum)
                        if v > 0:
                            aum = v * 1000  # 천원 → 원
                    except ValueError:
                        pass
                # 배당수익률 필드 탐색 (필드명이 버전마다 다를 수 있음)
                div_yield = 0.0
                for dy_key in ('DVDND_YD', 'DVD_YD', 'DVDNDYD', 'YELD'):
                    raw_dy = item.get(dy_key, '').replace(',', '').replace('%', '').strip()
                    if raw_dy:
                        try:
                            div_yield = float(raw_dy) / 100  # % → 소수
                            break
                        except ValueError:
                            pass
                if aum > 0 or div_yield > 0:
                    result[code] = {'aum': aum, 'dividend_yield': div_yield}
            if result:
                print(f"[KRX] ETF {len(result)}개 로드 ({date_str})")
                return result
        except Exception as e:
            print(f"[KRX] {date_str} 조회 실패: {e}")
    print("[KRX] 조회 실패: 최근 7일 모두 데이터 없음")
    return {}

ETFS = [
    # ============================================================
    # 미국 ETF (98개)
    # ============================================================

    # 지수 (17)
    {"yf": "SPY",  "code": "SPY",  "name": "S&P 500 (SPDR)",      "category": "지수",    "market": "US", "currency": "USD"},
    {"yf": "VOO",  "code": "VOO",  "name": "S&P 500 (Vanguard)",   "category": "지수",    "market": "US", "currency": "USD"},
    {"yf": "QQQ",  "code": "QQQ",  "name": "NASDAQ 100",            "category": "지수",    "market": "US", "currency": "USD"},
    {"yf": "VTI",  "code": "VTI",  "name": "미국 전체 시장",        "category": "지수",    "market": "US", "currency": "USD"},
    {"yf": "IWM",  "code": "IWM",  "name": "러셀 2000 소형주",      "category": "지수",    "market": "US", "currency": "USD"},
    {"yf": "DIA",  "code": "DIA",  "name": "다우존스 산업평균",     "category": "지수",    "market": "US", "currency": "USD"},
    {"yf": "RSP",  "code": "RSP",  "name": "S&P 500 동일가중",     "category": "지수",    "market": "US", "currency": "USD"},
    {"yf": "ACWI", "code": "ACWI", "name": "전세계 주식 (ACWI)",   "category": "지수",    "market": "US", "currency": "USD"},
    {"yf": "EEM",  "code": "EEM",  "name": "신흥국 (iShares)",     "category": "지수",    "market": "US", "currency": "USD"},
    {"yf": "VWO",  "code": "VWO",  "name": "신흥국 (Vanguard)",    "category": "지수",    "market": "US", "currency": "USD"},
    {"yf": "VEA",  "code": "VEA",  "name": "선진국 (미국 제외)",    "category": "지수",    "market": "US", "currency": "USD"},
    {"yf": "EFA",  "code": "EFA",  "name": "MSCI EAFE",             "category": "지수",    "market": "US", "currency": "USD"},
    {"yf": "VT",   "code": "VT",   "name": "전세계 주식 (Vanguard)", "category": "지수",    "market": "US", "currency": "USD"},
    {"yf": "VXUS", "code": "VXUS", "name": "미국 제외 전세계",       "category": "지수",    "market": "US", "currency": "USD"},
    {"yf": "VGK",  "code": "VGK",  "name": "유럽 주식",              "category": "지수",    "market": "US", "currency": "USD"},
    {"yf": "FXI",  "code": "FXI",  "name": "중국 대형주",            "category": "지수",    "market": "US", "currency": "USD"},
    {"yf": "EWZ",  "code": "EWZ",  "name": "브라질",                 "category": "지수",    "market": "US", "currency": "USD"},

    # 배당 (12)
    {"yf": "SCHD", "code": "SCHD", "name": "배당 성장",             "category": "배당",    "market": "US", "currency": "USD"},
    {"yf": "VYM",  "code": "VYM",  "name": "고배당 (Vanguard)",    "category": "배당",    "market": "US", "currency": "USD"},
    {"yf": "JEPI", "code": "JEPI", "name": "커버드콜 배당",         "category": "배당",    "market": "US", "currency": "USD"},
    {"yf": "DGRO", "code": "DGRO", "name": "배당 성장 (iShares)",   "category": "배당",    "market": "US", "currency": "USD"},
    {"yf": "SPYD", "code": "SPYD", "name": "S&P 500 고배당",        "category": "배당",    "market": "US", "currency": "USD"},
    {"yf": "NOBL", "code": "NOBL", "name": "배당 귀족 (25Y+ 연속)", "category": "배당",    "market": "US", "currency": "USD"},
    {"yf": "HDV",  "code": "HDV",  "name": "고배당 (iShares)",     "category": "배당",    "market": "US", "currency": "USD"},
    {"yf": "PFF",  "code": "PFF",  "name": "우선주",                "category": "배당",    "market": "US", "currency": "USD"},
    {"yf": "JEPQ", "code": "JEPQ", "name": "나스닥 커버드콜 배당",  "category": "배당",    "market": "US", "currency": "USD"},
    {"yf": "QYLD", "code": "QYLD", "name": "나스닥 100 커버드콜",   "category": "배당",    "market": "US", "currency": "USD"},
    {"yf": "DVY",  "code": "DVY",  "name": "고배당 선별 (iShares)", "category": "배당",    "market": "US", "currency": "USD"},
    {"yf": "DGRW", "code": "DGRW", "name": "배당 성장 (WisdomTree)","category": "배당",    "market": "US", "currency": "USD"},

    # 채권 (14)
    {"yf": "TLT",  "code": "TLT",  "name": "장기 국채 20Y+",       "category": "채권",    "market": "US", "currency": "USD"},
    {"yf": "IEF",  "code": "IEF",  "name": "중기 국채 7-10Y",      "category": "채권",    "market": "US", "currency": "USD"},
    {"yf": "SHY",  "code": "SHY",  "name": "단기 국채 1-3Y",       "category": "채권",    "market": "US", "currency": "USD"},
    {"yf": "AGG",  "code": "AGG",  "name": "종합 채권 (iShares)",   "category": "채권",    "market": "US", "currency": "USD"},
    {"yf": "BND",  "code": "BND",  "name": "종합 채권 (Vanguard)",  "category": "채권",    "market": "US", "currency": "USD"},
    {"yf": "LQD",  "code": "LQD",  "name": "투자등급 회사채",       "category": "채권",    "market": "US", "currency": "USD"},
    {"yf": "HYG",  "code": "HYG",  "name": "하이일드 채권",         "category": "채권",    "market": "US", "currency": "USD"},
    {"yf": "EMB",  "code": "EMB",  "name": "신흥국 채권",           "category": "채권",    "market": "US", "currency": "USD"},
    {"yf": "TIP",  "code": "TIP",  "name": "물가연동국채 (TIPS)",   "category": "채권",    "market": "US", "currency": "USD"},
    {"yf": "SGOV", "code": "SGOV", "name": "초단기 T-Bill",         "category": "채권",    "market": "US", "currency": "USD"},
    {"yf": "VCIT", "code": "VCIT", "name": "중기 회사채 (Vanguard)","category": "채권",    "market": "US", "currency": "USD"},
    {"yf": "BNDX", "code": "BNDX", "name": "해외 채권 (Vanguard)",  "category": "채권",    "market": "US", "currency": "USD"},
    {"yf": "VGIT", "code": "VGIT", "name": "중기 국채 (Vanguard)",  "category": "채권",    "market": "US", "currency": "USD"},
    {"yf": "MUB",  "code": "MUB",  "name": "지방채 (iShares)",      "category": "채권",    "market": "US", "currency": "USD"},

    # 섹터 — S&P 500 11개 섹터 전체 (11)
    {"yf": "XLK",  "code": "XLK",  "name": "기술",                  "category": "섹터",    "market": "US", "currency": "USD"},
    {"yf": "XLC",  "code": "XLC",  "name": "통신 서비스",           "category": "섹터",    "market": "US", "currency": "USD"},
    {"yf": "XLV",  "code": "XLV",  "name": "헬스케어",              "category": "섹터",    "market": "US", "currency": "USD"},
    {"yf": "XLF",  "code": "XLF",  "name": "금융",                  "category": "섹터",    "market": "US", "currency": "USD"},
    {"yf": "XLY",  "code": "XLY",  "name": "소비재 (경기)",         "category": "섹터",    "market": "US", "currency": "USD"},
    {"yf": "XLP",  "code": "XLP",  "name": "필수소비재",            "category": "섹터",    "market": "US", "currency": "USD"},
    {"yf": "XLI",  "code": "XLI",  "name": "산업재",                "category": "섹터",    "market": "US", "currency": "USD"},
    {"yf": "XLE",  "code": "XLE",  "name": "에너지",                "category": "섹터",    "market": "US", "currency": "USD"},
    {"yf": "XLU",  "code": "XLU",  "name": "유틸리티",              "category": "섹터",    "market": "US", "currency": "USD"},
    {"yf": "XLB",  "code": "XLB",  "name": "소재",                  "category": "섹터",    "market": "US", "currency": "USD"},
    {"yf": "XLRE", "code": "XLRE", "name": "리츠 (부동산)",         "category": "섹터",    "market": "US", "currency": "USD"},

    # 테마 (35)
    {"yf": "SOXX", "code": "SOXX", "name": "반도체",                "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "SMH",  "code": "SMH",  "name": "반도체 (VanEck)",       "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "ARKK", "code": "ARKK", "name": "혁신 기술 (ARK)",       "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "ARKW", "code": "ARKW", "name": "차세대 인터넷 (ARK)",   "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "ARKG", "code": "ARKG", "name": "유전체 혁신 (ARK)",     "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "ARKF", "code": "ARKF", "name": "핀테크 (ARK)",          "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "BOTZ", "code": "BOTZ", "name": "로보틱스·AI",           "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "AIQ",  "code": "AIQ",  "name": "AI & 빅데이터",         "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "ROBO", "code": "ROBO", "name": "로보틱스 (ROBO Global)","category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "ICLN", "code": "ICLN", "name": "청정에너지",            "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "DRIV", "code": "DRIV", "name": "전기차·자율주행",       "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "LIT",  "code": "LIT",  "name": "리튬·배터리",           "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "CLOU", "code": "CLOU", "name": "클라우드 컴퓨팅",       "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "IBIT", "code": "IBIT", "name": "비트코인 현물",         "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "FBTC", "code": "FBTC", "name": "비트코인 현물 (피델리티)","category": "테마",   "market": "US", "currency": "USD"},
    {"yf": "BITO", "code": "BITO", "name": "비트코인 선물",         "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "ETHA", "code": "ETHA", "name": "이더리움 현물",         "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "CIBR", "code": "CIBR", "name": "사이버보안",            "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "HACK", "code": "HACK", "name": "사이버보안 (PureFunds)","category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "VNQ",  "code": "VNQ",  "name": "리츠 (Vanguard)",       "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "IBB",  "code": "IBB",  "name": "바이오테크",            "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "XBI",  "code": "XBI",  "name": "바이오테크 동일가중",   "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "KWEB", "code": "KWEB", "name": "중국 인터넷",           "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "EWJ",  "code": "EWJ",  "name": "일본",                  "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "INDA", "code": "INDA", "name": "인도",                  "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "EWY",  "code": "EWY",  "name": "한국",                  "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "EWT",  "code": "EWT",  "name": "대만",                  "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "EWG",  "code": "EWG",  "name": "독일",                  "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "EWU",  "code": "EWU",  "name": "영국",                  "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "EWA",  "code": "EWA",  "name": "호주",                  "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "VNM",  "code": "VNM",  "name": "베트남",                "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "JETS", "code": "JETS", "name": "항공·여행",             "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "UFO",  "code": "UFO",  "name": "우주·항공",             "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "HERO", "code": "HERO", "name": "게임·e스포츠",          "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "ESPO", "code": "ESPO", "name": "게임 (VanEck)",         "category": "테마",    "market": "US", "currency": "USD"},

    # 원자재 (13)
    {"yf": "GLD",  "code": "GLD",  "name": "금 (SPDR)",             "category": "원자재",  "market": "US", "currency": "USD"},
    {"yf": "IAU",  "code": "IAU",  "name": "금 (iShares)",          "category": "원자재",  "market": "US", "currency": "USD"},
    {"yf": "GLDM", "code": "GLDM", "name": "금 저비용 (SPDR)",      "category": "원자재",  "market": "US", "currency": "USD"},
    {"yf": "SLV",  "code": "SLV",  "name": "은",                    "category": "원자재",  "market": "US", "currency": "USD"},
    {"yf": "USO",  "code": "USO",  "name": "원유 (WTI)",            "category": "원자재",  "market": "US", "currency": "USD"},
    {"yf": "DBA",  "code": "DBA",  "name": "농산물",                "category": "원자재",  "market": "US", "currency": "USD"},
    {"yf": "UNG",  "code": "UNG",  "name": "천연가스",              "category": "원자재",  "market": "US", "currency": "USD"},
    {"yf": "PDBC", "code": "PDBC", "name": "분산 원자재",           "category": "원자재",  "market": "US", "currency": "USD"},
    {"yf": "COPX", "code": "COPX", "name": "구리 광업",             "category": "원자재",  "market": "US", "currency": "USD"},
    {"yf": "DBB",  "code": "DBB",  "name": "산업금속 (구리·알루미늄·아연)", "category": "원자재", "market": "US", "currency": "USD"},
    {"yf": "PPLT", "code": "PPLT", "name": "플래티넘",              "category": "원자재",  "market": "US", "currency": "USD"},
    {"yf": "BNO",  "code": "BNO",  "name": "원유 (브렌트)",         "category": "원자재",  "market": "US", "currency": "USD"},
    {"yf": "REMX", "code": "REMX", "name": "희토류·희귀금속",       "category": "원자재",  "market": "US", "currency": "USD"},

    # 레버리지·인버스 (13) — 고위험 상품
    {"yf": "TQQQ", "code": "TQQQ", "name": "NASDAQ 100 3x",        "category": "레버리지", "market": "US", "currency": "USD"},
    {"yf": "SQQQ", "code": "SQQQ", "name": "NASDAQ 100 -3x",       "category": "레버리지", "market": "US", "currency": "USD"},
    {"yf": "UPRO", "code": "UPRO", "name": "S&P 500 3x",           "category": "레버리지", "market": "US", "currency": "USD"},
    {"yf": "SPXU", "code": "SPXU", "name": "S&P 500 -3x",         "category": "레버리지", "market": "US", "currency": "USD"},
    {"yf": "UVXY", "code": "UVXY", "name": "VIX 변동성 1.5x",      "category": "레버리지", "market": "US", "currency": "USD"},
    {"yf": "QLD",  "code": "QLD",  "name": "NASDAQ 100 2x",        "category": "레버리지", "market": "US", "currency": "USD"},
    {"yf": "SSO",  "code": "SSO",  "name": "S&P 500 2x",           "category": "레버리지", "market": "US", "currency": "USD"},
    {"yf": "SDS",  "code": "SDS",  "name": "S&P 500 -2x",          "category": "레버리지", "market": "US", "currency": "USD"},
    {"yf": "QID",  "code": "QID",  "name": "NASDAQ 100 -2x",       "category": "레버리지", "market": "US", "currency": "USD"},
    {"yf": "SOXL", "code": "SOXL", "name": "반도체 3x",            "category": "레버리지", "market": "US", "currency": "USD"},
    {"yf": "SOXS", "code": "SOXS", "name": "반도체 -3x",           "category": "레버리지", "market": "US", "currency": "USD"},

    # ============================================================
    # 한국 ETF (44개, Yahoo Finance .KS suffix)
    # ============================================================

    # 지수 — 국내 (6)
    {"yf": "069500.KS", "code": "069500", "name": "KODEX 200",                  "category": "지수",    "market": "KR", "currency": "KRW", "er": 0.0015},
    {"yf": "102110.KS", "code": "102110", "name": "TIGER 200",                  "category": "지수",    "market": "KR", "currency": "KRW", "er": 0.0005},
    {"yf": "229200.KS", "code": "229200", "name": "KODEX KOSDAQ150",            "category": "지수",    "market": "KR", "currency": "KRW", "er": 0.0026},
    {"yf": "153130.KS", "code": "153130", "name": "KODEX 단기채권",             "category": "지수",    "market": "KR", "currency": "KRW", "er": 0.0015},
    {"yf": "148020.KS", "code": "148020", "name": "KODEX KRX300",               "category": "지수",    "market": "KR", "currency": "KRW", "er": 0.0019},
    {"yf": "332620.KS", "code": "332620", "name": "TIGER MSCI Korea TR",        "category": "지수",    "market": "KR", "currency": "KRW", "er": 0.0015},
    # 지수 — 해외 (13)
    {"yf": "360750.KS", "code": "360750", "name": "TIGER 미국S&P500",           "category": "지수",    "market": "KR", "currency": "KRW", "er": 0.00045},
    {"yf": "133690.KS", "code": "133690", "name": "TIGER 미국나스닥100",        "category": "지수",    "market": "KR", "currency": "KRW", "er": 0.0007},
    {"yf": "379800.KS", "code": "379800", "name": "KODEX 미국S&P500TR",         "category": "지수",    "market": "KR", "currency": "KRW", "er": 0.0005},
    {"yf": "195980.KS", "code": "195980", "name": "TIGER 유로STOXX50",          "category": "지수",    "market": "KR", "currency": "KRW", "er": 0.0035},
    {"yf": "241180.KS", "code": "241180", "name": "TIGER 일본니케이225",        "category": "지수",    "market": "KR", "currency": "KRW", "er": 0.0049},
    {"yf": "192090.KS", "code": "192090", "name": "TIGER 차이나CSI300",         "category": "지수",    "market": "KR", "currency": "KRW", "er": 0.0053},
    {"yf": "411060.KS", "code": "411060", "name": "ACE 미국S&P500",             "category": "지수",    "market": "KR", "currency": "KRW", "er": 0.0007},
    {"yf": "367380.KS", "code": "367380", "name": "KODEX 미국나스닥100TR",      "category": "지수",    "market": "KR", "currency": "KRW", "er": 0.0005},
    {"yf": "352560.KS", "code": "352560", "name": "TIGER 미국테크TOP10 INDXX",  "category": "지수",    "market": "KR", "currency": "KRW", "er": 0.0049},
    {"yf": "287310.KS", "code": "287310", "name": "TIGER 인도니프티50",         "category": "지수",    "market": "KR", "currency": "KRW", "er": 0.0049},
    {"yf": "245710.KS", "code": "245710", "name": "TIGER 베트남VN30",           "category": "지수",    "market": "KR", "currency": "KRW", "er": 0.0049},
    {"yf": "396520.KS", "code": "396520", "name": "TIGER 미국S&P500동일가중",   "category": "지수",    "market": "KR", "currency": "KRW", "er": 0.0007},
    {"yf": "453810.KS", "code": "453810", "name": "KODEX 미국S&P동일가중",      "category": "지수",    "market": "KR", "currency": "KRW", "er": 0.0005},

    # 배당 (10)
    {"yf": "279530.KS", "code": "279530", "name": "KODEX 배당가치",             "category": "배당",    "market": "KR", "currency": "KRW", "er": 0.0037},
    {"yf": "458730.KS", "code": "458730", "name": "TIGER 미국배당다우존스",     "category": "배당",    "market": "KR", "currency": "KRW", "er": 0.0013},
    {"yf": "441680.KS", "code": "441680", "name": "KODEX 미국배당프리미엄",     "category": "배당",    "market": "KR", "currency": "KRW", "er": 0.0049},
    {"yf": "266160.KS", "code": "266160", "name": "KODEX 고배당",               "category": "배당",    "market": "KR", "currency": "KRW", "er": 0.002},
    {"yf": "319640.KS", "code": "319640", "name": "TIGER 배당성장",             "category": "배당",    "market": "KR", "currency": "KRW", "er": 0.0015},
    {"yf": "455890.KS", "code": "455890", "name": "TIGER 미국배당+7%프리미엄",  "category": "배당",    "market": "KR", "currency": "KRW", "er": 0.0049},
    {"yf": "480040.KS", "code": "480040", "name": "ACE 미국배당다우존스",       "category": "배당",    "market": "KR", "currency": "KRW", "er": 0.0005},
    {"yf": "494390.KS", "code": "494390", "name": "TIGER 미국배당+10%프리미엄", "category": "배당",    "market": "KR", "currency": "KRW", "er": 0.0049},
    {"yf": "460130.KS", "code": "460130", "name": "KODEX 미국배당다우존스",     "category": "배당",    "market": "KR", "currency": "KRW", "er": 0.0005},
    {"yf": "448290.KS", "code": "448290", "name": "TIGER 월배당고배당주커버드콜ATM","category": "배당","market": "KR", "currency": "KRW", "er": 0.0049},

    # 채권 (8)
    {"yf": "114820.KS", "code": "114820", "name": "KODEX 국고채3년",            "category": "채권",    "market": "KR", "currency": "KRW", "er": 0.0015},
    {"yf": "148070.KS", "code": "148070", "name": "KOSEF 국고채10년",            "category": "채권",    "market": "KR", "currency": "KRW", "er": 0.0015},
    {"yf": "304660.KS", "code": "304660", "name": "KODEX 미국채30년선물(H)",     "category": "채권",    "market": "KR", "currency": "KRW", "er": 0.003},
    {"yf": "453850.KS", "code": "453850", "name": "KODEX 미국채10년선물",        "category": "채권",    "market": "KR", "currency": "KRW", "er": 0.0007},
    {"yf": "385560.KS", "code": "385560", "name": "TIGER 단기통안채",           "category": "채권",    "market": "KR", "currency": "KRW", "er": 0.0006},
    {"yf": "273130.KS", "code": "273130", "name": "KODEX 종합채권(AA-이상)액티브","category": "채권",  "market": "KR", "currency": "KRW", "er": 0.0009},
    {"yf": "472160.KS", "code": "472160", "name": "ACE 미국30년국채액티브(H)",  "category": "채권",    "market": "KR", "currency": "KRW", "er": 0.0005},
    {"yf": "453840.KS", "code": "453840", "name": "KODEX 미국30년국채+12%프리미엄","category": "채권",  "market": "KR", "currency": "KRW", "er": 0.0049},

    # 섹터 (12)
    {"yf": "091160.KS", "code": "091160", "name": "KODEX 반도체",               "category": "섹터",    "market": "KR", "currency": "KRW", "er": 0.0045},
    {"yf": "396500.KS", "code": "396500", "name": "TIGER 반도체TOP10",           "category": "섹터",    "market": "KR", "currency": "KRW", "er": 0.0045},
    {"yf": "448540.KS", "code": "448540", "name": "KODEX 미국반도체MV",          "category": "섹터",    "market": "KR", "currency": "KRW", "er": 0.0005},
    {"yf": "143850.KS", "code": "143850", "name": "TIGER 미국나스닥바이오",      "category": "섹터",    "market": "KR", "currency": "KRW", "er": 0.0049},
    {"yf": "139290.KS", "code": "139290", "name": "TIGER 200 IT",                "category": "섹터",    "market": "KR", "currency": "KRW", "er": 0.0015},
    {"yf": "227550.KS", "code": "227550", "name": "TIGER 200 헬스케어",          "category": "섹터",    "market": "KR", "currency": "KRW", "er": 0.0015},
    {"yf": "091180.KS", "code": "091180", "name": "KODEX 자동차",                "category": "섹터",    "market": "KR", "currency": "KRW", "er": 0.0045},
    {"yf": "102970.KS", "code": "102970", "name": "TIGER 200 금융",              "category": "섹터",    "market": "KR", "currency": "KRW", "er": 0.0015},
    {"yf": "244620.KS", "code": "244620", "name": "KODEX 은행",                  "category": "섹터",    "market": "KR", "currency": "KRW", "er": 0.0045},
    {"yf": "140710.KS", "code": "140710", "name": "TIGER 200 에너지화학",        "category": "섹터",    "market": "KR", "currency": "KRW", "er": 0.0015},
    {"yf": "140700.KS", "code": "140700", "name": "TIGER 200 산업재",            "category": "섹터",    "market": "KR", "currency": "KRW", "er": 0.0015},
    {"yf": "484990.KS", "code": "484990", "name": "TIGER 조선TOP10",             "category": "섹터",    "market": "KR", "currency": "KRW", "er": 0.0045},

    # 테마 (14)
    {"yf": "305720.KS", "code": "305720", "name": "KODEX 2차전지산업",           "category": "테마",    "market": "KR", "currency": "KRW", "er": 0.0045},
    {"yf": "381170.KS", "code": "381170", "name": "TIGER 미국테크TOP10",         "category": "테마",    "market": "KR", "currency": "KRW", "er": 0.0049},
    {"yf": "364980.KS", "code": "364980", "name": "TIGER 글로벌사이버보안",      "category": "테마",    "market": "KR", "currency": "KRW", "er": 0.0049},
    {"yf": "371460.KS", "code": "371460", "name": "TIGER 글로벌AI",              "category": "테마",    "market": "KR", "currency": "KRW", "er": 0.0049},
    {"yf": "334700.KS", "code": "334700", "name": "KODEX 바이오",                "category": "테마",    "market": "KR", "currency": "KRW", "er": 0.0045},
    {"yf": "425040.KS", "code": "425040", "name": "TIGER 글로벌반도체핵심공정",  "category": "테마",    "market": "KR", "currency": "KRW", "er": 0.0049},
    {"yf": "472090.KS", "code": "472090", "name": "TIGER AI코리아그로스액티브",  "category": "테마",    "market": "KR", "currency": "KRW", "er": 0.0059},
    {"yf": "463050.KS", "code": "463050", "name": "KODEX 미국AI테크TOP10",       "category": "테마",    "market": "KR", "currency": "KRW", "er": 0.0045},
    {"yf": "395160.KS", "code": "395160", "name": "TIGER 미국필라델피아반도체나스닥","category": "테마", "market": "KR", "currency": "KRW", "er": 0.0049},
    {"yf": "462900.KS", "code": "462900", "name": "TIGER 미국빅테크10",          "category": "테마",    "market": "KR", "currency": "KRW", "er": 0.0049},
    {"yf": "489430.KS", "code": "489430", "name": "KODEX 국방",                  "category": "테마",    "market": "KR", "currency": "KRW", "er": 0.0045},
    {"yf": "424410.KS", "code": "424410", "name": "TIGER 비트코인레버리지MX",    "category": "테마",    "market": "KR", "currency": "KRW", "er": 0.0099},
    {"yf": "482730.KS", "code": "482730", "name": "ACE 비트코인현물",            "category": "테마",    "market": "KR", "currency": "KRW", "er": 0.0034},
    {"yf": "494070.KS", "code": "494070", "name": "KODEX 비트코인현물",          "category": "테마",    "market": "KR", "currency": "KRW", "er": 0.0034},

    # 원자재 (6)
    {"yf": "132030.KS", "code": "132030", "name": "KODEX 골드선물(H)",           "category": "원자재",  "market": "KR", "currency": "KRW", "er": 0.0068},
    {"yf": "130680.KS", "code": "130680", "name": "TIGER 원유선물Enhanced",      "category": "원자재",  "market": "KR", "currency": "KRW", "er": 0.0049},
    {"yf": "292050.KS", "code": "292050", "name": "TIGER 구리실물",              "category": "원자재",  "market": "KR", "currency": "KRW", "er": 0.0049},
    {"yf": "411210.KS", "code": "411210", "name": "ACE KRX금현물",               "category": "원자재",  "market": "KR", "currency": "KRW", "er": 0.003},
    {"yf": "449170.KS", "code": "449170", "name": "TIGER 금은선물(H)",           "category": "원자재",  "market": "KR", "currency": "KRW", "er": 0.0049},
    {"yf": "473420.KS", "code": "473420", "name": "KODEX 천연가스선물(H)",       "category": "원자재",  "market": "KR", "currency": "KRW", "er": 0.0068},

    # 레버리지·인버스 (8)
    {"yf": "122630.KS", "code": "122630", "name": "KODEX 레버리지 2x",           "category": "레버리지","market": "KR", "currency": "KRW", "er": 0.0049},
    {"yf": "114800.KS", "code": "114800", "name": "KODEX 인버스",                 "category": "레버리지","market": "KR", "currency": "KRW", "er": 0.0015},
    {"yf": "233740.KS", "code": "233740", "name": "KODEX 코스닥150 레버리지",     "category": "레버리지","market": "KR", "currency": "KRW", "er": 0.0064},
    {"yf": "252670.KS", "code": "252670", "name": "KODEX 200선물인버스2X",        "category": "레버리지","market": "KR", "currency": "KRW", "er": 0.0064},
    {"yf": "251340.KS", "code": "251340", "name": "KODEX 코스닥150 인버스",       "category": "레버리지","market": "KR", "currency": "KRW", "er": 0.0049},
    {"yf": "275980.KS", "code": "275980", "name": "TIGER 200선물레버리지",        "category": "레버리지","market": "KR", "currency": "KRW", "er": 0.0064},
    {"yf": "406810.KS", "code": "406810", "name": "KODEX 나스닥100레버리지(합성)","category": "레버리지","market": "KR", "currency": "KRW", "er": 0.0064},
    {"yf": "438330.KS", "code": "438330", "name": "TIGER 미국S&P500레버리지(합성)","category": "레버리지","market": "KR", "currency": "KRW", "er": 0.0064},
]

kr_etf_data = fetch_kr_etf_data()

result = []
for s in ETFS:
    try:
        ticker = yf.Ticker(s["yf"])
        fi     = ticker.fast_info
        info   = ticker.info

        current    = round(float(fi.last_price), 2)
        prev_close = round(float(fi.previous_close), 2)
        change     = round(current - prev_close, 2)
        change_pct = round((change / prev_close) * 100, 2)

        hist = ticker.history(period="1y")
        if hist.empty:
            print(f"✗ {s['code']}: 히스토리 없음"); continue

        high_52w = round(float(hist['High'].max()), 2)
        low_52w  = round(float(hist['Low'].min()), 2)

        try:
            expense_ratio = s.get('er') or float(info.get('annualReportExpenseRatio') or info.get('expenseRatio') or 0)
        except (TypeError, ValueError):
            expense_ratio = s.get('er') or 0

        try:
            dividend_yield = float(info.get('yield') or info.get('trailingAnnualDividendYield') or 0)
        except (TypeError, ValueError):
            dividend_yield = 0

        try:
            total_assets = int(info.get('totalAssets') or 0)
        except (TypeError, ValueError):
            total_assets = 0
        # 한국 ETF: KRX 데이터로 덮어씀
        if s['market'] == 'KR' and s['code'] in kr_etf_data:
            kd = kr_etf_data[s['code']]
            if kd['aum'] > 0:
                total_assets = kd['aum']
            if kd['dividend_yield'] > 0:
                dividend_yield = kd['dividend_yield']

        result.append({
            "code":           s["code"],
            "name":           s["name"],
            "category":       s["category"],
            "market":         s["market"],
            "currency":       s["currency"],
            "current":        current,
            "change":         change,
            "change_pct":     change_pct,
            "expense_ratio":  round(expense_ratio, 4),
            "dividend_yield": round(dividend_yield, 4),
            "total_assets":   total_assets,
            "high_52w":       high_52w,
            "low_52w":        low_52w,
        })
        cur_sym = "₩" if s["currency"] == "KRW" else "$"
        print(f"✓ {s['code']:8s} ({s['name']:20s})  {cur_sym}{current:>12,.2f}  {change:+.2f} ({change_pct:+.2f}%)")
    except Exception as e:
        print(f"✗ {s['code']}: {e}")

now_str = datetime.now().strftime('%Y-%m-%dT%H:%M')

with open('etfs.json', 'w', encoding='utf-8') as f:
    json.dump({"updated": now_str, "etfs": result}, f, ensure_ascii=False, separators=(',', ':'))

supabase_rows = [{**r, 'updated_at': now_str} for r in result]
supabase_upsert('etfs', supabase_rows)

print(f"\n총 {len(result)}/{len(ETFS)}개 업데이트 완료")