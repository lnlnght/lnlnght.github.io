import yfinance as yf
import json
import math
from datetime import datetime

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

    # ============================================================
    # 한국 주요 종목
    # ============================================================

    # 반도체·IT
    {"yf": "005930.KS", "code": "005930", "name": "삼성전자",       "sector": "반도체·IT", "market": "KR"},
    {"yf": "000660.KS", "code": "000660", "name": "SK하이닉스",     "sector": "반도체·IT", "market": "KR"},
    {"yf": "066570.KS", "code": "066570", "name": "LG전자",         "sector": "반도체·IT", "market": "KR"},
    {"yf": "035420.KS", "code": "035420", "name": "NAVER",          "sector": "반도체·IT", "market": "KR"},
    {"yf": "035720.KS", "code": "035720", "name": "카카오",         "sector": "반도체·IT", "market": "KR"},

    # 자동차
    {"yf": "005380.KS", "code": "005380", "name": "현대차",         "sector": "자동차",    "market": "KR"},
    {"yf": "000270.KS", "code": "000270", "name": "기아",           "sector": "자동차",    "market": "KR"},
    {"yf": "012330.KS", "code": "012330", "name": "현대모비스",     "sector": "자동차",    "market": "KR"},

    # 배터리·화학
    {"yf": "373220.KS", "code": "373220", "name": "LG에너지솔루션", "sector": "배터리·화학","market": "KR"},
    {"yf": "006400.KS", "code": "006400", "name": "삼성SDI",        "sector": "배터리·화학","market": "KR"},
    {"yf": "051910.KS", "code": "051910", "name": "LG화학",         "sector": "배터리·화학","market": "KR"},
    {"yf": "096770.KS", "code": "096770", "name": "SK이노베이션",   "sector": "배터리·화학","market": "KR"},

    # 바이오·헬스
    {"yf": "207940.KS", "code": "207940", "name": "삼성바이오로직스","sector": "바이오·헬스","market": "KR"},
    {"yf": "068270.KS", "code": "068270", "name": "셀트리온",       "sector": "바이오·헬스","market": "KR"},
    {"yf": "326030.KS", "code": "326030", "name": "SK바이오팜",     "sector": "바이오·헬스","market": "KR"},

    # 금융
    {"yf": "105560.KS", "code": "105560", "name": "KB금융",         "sector": "금융",      "market": "KR"},
    {"yf": "055550.KS", "code": "055550", "name": "신한지주",       "sector": "금융",      "market": "KR"},
    {"yf": "086790.KS", "code": "086790", "name": "하나금융지주",   "sector": "금융",      "market": "KR"},
    {"yf": "316140.KS", "code": "316140", "name": "우리금융지주",   "sector": "금융",      "market": "KR"},

    # 지주·유통
    {"yf": "028260.KS", "code": "028260", "name": "삼성물산",       "sector": "지주·유통", "market": "KR"},
    {"yf": "003550.KS", "code": "003550", "name": "LG",             "sector": "지주·유통", "market": "KR"},
    {"yf": "034730.KS", "code": "034730", "name": "SK",             "sector": "지주·유통", "market": "KR"},
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
        psr = safe_float(info.get('priceToSalesTrailing12Months'))
        roe = safe_float(info.get('returnOnEquity'))
        eps = safe_float(info.get('trailingEps'))
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
            "roe":        round(roe * 100, 2) if roe is not None else None,
            "eps":        round(eps, 2) if eps is not None else None,
            "market_cap": market_cap,
        })
        cur = "₩" if currency == "KRW" else "$"
        tper_s = f"{trailing_per:.1f}" if trailing_per else "N/A"
        fper_s = f"{forward_per:.1f}"  if forward_per  else "N/A"
        pbr_s  = f"{pbr:.2f}"          if pbr          else "N/A"
        print(f"✓ {s['code']:12s} ({s['name']:16s})  {cur}{current:>12,.2f}  T.PER:{tper_s:>7}  F.PER:{fper_s:>7}  PBR:{pbr_s}")
    except Exception as e:
        print(f"✗ {s['code']}: {e}")

with open('stocks.json', 'w', encoding='utf-8') as f:
    json.dump({"updated": datetime.now().strftime('%Y-%m-%dT%H:%M'), "stocks": result}, f, ensure_ascii=False, separators=(',', ':'))

print(f"\n총 {len(result)}/{len(STOCKS)}개 업데이트 완료")
