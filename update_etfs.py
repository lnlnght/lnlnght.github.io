import yfinance as yf
import json
from datetime import datetime

ETFS = [
    # === 미국 ETF ===
    # 지수
    {"yf": "SPY",       "code": "SPY",    "name": "S&P 500",           "category": "지수",   "market": "US", "currency": "USD"},
    {"yf": "QQQ",       "code": "QQQ",    "name": "NASDAQ 100",         "category": "지수",   "market": "US", "currency": "USD"},
    {"yf": "VTI",       "code": "VTI",    "name": "미국 전체 시장",     "category": "지수",   "market": "US", "currency": "USD"},
    {"yf": "IWM",       "code": "IWM",    "name": "러셀 2000",           "category": "지수",   "market": "US", "currency": "USD"},
    # 배당
    {"yf": "SCHD",      "code": "SCHD",   "name": "배당 성장",           "category": "배당",   "market": "US", "currency": "USD"},
    {"yf": "VYM",       "code": "VYM",    "name": "고배당",              "category": "배당",   "market": "US", "currency": "USD"},
    {"yf": "JEPI",      "code": "JEPI",   "name": "커버드콜 배당",       "category": "배당",   "market": "US", "currency": "USD"},
    # 채권
    {"yf": "TLT",       "code": "TLT",    "name": "장기 국채 20Y+",     "category": "채권",   "market": "US", "currency": "USD"},
    {"yf": "AGG",       "code": "AGG",    "name": "종합 채권",           "category": "채권",   "market": "US", "currency": "USD"},
    {"yf": "HYG",       "code": "HYG",    "name": "하이일드 채권",       "category": "채권",   "market": "US", "currency": "USD"},
    # 섹터
    {"yf": "XLK",       "code": "XLK",    "name": "기술 섹터",           "category": "섹터",   "market": "US", "currency": "USD"},
    {"yf": "XLE",       "code": "XLE",    "name": "에너지 섹터",         "category": "섹터",   "market": "US", "currency": "USD"},
    {"yf": "XLF",       "code": "XLF",    "name": "금융 섹터",           "category": "섹터",   "market": "US", "currency": "USD"},
    {"yf": "XLV",       "code": "XLV",    "name": "헬스케어 섹터",       "category": "섹터",   "market": "US", "currency": "USD"},
    # 테마
    {"yf": "SOXX",      "code": "SOXX",   "name": "반도체",              "category": "테마",   "market": "US", "currency": "USD"},
    {"yf": "ARKK",      "code": "ARKK",   "name": "혁신 기술",           "category": "테마",   "market": "US", "currency": "USD"},
    {"yf": "BOTZ",      "code": "BOTZ",   "name": "로보틱스·AI",         "category": "테마",   "market": "US", "currency": "USD"},
    # 원자재
    {"yf": "GLD",       "code": "GLD",    "name": "금",                  "category": "원자재", "market": "US", "currency": "USD"},
    {"yf": "SLV",       "code": "SLV",    "name": "은",                  "category": "원자재", "market": "US", "currency": "USD"},
    {"yf": "USO",       "code": "USO",    "name": "원유",                "category": "원자재", "market": "US", "currency": "USD"},

    # === 한국 ETF (Yahoo Finance .KS suffix) ===
    # 지수
    {"yf": "069500.KS", "code": "069500", "name": "KODEX 200",           "category": "지수",   "market": "KR", "currency": "KRW"},
    {"yf": "229200.KS", "code": "229200", "name": "KODEX KOSDAQ150",     "category": "지수",   "market": "KR", "currency": "KRW"},
    {"yf": "360750.KS", "code": "360750", "name": "TIGER 미국S&P500",    "category": "지수",   "market": "KR", "currency": "KRW"},
    {"yf": "133690.KS", "code": "133690", "name": "TIGER 미국나스닥100", "category": "지수",   "market": "KR", "currency": "KRW"},
    # 섹터/테마
    {"yf": "091160.KS", "code": "091160", "name": "KODEX 반도체",         "category": "섹터",   "market": "KR", "currency": "KRW"},
    {"yf": "305720.KS", "code": "305720", "name": "KODEX 2차전지산업",    "category": "테마",   "market": "KR", "currency": "KRW"},
    # 배당
    {"yf": "279530.KS", "code": "279530", "name": "KODEX 배당가치",       "category": "배당",   "market": "KR", "currency": "KRW"},
    # 채권
    {"yf": "114820.KS", "code": "114820", "name": "KODEX 국고채3년",      "category": "채권",   "market": "KR", "currency": "KRW"},
]

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

        prices = [
            {"date": str(d.date()), "close": round(float(r['Close']), 2)}
            for d, r in hist.iterrows()
        ]

        try:
            expense_ratio = float(info.get('annualReportExpenseRatio') or info.get('expenseRatio') or 0)
        except (TypeError, ValueError):
            expense_ratio = 0

        try:
            dividend_yield = float(info.get('yield') or info.get('trailingAnnualDividendYield') or 0)
        except (TypeError, ValueError):
            dividend_yield = 0

        try:
            total_assets = int(info.get('totalAssets') or 0)
        except (TypeError, ValueError):
            total_assets = 0

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
            "prices":         prices,
        })
        cur_sym = "₩" if s["currency"] == "KRW" else "$"
        print(f"✓ {s['code']:8s} ({s['name']:14s})  {cur_sym}{current:>12,.2f}  {change:+.2f} ({change_pct:+.2f}%)")
    except Exception as e:
        print(f"✗ {s['code']}: {e}")

with open('etfs.json', 'w', encoding='utf-8') as f:
    json.dump({"updated": datetime.now().strftime('%Y-%m-%d %H:%M'), "etfs": result}, f, ensure_ascii=False, indent=2)

print(f"\n총 {len(result)}/{len(ETFS)}개 업데이트 완료")
