import yfinance as yf
import json
from datetime import datetime

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

    # 테마 (20)
    {"yf": "SOXX", "code": "SOXX", "name": "반도체",                "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "SMH",  "code": "SMH",  "name": "반도체 (VanEck)",       "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "ARKK", "code": "ARKK", "name": "혁신 기술 (ARK)",       "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "ARKW", "code": "ARKW", "name": "차세대 인터넷 (ARK)",   "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "ARKG", "code": "ARKG", "name": "유전체 혁신 (ARK)",     "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "BOTZ", "code": "BOTZ", "name": "로보틱스·AI",           "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "AIQ",  "code": "AIQ",  "name": "AI & 빅데이터",         "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "ICLN", "code": "ICLN", "name": "청정에너지",            "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "DRIV", "code": "DRIV", "name": "전기차·자율주행",       "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "CLOU", "code": "CLOU", "name": "클라우드 컴퓨팅",       "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "IBIT", "code": "IBIT", "name": "비트코인 현물",         "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "BITO", "code": "BITO", "name": "비트코인 선물",         "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "CIBR", "code": "CIBR", "name": "사이버보안",            "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "VNQ",  "code": "VNQ",  "name": "리츠 (Vanguard)",       "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "IBB",  "code": "IBB",  "name": "바이오테크",            "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "XBI",  "code": "XBI",  "name": "바이오테크 동일가중",   "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "KWEB", "code": "KWEB", "name": "중국 인터넷",           "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "EWJ",  "code": "EWJ",  "name": "일본",                  "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "INDA", "code": "INDA", "name": "인도",                  "category": "테마",    "market": "US", "currency": "USD"},
    {"yf": "JETS", "code": "JETS", "name": "항공·여행",             "category": "테마",    "market": "US", "currency": "USD"},

    # 원자재 (10)
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

    # 레버리지·인버스 (10) — 고위험 상품
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

    # 지수 — 국내 (3)
    {"yf": "069500.KS", "code": "069500", "name": "KODEX 200",            "category": "지수",    "market": "KR", "currency": "KRW"},
    {"yf": "102110.KS", "code": "102110", "name": "TIGER 200",            "category": "지수",    "market": "KR", "currency": "KRW"},
    {"yf": "229200.KS", "code": "229200", "name": "KODEX KOSDAQ150",      "category": "지수",    "market": "KR", "currency": "KRW"},
    # 지수 — 해외 (9)
    {"yf": "360750.KS", "code": "360750", "name": "TIGER 미국S&P500",         "category": "지수",    "market": "KR", "currency": "KRW"},
    {"yf": "133690.KS", "code": "133690", "name": "TIGER 미국나스닥100",      "category": "지수",    "market": "KR", "currency": "KRW"},
    {"yf": "379800.KS", "code": "379800", "name": "KODEX 미국S&P500TR",       "category": "지수",    "market": "KR", "currency": "KRW"},
    {"yf": "195980.KS", "code": "195980", "name": "TIGER 유로STOXX50",        "category": "지수",    "market": "KR", "currency": "KRW"},
    {"yf": "241180.KS", "code": "241180", "name": "TIGER 일본니케이225",      "category": "지수",    "market": "KR", "currency": "KRW"},
    {"yf": "192090.KS", "code": "192090", "name": "TIGER 차이나CSI300",       "category": "지수",    "market": "KR", "currency": "KRW"},
    {"yf": "411060.KS", "code": "411060", "name": "ACE 미국S&P500",           "category": "지수",    "market": "KR", "currency": "KRW"},
    {"yf": "367380.KS", "code": "367380", "name": "KODEX 미국나스닥100TR",    "category": "지수",    "market": "KR", "currency": "KRW"},
    {"yf": "352560.KS", "code": "352560", "name": "TIGER 미국테크TOP10 INDXX","category": "지수",    "market": "KR", "currency": "KRW"},

    # 배당 (6)
    {"yf": "279530.KS", "code": "279530", "name": "KODEX 배당가치",            "category": "배당",    "market": "KR", "currency": "KRW"},
    {"yf": "458730.KS", "code": "458730", "name": "TIGER 미국배당다우존스",    "category": "배당",    "market": "KR", "currency": "KRW"},
    {"yf": "441680.KS", "code": "441680", "name": "KODEX 미국배당프리미엄",    "category": "배당",    "market": "KR", "currency": "KRW"},
    {"yf": "266160.KS", "code": "266160", "name": "KODEX 고배당",              "category": "배당",    "market": "KR", "currency": "KRW"},
    {"yf": "319640.KS", "code": "319640", "name": "TIGER 배당성장",            "category": "배당",    "market": "KR", "currency": "KRW"},
    {"yf": "455890.KS", "code": "455890", "name": "TIGER 미국배당+7%프리미엄", "category": "배당",    "market": "KR", "currency": "KRW"},

    # 채권 (5)
    {"yf": "114820.KS", "code": "114820", "name": "KODEX 국고채3년",           "category": "채권",    "market": "KR", "currency": "KRW"},
    {"yf": "148070.KS", "code": "148070", "name": "KOSEF 국고채10년",           "category": "채권",    "market": "KR", "currency": "KRW"},
    {"yf": "304660.KS", "code": "304660", "name": "KODEX 미국채30년선물(H)",    "category": "채권",    "market": "KR", "currency": "KRW"},
    {"yf": "453850.KS", "code": "453850", "name": "KODEX 미국채10년선물",       "category": "채권",    "market": "KR", "currency": "KRW"},

    # 섹터 (7)
    {"yf": "091160.KS", "code": "091160", "name": "KODEX 반도체",               "category": "섹터",    "market": "KR", "currency": "KRW"},
    {"yf": "396500.KS", "code": "396500", "name": "TIGER 반도체TOP10",           "category": "섹터",    "market": "KR", "currency": "KRW"},
    {"yf": "448540.KS", "code": "448540", "name": "KODEX 미국반도체MV",         "category": "섹터",    "market": "KR", "currency": "KRW"},
    {"yf": "143850.KS", "code": "143850", "name": "TIGER 미국나스닥바이오",     "category": "섹터",    "market": "KR", "currency": "KRW"},
    {"yf": "139290.KS", "code": "139290", "name": "TIGER 200 IT",               "category": "섹터",    "market": "KR", "currency": "KRW"},
    {"yf": "227550.KS", "code": "227550", "name": "TIGER 200 헬스케어",         "category": "섹터",    "market": "KR", "currency": "KRW"},
    {"yf": "091180.KS", "code": "091180", "name": "KODEX 자동차",               "category": "섹터",    "market": "KR", "currency": "KRW"},

    # 테마 (7)
    {"yf": "305720.KS", "code": "305720", "name": "KODEX 2차전지산업",          "category": "테마",    "market": "KR", "currency": "KRW"},
    {"yf": "381170.KS", "code": "381170", "name": "TIGER 미국테크TOP10",        "category": "테마",    "market": "KR", "currency": "KRW"},
    {"yf": "364980.KS", "code": "364980", "name": "TIGER 글로벌사이버보안",     "category": "테마",    "market": "KR", "currency": "KRW"},
    {"yf": "371460.KS", "code": "371460", "name": "TIGER 글로벌AI",             "category": "테마",    "market": "KR", "currency": "KRW"},
    {"yf": "334700.KS", "code": "334700", "name": "KODEX 바이오",               "category": "테마",    "market": "KR", "currency": "KRW"},

    # 원자재 (4)
    {"yf": "132030.KS", "code": "132030", "name": "KODEX 골드선물(H)",          "category": "원자재",  "market": "KR", "currency": "KRW"},
    {"yf": "130680.KS", "code": "130680", "name": "TIGER 원유선물Enhanced",     "category": "원자재",  "market": "KR", "currency": "KRW"},
    {"yf": "292050.KS", "code": "292050", "name": "TIGER 구리실물",             "category": "원자재",  "market": "KR", "currency": "KRW"},

    # 레버리지·인버스 (6)
    {"yf": "122630.KS", "code": "122630", "name": "KODEX 레버리지 2x",          "category": "레버리지","market": "KR", "currency": "KRW"},
    {"yf": "114800.KS", "code": "114800", "name": "KODEX 인버스",                "category": "레버리지","market": "KR", "currency": "KRW"},
    {"yf": "233740.KS", "code": "233740", "name": "KODEX 코스닥150 레버리지",    "category": "레버리지","market": "KR", "currency": "KRW"},
    {"yf": "252670.KS", "code": "252670", "name": "KODEX 200선물인버스2X",       "category": "레버리지","market": "KR", "currency": "KRW"},
    {"yf": "251340.KS", "code": "251340", "name": "KODEX 코스닥150 인버스",      "category": "레버리지","market": "KR", "currency": "KRW"},
    {"yf": "275980.KS", "code": "275980", "name": "TIGER 200선물레버리지",       "category": "레버리지","market": "KR", "currency": "KRW"},
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
        print(f"✓ {s['code']:8s} ({s['name']:20s})  {cur_sym}{current:>12,.2f}  {change:+.2f} ({change_pct:+.2f}%)")
    except Exception as e:
        print(f"✗ {s['code']}: {e}")

with open('etfs.json', 'w', encoding='utf-8') as f:
    json.dump({"updated": datetime.now().strftime('%Y-%m-%d %H:%M'), "etfs": result}, f, ensure_ascii=False, separators=(',', ':'))

print(f"\n총 {len(result)}/{len(ETFS)}개 업데이트 완료")
