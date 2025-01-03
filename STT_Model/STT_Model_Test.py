import os
import time
import torch
from faster_whisper import WhisperModel
from datetime import datetime
import logging

def setup_logging():
    """로깅 설정"""
    log_dir = "Logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f'STT_Log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def setup_gpu():
    """GPU 사용 가능 여부 확인 및 설정"""
    if torch.cuda.is_available():
        logging.info(f"GPU 사용 가능: {torch.cuda.get_device_name(0)}")
        return "cuda", "float16"
    else:
        logging.info("GPU 사용 불가능 - CPU 모드로 실행")
        return "cpu", "int8"

def load_model():
    """모델 로딩"""
    start_time = time.time()
    device, compute_type = setup_gpu()
    model = WhisperModel("large-v3", device=device, compute_type=compute_type)
    load_time = time.time() - start_time
    logging.info(f"모델 로딩 완료 (소요 시간: {load_time:.2f}초)")
    return model

def process_audio_file(model, file_path):
    """오디오 파일 처리"""
    start_time = time.time()
    try:
        segments, info = model.transcribe(file_path, beam_size=5)
        process_time = time.time() - start_time
        
        logging.info(f"\n[{file_path}] 처리 결과:")
        logging.info(f"파일 처리 시간: {process_time:.2f}초")
        logging.info(f"감지된 언어: {info.language} (확률: {info.language_probability:.2f})")
        
        for segment in segments:
            logging.info(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
        return True
    except Exception as e:
        logging.error(f"오류 발생 ({file_path}): {str(e)}")
        return False

def find_audio_files(folder):
    """오디오 파일 검색"""
    audio_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(folder)
        for file in files
        if file.endswith(('.wav', '.mp3'))
    ]
    return audio_files

def process_files(model, audio_files):
    """파일 일괄 처리"""
    successful = 0
    for file in audio_files:
        if process_audio_file(model, file):
            successful += 1
    return successful

def main():
    setup_logging()
    start_time = time.time()
    
    # 모델 로딩
    logging.info("모델 로딩 시작...")
    model = load_model()
    
    # 오디오 파일 찾기
    audio_folder = "Audio"
    audio_files = find_audio_files(audio_folder)
    
    if not audio_files:
        logging.warning(f"'{audio_folder}' 폴더에서 오디오 파일을 찾을 수 없습니다.")
        return
    
    # 파일 처리
    logging.info(f"\n총 {len(audio_files)}개 파일 처리 시작")
    successful = process_files(model, audio_files)
    
    # 결과 출력
    total_time = time.time() - start_time
    logging.info(f"\n처리 완료:")
    logging.info(f"성공: {successful}/{len(audio_files)} 파일")
    logging.info(f"총 소요 시간: {total_time/60:.1f}분 ({total_time:.1f}초)")

if __name__ == "__main__":
    main()