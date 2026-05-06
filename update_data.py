import FinanceDataReader as fdr
import json
import os
from datetime import datetime, timedelta
print("데이터 업데이트 시작!")
# 1. 데이터 수집 (삼성전자 예시)
end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
df = fdr.DataReader('005930', start_date, end_date)

# 2. JSON 형태로 가공
stock_data = []
for date, row in df.iterrows():
    stock_data.append({
        "date": date.strftime('%Y-%m-%d'),
        "close": int(row['Close'])
    })

# 3. 파일로 저장
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(stock_data, f, ensure_ascii=False, indent=4)

print("데이터 업데이트 완료!")
