import yfinance as yf
import json
from datetime import datetime

ETFS = [
    # 지수
    {"code": "SPY",  "name": "S&P 500",          "category": "지수"},
    {"code": "QQQ",  "name": "NASDAQ 100",        "category": "지수"},
    {"code": "VTI",  "name": "미국 전체 시장",    "category": "지수"},
    {"code": "IWM",  "name": "러셀 2000",          "category": "지수"},
    # 배당
    {"code": "SCHD", "name": "배당 성장",          "category": "배당"},
    {"code": "VYM",  "name": "고배당",             "category": "배당"},
    {"code": "JEPI", "name": "커버드콜 배당",      "category": "배당"},
    # 채권
    {"code": "TLT",  "name": "장기 국채 20Y+",    "category": "채권"},
    {"code": "AGG",  "name": "종합 채권",          "category": "채권"},
    {"code": "HYG",  "name": "하이일드 채권",      "category": "채권"},
    # 섹터
    {"code": "XLK",  "name": "기술 섹터",          "category": "섹터"},
    {"code": "XLE",  "name": "에너지 섹터",        "category": "섹터"},
    {"code": "XLF",  "name": "금융 섹터",          "category": "섹터"},
    {"code": "XLV",  "name": "헬스케어 섹터",      "category": "섹터"},
    # 테마
    {"code": "SOXX", "name": "반도체",             "category": "테마"},
    {"code": "ARKK", "name": "혁신 기술",          "category": "테마"},
    {"code": "BOTZ", "name": "로보틱스·AI",        "category": "테마"},
    # 원자재
    {"code": "GLD",  "name": "금",                 "category": "원자재"},
    {"code": "SLV",  "name": "은",                 "category": "원자재"},
    {"code": "USO",  "name": "원유",               "category": "원자재"},
]

result = []
for s in ETFS:
    try:
        ticker = yf.Ticker(s["code"])
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
        print(f"✓ {s['code']:5s} ({s['name']:12s})  ${current:>8,.2f}  {change:+.2f} ({change_pct:+.2f}%)")
    except Exception as e:
        print(f"✗ {s['code']}: {e}")

with open('etfs.json', 'w', encoding='utf-8') as f:
    json.dump({"updated": datetime.now().strftime('%Y-%m-%d %H:%M'), "etfs": result}, f, ensure_ascii=False, indent=2)

print(f"\n총 {len(result)}/{len(ETFS)}개 업데이트 완료")
