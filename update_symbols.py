import yfinance as yf
import json
from datetime import datetime

STOCKS = [
    # 국내 주요 종목 (시가총액 상위) — Yahoo Finance uses .KS suffix for KOSPI
    {"yf": "005930.KS", "code": "005930", "name": "삼성전자",        "market": "KR", "currency": "KRW"},
    {"yf": "000660.KS", "code": "000660", "name": "SK하이닉스",      "market": "KR", "currency": "KRW"},
    {"yf": "373220.KS", "code": "373220", "name": "LG에너지솔루션",  "market": "KR", "currency": "KRW"},
    {"yf": "207940.KS", "code": "207940", "name": "삼성바이오로직스","market": "KR", "currency": "KRW"},
    {"yf": "005380.KS", "code": "005380", "name": "현대차",          "market": "KR", "currency": "KRW"},
    {"yf": "000270.KS", "code": "000270", "name": "기아",            "market": "KR", "currency": "KRW"},
    {"yf": "105560.KS", "code": "105560", "name": "KB금융",          "market": "KR", "currency": "KRW"},
    {"yf": "068270.KS", "code": "068270", "name": "셀트리온",        "market": "KR", "currency": "KRW"},
    {"yf": "005490.KS", "code": "005490", "name": "POSCO홀딩스",     "market": "KR", "currency": "KRW"},
    {"yf": "035420.KS", "code": "035420", "name": "NAVER",           "market": "KR", "currency": "KRW"},
    # 미국 주요 종목 (시가총액 상위)
    {"yf": "AAPL",  "code": "AAPL",  "name": "Apple",     "market": "US", "currency": "USD"},
    {"yf": "MSFT",  "code": "MSFT",  "name": "Microsoft", "market": "US", "currency": "USD"},
    {"yf": "NVDA",  "code": "NVDA",  "name": "NVIDIA",    "market": "US", "currency": "USD"},
    {"yf": "AMZN",  "code": "AMZN",  "name": "Amazon",    "market": "US", "currency": "USD"},
    {"yf": "GOOGL", "code": "GOOGL", "name": "Alphabet",  "market": "US", "currency": "USD"},
    {"yf": "META",  "code": "META",  "name": "Meta",      "market": "US", "currency": "USD"},
    {"yf": "TSLA",  "code": "TSLA",  "name": "Tesla",     "market": "US", "currency": "USD"},
    {"yf": "AVGO",  "code": "AVGO",  "name": "Broadcom",  "market": "US", "currency": "USD"},
    {"yf": "JPM",   "code": "JPM",   "name": "JPMorgan",  "market": "US", "currency": "USD"},
    {"yf": "WMT",   "code": "WMT",   "name": "Walmart",   "market": "US", "currency": "USD"},
]

result = []
for s in STOCKS:
    try:
        ticker = yf.Ticker(s["yf"])
        fi = ticker.fast_info

        # fast_info.last_price: real-time during market hours, last close otherwise
        current    = round(float(fi.last_price), 2)
        prev_close = round(float(fi.previous_close), 2)
        change     = round(current - prev_close, 2)
        change_pct = round((change / prev_close) * 100, 2)

        # 1-year history for 52-week range + 90-day chart data
        hist = ticker.history(period="1y")
        if hist.empty:
            print(f"✗ {s['code']}: 히스토리 없음"); continue

        high_52w = round(float(hist['High'].max()), 2)
        low_52w  = round(float(hist['Low'].min()), 2)

        prices = [
            {"date": d.strftime('%Y-%m-%d'), "close": round(float(r['Close']), 2)}
            for d, r in hist.tail(90).iterrows()
        ]

        result.append({
            "code":       s["code"],
            "name":       s["name"],
            "market":     s["market"],
            "currency":   s["currency"],
            "current":    current,
            "change":     change,
            "change_pct": change_pct,
            "high_52w":   high_52w,
            "low_52w":    low_52w,
            "prices":     prices,
        })
        print(f"✓ {s['name']:12s} ({s['code']:6s})  {current:>12,.2f}  {change:+.2f} ({change_pct:+.2f}%)")
    except Exception as e:
        print(f"✗ {s['code']}: {e}")

now = datetime.now()
with open('stocks.json', 'w', encoding='utf-8') as f:
    json.dump({"updated": now.strftime('%Y-%m-%d %H:%M'), "stocks": result}, f, ensure_ascii=False, indent=2)

print(f"\n총 {len(result)}/{len(STOCKS)}개 업데이트 완료")
