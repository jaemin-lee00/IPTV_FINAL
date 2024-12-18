import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# 한글 폰트 설정
from matplotlib import font_manager, rc
import platform

if platform.system() == 'Windows':
    font_name = font_manager.FontProperties(fname="c:/Windows/Fonts/malgun.ttf").get_name()
    rc('font', family=font_name)
elif platform.system() == 'Darwin':  # MacOS
    rc('font', family='AppleGothic')
else:
    print('Unknown system, unable to set Korean font.')

plt.rcParams['axes.unicode_minus'] = False

# 현재 폴더 내의 모든 CSV 파일 목록
csv_files = [file for file in os.listdir() if file.endswith('.csv')]

# 현재 폴더 내의 xls 파일 목록
xls_files = [file for file in os.listdir() if file.endswith('.xlsx')]

# 주제별 목표 평균값 및 표준편차 설정
target_params = {}
for xls_file in xls_files:
    xls_df = pd.read_excel(xls_file)  # 인코딩 설정 제거
    for index, row in xls_df.iterrows():
        mlsfc = row.iloc[0]  # 첫 번째 컬럼 값 가져오기
        target_params[mlsfc] = {
            '100Hz': {'mean': row.iloc[1], 'std_dev': row.iloc[1] * 0.1},
            '300Hz': {'mean': row.iloc[2], 'std_dev': row.iloc[2] * 0.1},
            '1kHz': {'mean': row.iloc[3], 'std_dev': row.iloc[3] * 0.1},
            '3kHz': {'mean': row.iloc[4], 'std_dev': row.iloc[4] * 0.1},
            '10kHz': {'mean': row.iloc[5], 'std_dev': row.iloc[5] * 0.1}
        }

# A 열의 모든 값을 출력
for xls_file in xls_files:
    xls_df = pd.read_excel(xls_file)  # 인코딩 설정 제거
    a_column_values = xls_df.iloc[:, 0]  # A 열의 모든 값 가져오기
    print(f'Values in column A of {xls_file}:')
    print(a_column_values)

# 색깔 목록
colors = ['blue', 'green', 'red', 'cyan', 'magenta', 'yellow', 'black']

# output 폴더가 없으면 생성
output_dir = 'output'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 히스토그램 데이터와 제목을 저장할 리스트 초기화
hist_data = []
titles = []

# 각 CSV 파일에 대해 동일한 과정 수행
for file in csv_files:
    # CSV 파일을 DataFrame으로 로드
    df = pd.read_csv(file, encoding='cp949')  # 인코딩 설정
    
    # 전체 데이터 갯수 출력
    total_rows = len(df)
    print(f'Total rows in {file}: {total_rows}')
    
    # 전체 데이터 중 20%를 랜덤 데이터로 설정
    num_random = int(total_rows * 0.2)
    random_indices = np.random.choice(df.index, size=num_random, replace=False)
    
    # 각 주제에 대해 데이터 생성
    for i, (mlsfc, params) in enumerate(target_params.items()):
        # 해당 주제에 해당하는 데이터 필터링
        mask = (df['GNR_MLSFC_NM'] == mlsfc)
        num_rows = mask.sum()
        
        # 필터링된 데이터 갯수 출력
        print(f'Filtered rows for {mlsfc} in {file}: {num_rows}')
        
        if num_rows > 0:
            freq_data = {} 
            for j, (freq, stats) in enumerate(params.items()):
                # 랜덤 데이터 생성
                random_data = np.random.normal(stats['mean'], stats['std_dev'], size=num_random).astype(int)
                random_data = random_data[random_data <= 100]  # Truncate data to ensure values are less than 100
                while len(random_data) < num_random:  # Ensure we have enough data points
                    additional_data = np.random.normal(stats['mean'], stats['std_dev'], size=num_random - len(random_data)).astype(int)
                    additional_data = additional_data[additional_data <= 100]
                    random_data = np.concatenate([random_data, additional_data])
                
                # 노말 데이터 생성
                normal_data = np.full(total_rows, 50)
                
                # 랜덤 데이터 할당
                normal_data[random_indices] = random_data[:num_random]
                
                df[freq] = normal_data  # Assign the combined data to the DataFrame
                
                freq_data[freq] = df[freq]  # 각 주파수별 데이터를 저장
            
            # 히스토그램 데이터를 저장
            hist_data.append((freq_data, mlsfc, file))
            titles.append(f'{mlsfc}의 분포 ({file})')
    
    # 업데이트된 DataFrame을 CSV 파일로 저장
    base_name = os.path.splitext(file)[0]
    new_file_name = os.path.join(output_dir, f'{base_name}-더미.csv')
    df.to_csv(new_file_name, index=False, float_format='%.0f')  # Save as integers
    
    # 결과 파일을 output 폴더 내의 output.csv 파일에 추가
    output_file_path = os.path.join(output_dir, 'output.csv')
    with open(output_file_path, 'a', encoding='cp949') as f:  # 인코딩 설정
        df.to_csv(f, header=f.tell()==0, index=False, float_format='%.0f')  # Save as integers

# 그래프 초기화
fig, ax = plt.subplots()
index = 0

def update_plot(index):
    ax.clear()
    freq_data, mlsfc, file = hist_data[index]
    for j, (freq, data) in enumerate(freq_data.items()):
        # 노말 데이터(값이 50인 데이터)를 제외하고 히스토그램 생성
        filtered_data = data[data != 50]
        ax.hist(filtered_data, bins=20, edgecolor='black', alpha=0.5, color=colors[j % len(colors)], label=f'{freq}')
    ax.set_title(titles[index])
    ax.set_xlabel('값')
    ax.set_ylabel('빈도수')
    ax.legend()
    fig.canvas.draw()

def on_key(event):
    global index
    if event.key == 'right':
        index = (index + 1) % len(hist_data)
        update_plot(index)
    elif event.key == 'left':
        index = (index - 1) % len(hist_data)
        update_plot(index)

fig.canvas.mpl_connect('key_press_event', on_key)
update_plot(index)
plt.show()

# ...existing code...