import os
import torch
from faster_whisper import WhisperModel

# 환경변수 설정 확인 (기존 체크 코드 확장)
cuda_home = os.environ.get('CUDA_HOME')
if cuda_home is None:
    print("CUDA_HOME이 설정되어 있지 않습니다.")
    print("CUDA_PATH를 CUDA_HOME으로 사용합니다...")
    os.environ['CUDA_HOME'] = os.environ.get('CUDA_PATH')
    print("CUDA_HOME 설정됨:", os.environ['CUDA_HOME'])

# CUDA 환경 체크
print("CUDA 사용 가능:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("현재 CUDA 버전:", torch.version.cuda)
    print("사용 가능한 GPU:", torch.cuda.get_device_name(0))

# 환경변수 체크
print("\nCUDA 관련 환경변수:")
print("CUDA_PATH:", os.environ.get('CUDA_PATH'))
print("CUDA_HOME:", os.environ.get('CUDA_HOME'))
print("PATH에서 CUDA:", [p for p in os.environ['PATH'].split(';') if 'cuda' in p.lower()])

model_size = "large-v3"

try:
    # GPU 모드로 먼저 시도
    model = WhisperModel(model_size, device="cuda", compute_type="float16")
except RuntimeError as e:
    print("\nGPU 오류 발생, 상세 에러:", str(e))
    print("CPU 모드로 전환")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

segments, info = model.transcribe("test_16K.wav", beam_size=5)

print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))