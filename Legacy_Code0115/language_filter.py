import os
import time
import torch
from faster_whisper import WhisperModel
from datetime import datetime
import logging
import json

def setup_logging():
    log_dir = "Logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f'Language_Filter_Log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def setup_gpu():
    if torch.cuda.is_available():
        logging.info(f"GPU 사용 가능: {torch.cuda.get_device_name(0)}")
        return "cuda", "float16"
    else:
        logging.info("GPU 사용 불가능 - CPU 모드로 실행")
        return "cpu", "int8"

def find_audio_files(folder):
    audio_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(folder)
        for file in files
        if file.endswith(('.wav', '.mp3'))
    ]
    return audio_files

def detect_language(model, file_path):
    try:
        segments, info = model.transcribe(file_path, beam_size=5)
        return {
            'file': file_path,
            'is_korean': info.language == 'ko',
            'language': info.language,
            'probability': float(info.language_probability)
        }
    except Exception as e:
        return {
            'file': file_path,
            'is_korean': False,
            'error': str(e)
        }

def main():
    setup_logging()
    start_time = time.time()

    # 작업 디렉토리 설정
    audio_folder = "Audio"
    korean_folder = "Korean_Audio"
    os.makedirs(korean_folder, exist_ok=True)

    # 오디오 파일 찾기
    audio_files = find_audio_files(audio_folder)
    if not audio_files:
        logging.warning(f"'{audio_folder}' 폴더에서 오디오 파일을 찾을 수 없습니다.")
        return

    # 모델 로드
    device, compute_type = setup_gpu()
    model = WhisperModel("base", device=device, compute_type=compute_type)

    # 언어 감지 및 파일 분류
    korean_files = []
    non_korean_files = []

    for file in audio_files:
        result = detect_language(model, file)
        if result['is_korean']:
            korean_files.append(result)
            # 한국어 파일 복사
            new_path = os.path.join(korean_folder, os.path.basename(file))
            os.system(f'copy "{file}" "{new_path}"')
            logging.info(f"한국어 파일 감지 및 복사: {os.path.basename(file)}")
        else:
            non_korean_files.append(result)
            logging.info(f"비한국어 파일 제외: {os.path.basename(file)}")

    # 결과 저장
    results = {
        'korean_files': korean_files,
        'non_korean_files': non_korean_files,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    with open('language_detection_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 요약 출력
    logging.info("\n" + "="*50)
    logging.info("처리 완료 요약")
    logging.info("="*50)
    logging.info(f"총 파일 수: {len(audio_files)}개")
    logging.info(f"한국어 파일: {len(korean_files)}개")
    logging.info(f"비한국어 파일: {len(non_korean_files)}개")
    logging.info(f"총 소요 시간: {(time.time() - start_time)/60:.1f}분")
    logging.info("="*50)

if __name__ == "__main__":
    main()
