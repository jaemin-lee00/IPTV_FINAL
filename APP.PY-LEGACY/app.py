import os
import pickle
import joblib
import pandas as pd
import warnings
from sklearn.exceptions import InconsistentVersionWarning

warnings.filterwarnings("ignore", category=InconsistentVersionWarning)

# 현재 파일의 디렉토리 경로
current_dir = os.path.dirname(__file__)
sleep_model_path = os.path.join(current_dir, 'Sleep_model.pkl')
cardio_model_path = os.path.join(current_dir, 'Cardio_model.pkl')
diabetes_model_path = os.path.join(current_dir, 'diabetes_model.joblib')
liver_model_path = os.path.join(current_dir, 'liver_model.joblib')
lung_model_path = os.path.join(current_dir, 'lung_model.joblib')

# Sleep 모델 로드
try:
    with open(sleep_model_path, 'rb') as file:
        loaded_Sleep_RF = pickle.load(file)
    print("Model loaded successfully!")
except FileNotFoundError:
    print(f"Model file not found at {sleep_model_path}")
except Exception as e:
    print(f"An error occurred while loading the model: {e}")

# Cardio 모델 로드
try:
    with open(cardio_model_path, 'rb') as file:
        loaded_Cardio_XGB = pickle.load(file)
    print("Model loaded successfully!")
except FileNotFoundError:
    print(f"Model file not found at {cardio_model_path}")
except Exception as e:
    print(f"An error occurred while loading the model: {e}")

# diabetes 모델 로드
try:
    with open(diabetes_model_path, 'rb') as file:
        loaded_Diabetes_GBM = joblib.load(file)
    print("Model loaded successfully!")
except FileNotFoundError:
    print(f"Model file not found at {diabetes_model_path}")
except Exception as e:
    print(f"An error occurred while loading the model: {e}")

# liver 모델 로드
try:
    with open(liver_model_path, 'rb') as file:
        loaded_Liver_RF = joblib.load(file)
    print("Model loaded successfully!")
except FileNotFoundError:
    print(f"Model file not found at {liver_model_path}")
except Exception as e:
    print(f"An error occurred while loading the model: {e}")

# lung 모델 로드
try:
    with open(lung_model_path, 'rb') as file:
        loaded_Lung_LG = joblib.load(file)
    print("Model loaded successfully!")
except FileNotFoundError:
    print(f"Model file not found at {lung_model_path}")
except Exception as e:
    print(f"An error occurred while loading the model: {e}")

#######################################################################################
############################ 사용자에게 받을 데이터 예시#################################
tmdrbs = {
    'Name' : '박승균', 
    'Age': 25,
    'Gender' : 1,
    'Height' : 172,
    'Weight' : 72,
    'Alco' : 1,
    'Smoke' : 1,
    'Sleep Duration': 7.0,
    'Tired' : 1,
    'Systolic': 110,
    'Diastolic': 80,
    'Daily Steps': 8000,
    'Col': 1           # 콜레스테롤 수치 여부
}

tmdrbs_pd = pd.DataFrame([tmdrbs])
print(tmdrbs_pd)
#######################################################################################
#######################################################################################
def calculate_bmi_category(height, weight):
    bmi = weight / (height / 100) ** 2
    if bmi < 18.5:
        return 1  # 저체중
    elif 18.5 <= bmi < 25:
        return 2  # 정상
    elif 25 <= bmi < 30:
        return 3  # 과체중
    else:
        return 4  # 비만
    
# 고혈압 여부를 판단하여 'Hyper' 컬럼 추가
def calculate_hypertension(systolic, diastolic):
    if systolic >= 140 or diastolic >= 90:
        return 1  # 고혈압
    else:
        return 0  # 정상

# 'BMI Encoded' 열 추가해서 새로운 데이터 프레임에 저장
tmdrbs_pd_f = tmdrbs_pd.copy()
tmdrbs_pd_f['BMI Encoded'] = tmdrbs_pd_f.apply(lambda row: calculate_bmi_category(row['Height'], row['Weight']), axis=1)
tmdrbs_pd_f['Hyper'] = tmdrbs_pd_f.apply(lambda row: calculate_hypertension(row['Systolic'], row['Diastolic']), axis=1)


cols_sleep = ['BMI Encoded','Age','Sleep Duration','Systolic','Diastolic','Daily Steps']
# BMI Encoded : 1 (저체중), 2(정상체중), 3(과체중), 4(비만)
tmdrbs_sleep = tmdrbs_pd_f[cols_sleep]
# 예측
try:
    sleep_predictions = loaded_Sleep_RF.predict(tmdrbs_sleep)
    if sleep_predictions == 1:
        print('수면장애 위험군입니다.')
    else:
        print('수면장애 위험군이 아닙니다.')
except Exception as e:
    print(f"An error occurred during prediction: {e}")

#####################################################################
#####################################################################
cols_cardio = ['Systolic','Diastolic','Age','Weight']
tmdrbs_cardio = tmdrbs_pd_f[cols_cardio]
# 예측
try:
    cardio_predictions = loaded_Cardio_XGB.predict(tmdrbs_cardio)
    if cardio_predictions == 1:
        print('심혈관질환 위험군입니다.')
    else:
        print('심혈관질환 위험군이 아닙니다.')
except Exception as e:
    print(f"An error occurred during prediction: {e}")

######################################################################
cols_diabetes = ["Gender", "Age", "Hyper", "BMI Encoded", "Smoke", "Col", "Alco"]
tmdrbs_diabetes = tmdrbs_pd_f[cols_diabetes]
# 예측
try:
    diabetes_predictions = loaded_Diabetes_GBM.predict(tmdrbs_diabetes)
    if diabetes_predictions == 1:
        print('당뇨 위험군입니다.')
    else:
        print('당뇨 위험군이 아닙니다.')
except Exception as e:
    print(f"An error occurred during prediction: {e}")

######################################################################
cols_liver = ['Age', 'Gender', 'BMI Encoded', 'Alco', 'Smoke', 'Daily Steps', 'Hyper']
tmdrbs_liver = tmdrbs_pd_f[cols_liver]
# 예측
try:
    liver_predictions = loaded_Liver_RF.predict(tmdrbs_liver)
    if cardio_predictions == 1:
        print('간암 위험군입니다.')
    else:
        print('간암 위험군이 아닙니다.')
except Exception as e:
    print(f"An error occurred during prediction: {e}")

######################################################################
cols_lung = ['Gender', 'Age', 'Smoke', 'Tired', 'Alco']
tmdrbs_lung = tmdrbs_pd_f[cols_lung]
# 예측
try:
    lung_predictions = loaded_Lung_LG.predict(tmdrbs_lung)
    if lung_predictions == 1:
        print('폐암 위험군입니다.')
    else:
        print('폐암 위험군이 아닙니다.')
except Exception as e:
    print(f"An error occurred during prediction: {e}")










