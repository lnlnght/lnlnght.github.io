import FinanceDataReader as fdr
import json
from datetime import datetime, timedelta

STOCKS = [
    # 국내 주요 종목 (시가총액 상위)
    {"code": "005930", "name": "삼성전자",        "market": "KR", "currency": "KRW"},
    {"code": "000660", "name": "SK하이닉스",      "market": "KR", "currency": "KRW"},
    {"code": "373220", "name": "LG에너지솔루션",  "market": "KR", "currency": "KRW"},
    {"code": "207940", "name": "삼성바이오로직스","market": "KR", "currency": "KRW"},
    {"code": "005380", "name": "현대차",          "market": "KR", "currency": "KRW"},
    {"code": "000270", "name": "기아",            "market": "KR", "currency": "KRW"},
    {"code": "105560", "name": "KB금융",          "market": "KR", "currency": "KRW"},
    {"code": "068270", "name": "셀트리온",        "market": "KR", "currency": "KRW"},
    {"code": "005490", "name": "POSCO홀딩스",     "market": "KR", "currency": "KRW"},
    {"code": "035420", "name": "NAVER",           "market": "KR", "currency": "KRW"},
    # 미국 주요 종목 (시가총액 상위)
    {"code": "AAPL",   "name": "Apple",           "market": "US", "currency": "USD"},
    {"code": "MSFT",   "name": "Microsoft",       "market": "US", "currency": "USD"},
    {"code": "NVDA",   "name": "NVIDIA",          "market": "US", "currency": "USD"},
    {"code": "AMZN",   "name": "Amazon",          "market": "US", "currency": "USD"},
    {"code": "GOOGL",  "name": "Alphabet",        "market": "US", "currency": "USD"},
    {"code": "META",   "name": "Meta",            "market": "US", "currency": "USD"},
    {"code": "TSLA",   "name": "Tesla",           "market": "US", "currency": "USD"},
    {"code": "AVGO",   "name": "Broadcom",        "market": "US", "currency": "USD"},
    {"code": "JPM",    "name": "JPMorgan",        "market": "US", "currency": "USD"},
    {"code": "WMT",    "name": "Walmart",         "market": "US", "currency": "USD"},
]

end   = datetime.now()
start = end - timedelta(days=400)

result = []
for s in STOCKS:
    try:
        df = fdr.DataReader(s["code"], start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
        if df.empty:
            print(f"✗ {s['code']}: 데이터 없음"); continue

        prices = [
            {"date": d.strftime('%Y-%m-%d'), "close": round(float(r['Close']), 2)}
            for d, r in df.tail(90).iterrows()
        ]
        current    = round(float(df['Close'].iloc[-1]), 2)
        prev_close = round(float(df['Close'].iloc[-2]), 2)
        change     = round(current - prev_close, 2)
        change_pct = round((change / prev_close) * 100, 2)
        high_52w   = round(float(df['Close'].tail(252).max()), 2)
        low_52w    = round(float(df['Close'].tail(252).min()), 2)

        result.append({**s, "current": current, "change": change, "change_pct": change_pct,
                        "high_52w": high_52w, "low_52w": low_52w, "prices": prices})
        print(f"✓ {s['name']:12s} ({s['code']:6s})  {current:>12,.2f}  {change:+.2f} ({change_pct:+.2f}%)")
    except Exception as e:
        print(f"✗ {s['code']}: {e}")

with open('stocks.json', 'w', encoding='utf-8') as f:
    json.dump({"updated": end.strftime('%Y-%m-%d %H:%M'), "stocks": result}, f, ensure_ascii=False, indent=2)

print(f"\n총 {len(result)}/{len(STOCKS)}개 업데이트 완료")
