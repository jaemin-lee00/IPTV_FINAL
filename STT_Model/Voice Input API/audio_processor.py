import time
import logging
from faster_whisper import WhisperModel

def process_audio_file(model, file_path):
    """오디오 파일 처리"""
    start_time = time.time()
    try:
        segments, info = model.transcribe(file_path, beam_size=5)
        process_time = time.time() - start_time
        
        logging.info(f"\n[{file_path}] 처리 결과:")
        logging.info(f"파일 처리 시간: {process_time:.2f}초")
        logging.info(f"감지된 언어: {info.language} (확률: {info.language_probability:.2f})")
        
        # 디버깅: segments 내용 출력
        segments = list(segments)
        
        for segment in segments:
            logging.info(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
        return segments, info
    except Exception as e:
        logging.error(f"오류 발생 ({file_path}): {str(e)}")
        return None, None