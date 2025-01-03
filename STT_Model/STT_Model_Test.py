# def transcribe_audio(model, audio_path):
#     """단일 오디오 파일을 텍스트로 변환하는 함수"""
#     try:
#         segments, info = model.transcribe(audio_path, beam_size=5)
#         return segments, info
#     except Exception as e:
#         print(f"Error processing {audio_path}: {str(e)}")
#         return None, None

# def process_audio_directory(input_dir, output_dir):
#     """디렉토리 내의 모든 오디오 파일을 처리하는 함수"""
#     # 출력 디렉토리가 없으면 생성
#     os.makedirs(output_dir, exist_ok=True)
    
#     # 지원하는 오디오 파일 확장자
#     audio_extensions = ('.wav', '.mp3', '.m4a', '.flac')
    
#     # 디렉토리 내의 모든 오디오 파일 처리
#     for filename in os.listdir(input_dir):
#         if filename.lower().endswith(audio_extensions):
#             audio_path = os.path.join(input_dir, filename)
#             output_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.txt")
            
#             print(f"\nProcessing: {filename}")
#             segments, info = transcribe_audio(model, audio_path)
            
#             if segments and info:
#                 # 결과를 텍스트 파일로 저장
#                 with open(output_path, 'w', encoding='utf-8') as f:
#                     f.write(f"File: {filename}\n")
#                     f.write(f"Detected language: {info.language} (probability: {info.language_probability:.2f})\n\n")
#                     for segment in segments:
#                         f.write(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n")
#                 print(f"Transcription saved to: {output_path}")

# if __name__ == "__main__":
#     # 입력과 출력 디렉토리 설정
#     input_directory = "test_16K.wav"
#     output_directory = "transcriptions"
    
#     try:
#         # GPU 모드로 먼저 시도
#         model = WhisperModel(model_size, device="cuda", compute_type="float16")
#     except RuntimeError as e:
#         print("\nGPU 오류 발생, 상세 에러:", str(e))
#         print("CPU 모드로 전환")
#         model = WhisperModel(model_size, device="cpu", compute_type="int8")
    
#     # 디렉토리 처리 시작
#     transcribe_audio(input_directory, output_directory)


import os
import sys
import time
import torch
import logging
from faster_whisper import WhisperModel
from pathlib import Path

def set_cuda_paths():
    venv_base = Path(sys.executable).parent.parent
    nvidia_base_path = venv_base / 'Lib' / 'site-packages' / 'nvidia'
    cuda_path = nvidia_base_path / 'cuda_runtime' / 'bin'
    cublas_path = nvidia_base_path / 'cublas' / 'bin'
    cudnn_path = nvidia_base_path / 'cudnn' / 'bin'
    paths_to_add = [str(cuda_path), str(cublas_path), str(cudnn_path)]
    env_vars = ['CUDA_PATH', 'CUDA_PATH_V12_4', 'PATH']
    
    for env_var in env_vars:
        current_value = os.environ.get(env_var, '')
        new_value = os.pathsep.join(paths_to_add + [current_value] if current_value else paths_to_add)
        os.environ[env_var] = new_value

set_cuda_paths()

# Logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("faster_whisper")

# 환경변수 설정 확인 (기존 체크 코드 확장)
cuda_home = os.environ.get('CUDA_HOME')
if cuda_home is None:
    print("CUDA_HOME이 설정되어 있지 않습니다.")
    print("CUDA_PATH를 CUDA_HOME으로 사용합니다...")
    os.environ['CUDA_HOME'] = os.environ.get('CUDA_PATH')

    '''
    설정 쿠다 홈 확인
    print("CUDA_HOME 설정됨:", os.environ['CUDA_HOME'])
    '''

# CUDA 환경 체크
print("CUDA 사용 가능:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("현재 CUDA 버전:", torch.version.cuda)
    print("사용 가능한 GPU:", torch.cuda.get_device_name(0))
else :
    # 환경변수 체크
    print("\nCUDA 관련 환경변수:")
    print("CUDA_PATH:", os.environ.get('CUDA_PATH'))
    print("CUDA_HOME:", os.environ.get('CUDA_HOME'))
    print("PATH에서 CUDA:", [p for p in os.environ['PATH'].split(';') if 'cuda' in p.lower()])

model_size = "large-v3"  # 모델 크기 변경 가능
beam_size = 5  # 빔 서치 크기 조정 가능

# Measure model loading time
logger.info("모델 로딩 시작 시간: %s", time.strftime("%Y-%m-%d %H:%M:%S"))
model_load_start_time = time.time()

try:
    # GPU 모드로 먼저 시도
    model = WhisperModel(model_size, device="cuda", compute_type="float16")
except RuntimeError as e:
    print("\nGPU 오류 발생, 상세 에러:", str(e))
    print("CPU 모드로 전환")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

model_load_end_time = time.time()
model_load_time = model_load_end_time - model_load_start_time
logger.info("모델 로딩 종료 시간: %s", time.strftime("%Y-%m-%d %H:%M:%S"))
logger.info("모델 로딩 시간: %.2f초", model_load_time)

# Measure transcription time
logger.info("음성 파일 변환 시작 시간: %s", time.strftime("%Y-%m-%d %H:%M:%S"))
transcription_start_time = time.time()

segments, info = model.transcribe("test_16K.wav", beam_size=beam_size)

transcription_end_time = time.time()
transcription_time = transcription_end_time - transcription_start_time
logger.info("음성 파일 변환 종료 시간: %s", time.strftime("%Y-%m-%d %H:%M:%S"))
logger.info("음성 파일 변환 시간: %.2f초", transcription_time)

# Print results
print("\n처리 결과:")
print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))

# Print execution times
execution_time = transcription_end_time - model_load_start_time
print("\n실행 시간 정보:")
print(f"모델 로딩 시간: {model_load_time:.2f}초")
print(f"음성 파일 변환 시간: {transcription_time:.2f}초")
print(f"총 실행 시간: {execution_time:.2f}초")
print(f"총 실행 시간: {execution_time/60:.2f}분")
print("프로그램 종료 시간:", time.strftime("%Y-%m-%d %H:%M:%S"))