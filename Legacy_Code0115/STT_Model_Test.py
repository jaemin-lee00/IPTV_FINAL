import os
import time
import torch
from faster_whisper import WhisperModel
from datetime import datetime
import logging
from multiprocessing import Pool, cpu_count
import numpy as np
import re

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
    model = WhisperModel("base", device=device, compute_type=compute_type)
    load_time = time.time() - start_time
    logging.info(f"모델 로딩 완료 (소요 시간: {load_time:.2f}초)")
    return model

def process_single_file(file_path):
    """단일 파일 처리 (각 프로세스에서 실행)"""
    try:
        device, compute_type = setup_gpu()
        model = WhisperModel("base", device=device, compute_type=compute_type)
        
        segments, info = model.transcribe(file_path, beam_size=5)
        
        # 한국어가 아닌 경우 처리 중단
        if info.language != 'ko':
            return {
                'file': file_path,
                'success': False,
                'error': f"지원하지 않는 언어 감지: {info.language} (확률: {info.language_probability:.2f})"
            }
        
        results = []
        korean_pattern = re.compile('[가-힣]')  # 한글 문자 패턴
        
        for segment in segments:
            # 한글이 포함된 세그먼트만 저장
            if korean_pattern.search(segment.text):
                results.append({
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text
                })
        
        if not results:
            return {
                'file': file_path,
                'success': False,
                'error': "한국어 텍스트가 감지되지 않았습니다."
            }
        
        return {
            'file': file_path,
            'success': True,
            'language': info.language,
            'language_probability': info.language_probability,
            'segments': results
        }
    except Exception as e:
        return {
            'file': file_path,
            'success': False,
            'error': f"파일 처리 중 오류 발생: {str(e)}"
        }

def find_audio_files(folder):
    """오디오 파일 검색"""
    audio_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(folder)
        for file in files
        if file.endswith(('.wav', '.mp3'))
    ]
    return audio_files

def detect_language(model, file_path):
    """파일의 언어 감지"""
    try:
        segments, info = model.transcribe(file_path, beam_size=5)
        return {
            'file': file_path,
            'is_korean': info.language == 'ko',
            'language': info.language,
            'probability': info.language_probability
        }
    except Exception as e:
        return {
            'file': file_path,
            'is_korean': False,
            'error': str(e)
        }

def process_files(audio_files):
    """파일 병렬 처리"""
    n_processes = min(4, cpu_count())
    logging.info(f"병렬 처리 프로세스 수: {n_processes}")
    
    # 언어 감지를 위한 모델 로드
    device, compute_type = setup_gpu()
    model = WhisperModel("base", device=device, compute_type=compute_type)
    
    # 먼저 한국어 파일 필터링
    logging.info("\n한국어 파일 필터링 시작...")
    korean_files = []
    non_korean_files = []
    
    for file in audio_files:
        result = detect_language(model, file)
        if result['is_korean']:
            korean_files.append(file)
            logging.info(f"한국어 파일 감지: {os.path.basename(file)}")
        else:
            non_korean_files.append({
                'file': file,
                'language': result.get('language', 'unknown'),
                'probability': result.get('probability', 0)
            })
            logging.info(f"비한국어 파일 제외: {os.path.basename(file)}")
    
    logging.info(f"\n총 {len(audio_files)}개 중 한국어 파일: {len(korean_files)}개")
    logging.info(f"비한국어 파일: {len(non_korean_files)}개")
    
    if not korean_files:
        logging.warning("처리할 한국어 파일이 없습니다.")
        return 0
    
    successful = 0
    failed = 0
    error_files = []
    
    try:
        with Pool(processes=n_processes) as pool:
            results = []
            for batch in np.array_split(korean_files, n_processes):
                for file in batch:
                    results.append(pool.apply_async(process_single_file, (file,)))
            
            # 결과 수집
            for result in results:
                try:
                    data = result.get(timeout=300)
                    if data['success'] and len(data['segments']) > 0:
                        successful += 1
                        logging.info(f"\n[변환 성공] 파일: {os.path.basename(data['file'])}")
                        logging.info("="*50)
                        logging.info("한국어 음성-텍스트 변환 결과:")
                        for segment in data['segments']:
                            logging.info(f"[{segment['start']:.1f}초 ~ {segment['end']:.1f}초] {segment['text']}")
                        logging.info("="*50)
                    else:
                        failed += 1
                        error_files.append({
                            'file': os.path.basename(data['file']),
                            'error': data.get('error', '한국어 텍스트 없음')
                        })
                        logging.error(f"[실패] 파일: {os.path.basename(data['file'])} - {data.get('error', '한국어 텍스트 없음')}")
                        
                except Exception as e:
                    failed += 1
                    error_files.append({
                        'file': 'Unknown',
                        'error': str(e)
                    })
                    logging.error(f"처리 중 예외 발생: {str(e)}")
            
            pool.close()
            pool.join()
            
    except Exception as e:
        logging.error(f"프로세스 풀 실행 중 치명적 오류: {str(e)}")
    finally:
        # 요약 통계
        logging.info("\n" + "="*50)
        logging.info("처리 완료 요약")
        logging.info("="*50)
        logging.info(f"총 처리된 한국어 파일: {len(korean_files)}개")
        logging.info(f"변환 성공: {successful}개")
        logging.info(f"변환 실패: {failed}개")
        logging.info("="*50)
    
    return successful

def main():
    setup_logging()
    start_time = time.time()
    
    # 오디오 파일 찾기
    audio_folder = "Audio"
    audio_files = find_audio_files(audio_folder)
    
    if not audio_files:
        logging.warning(f"'{audio_folder}' 폴더에서 오디오 파일을 찾을 수 없습니다.")
        return
    
    # 파일 처리
    logging.info(f"\n총 {len(audio_files)}개 파일 처리 시작")
    successful = process_files(audio_files)
    
    # 결과 출력
    total_time = time.time() - start_time
    logging.info(f"\n처리 완료:")
    logging.info(f"성공: {successful}/{len(audio_files)} 파일")
    logging.info(f"총 소요 시간: {total_time/60:.1f}분 ({total_time:.1f}초)")

if __name__ == "__main__":
    main()