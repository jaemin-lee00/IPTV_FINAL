import pymysql
import pandas as pd

# MySQL 연결 설정
conn = pymysql.connect(
    host='192.168.101.227',
    user='Second',
    password='rkdwlsah12!*',
    database='second_pj',
    port=3306
)

# SQL 쿼리 작성
query = """
SELECT BDCT_TYPE_CLS, GNR_MLSFC_NM, AVG_WTCH_HR_MIN, Hz_100, Hz_300, Hz_1k, Hz_3k, Hz_10k
FROM watched_data
WHERE BDCT_TYPE_CLS = 'VOD'
ORDER BY CRTR_YM DESC;
"""

# 데이터 가져오기
try:
    df = pd.read_sql(query, conn)
    if df.empty:
        print("No data found for the last 3 months.")
    else:
        print("Data fetched successfully:")
        print(df.head())
finally:
    conn.close()

print(df.head())

def weighted_mean(df, value_col, weight_col):
    """가중평균 계산 함수"""
    weighted_sum = (df[value_col] * df[weight_col]).sum()
    total_weight = df[weight_col].sum()
    return weighted_sum / total_weight if total_weight != 0 else 0

def process_data(data):
    results = []
    for category, group in data.groupby('GNR_MLSFC_NM'):
        weighted_averages = {}
        
        # 각 컬럼별로 이상치를 계산 및 제거
        for col in ['Hz_100', 'Hz_300', 'Hz_1k', 'Hz_3k', 'Hz_10k']:
            Q1 = group[col].quantile(0.25)
            Q3 = group[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 2.5 * IQR
            upper_bound = Q3 + 2.5 * IQR
            
            # 해당 컬럼의 이상치 제거
            filtered_group = group[(group[col] >= lower_bound) & (group[col] <= upper_bound)]
            
            # 가중평균 계산
            weighted_averages[col] = weighted_mean(filtered_group, col, 'AVG_WTCH_HR_MIN')
        
        # 결과 저장
        results.append({'GNR_MLSFC_NM': category, **weighted_averages})
    
    # 결과를 DataFrame으로 반환
    return pd.DataFrame(results)
processed_data = process_data(df)

# 결과 확인
print(processed_data)