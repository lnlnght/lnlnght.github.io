import FinanceDataReader as fdr
import json

try:
    # 코스피, 코스닥 전체 종목 리스트 가져오기
    df_kospi = fdr.StockListing('KOSPI')
    df_kosdaq = fdr.StockListing('KOSDAQ')
    
    # 이름과 코드만 추출하여 딕셔너리로 변환
    symbols = {}
    for _, row in df_kospi.iterrows():
        symbols[row['Name']] = row['Code']
    for _, row in df_kosdaq.iterrows():
        symbols[row['Name']] = row['Code']

    with open('symbols.json', 'w', encoding='utf-8') as f:
        json.dump(symbols, f, ensure_ascii=False, indent=4)
    print(f"총 {len(symbols)}개 종목 코드 저장 완료!")

except Exception as e:
    print(f"에러: {e}")
    exit(1)
