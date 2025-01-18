import os
import time
import torch
from faster_whisper import WhisperModel
from datetime import datetime
import logging
from multiprocessing import Pool, cpu_count
import numpy as np
import re
import json

def setup_logging():
    log_dir = "Logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f'Transcription_Log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
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

def process_single_file(file_path, output_dir):
    try:
        logging.info(f"\n시작: {os.path.basename(file_path)} 처리 중...")
        device, compute_type = setup_gpu()
        
        # 모델 로딩 시간 제한
        start_time = time.time()
        model = WhisperModel("base", device=device, compute_type=compute_type)
        if time.time() - start_time > 10:  # 10초로 수정
            raise TimeoutError("모델 로딩 시간 초과 (10초)")
        
        # 음성 변환 시간 제한
        start_time = time.time()
        segments, info = model.transcribe(file_path, beam_size=5)
        if time.time() - start_time > 10:  # 10초로 수정
            raise TimeoutError("음성 변환 시간 초과 (10초)")
        
        results = []
        korean_pattern = re.compile('[가-힣]')
        
        segment_count = 0
        for segment in segments:
            if korean_pattern.search(segment.text):
                results.append({
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text
                })
                segment_count += 1
        
        # 개별 파일 결과를 즉시 저장
        result_data = {
            'file': file_path,
            'success': True,
            'segments': results,
            'processed_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        output_file = os.path.join(
            output_dir, 
            f"{os.path.splitext(os.path.basename(file_path))[0]}_result.json"
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
            
        logging.info(f"결과 저장 완료: {output_file}")
        
        return True, segment_count
        
    except Exception as e:
        logging.error(f"\n에러 발생 in {os.path.basename(file_path)}:")
        logging.error(f"에러 유형: {type(e).__name__}")
        logging.error(f"에러 메시지: {str(e)}")
        logging.error(f"스택 트레이스:", exc_info=True)
        return False, 0

def process_files(audio_files, output_dir):
    n_processes = min(4, cpu_count())
    logging.info(f"병렬 처리 프로세스 수: {n_processes}")
    
    successful = 0
    failed = 0
    
    try:
        with Pool(processes=n_processes) as pool:
            batch_size = min(len(audio_files), n_processes)  # 배치 크기 축소
            
            for i in range(0, len(audio_files), batch_size):
                batch = audio_files[i:i+batch_size]
                async_results = []
                
                # 배치 작업 제출
                for file in batch:
                    logging.info(f"작업 추가: {os.path.basename(file)}")
                    async_results.append(
                        pool.apply_async(process_single_file, (file, output_dir))
                    )
                
                # 배치 결과 수집 (타임아웃 적용)
                for idx, async_result in enumerate(async_results):
                    try:
                        success, segment_count = async_result.get(timeout=30)  # 타임아웃 30초로 증가
                        if success:
                            successful += 1
                        else:
                            failed += 1
                    except Exception as e:
                        failed += 1
                        logging.error(f"처리 실패: {str(e)}")
                    finally:
                        # 진행률 계산 및 로깅
                        completed = i + idx + 1
                        total = len(audio_files)
                        progress = (completed / total) * 100
                        logging.info(f"진행률: {completed}/{total} ({progress:.1f}%)")
                        
                        if completed >= total:
                            logging.info("모든 파일 처리 완료")
                            pool.terminate()  # 모든 작업 완료 시 풀 강제 종료
                            return successful, failed
                
                # 배치 처리 완료 후 메모리 정리
                del async_results
            
            pool.close()
            pool.join()
    
    except Exception as e:
        logging.error(f"프로세스 풀 실행 중 오류: {str(e)}")
        raise  # 오류 발생 시 상위로 전파
    
    return successful, failed

def get_project_paths():
    """프로젝트 관련 경로들을 반환"""
    # 현재 스크립트의 절대 경로
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 필요한 폴더들의 절대 경로
    paths = {
        'korean_audio': os.path.join(current_dir, "Korean_Audio"),
        'logs': os.path.join(current_dir, "Logs"),
        'output': os.path.join(current_dir, "Output")
    }
    
    # 필요한 폴더들이 없으면 생성
    for path in paths.values():
        if not os.path.exists(path):
            os.makedirs(path)
            logging.info(f"폴더 생성됨: {path}")
    
    return paths

def main():
    setup_logging()
    start_time = time.time()
    
    try:
        # 경로 설정
        paths = get_project_paths()
        korean_folder = paths['korean_audio']
        output_dir = paths['output']
        
        logging.info(f"작업 폴더 위치: {korean_folder}")
        logging.info(f"결과 저장 위치: {output_dir}")
        
        # 폴더 존재 여부 재확인
        if not os.path.exists(korean_folder):
            logging.error(f"치명적 오류: '{korean_folder}' 폴더를 찾을 수 없습니다.")
            return
        
        # 오디오 파일 목록 가져오기
        try:
            audio_files = [
                os.path.join(korean_folder, f) 
                for f in os.listdir(korean_folder)
                if f.endswith(('.wav', '.mp3'))
            ]
        except Exception as e:
            logging.error(f"폴더 읽기 오류: {str(e)}")
            return
        
        if not audio_files:
            logging.warning(f"'{korean_folder}' 폴더에 처리할 오디오 파일이 없습니다.")
            return

        logging.info(f"\n발견된 오디오 파일:")
        for file in audio_files:
            logging.info(f"- {os.path.basename(file)}")
        
        logging.info(f"\n총 {len(audio_files)}개 파일 처리 시작")
        successful, failed = process_files(audio_files, output_dir)

        # 처리 완료 후 정리
        logging.info("\n==== 처리 완료 ====")
        logging.info(f"성공: {successful}/{len(audio_files)} 파일")
        logging.info(f"실패: {failed} 파일")
        logging.info(f"총 소요 시간: {(time.time() - start_time)/60:.1f}분")
        
    except Exception as e:
        logging.error(f"치명적 오류 발생: {str(e)}")
    finally:
        logging.info("프로그램 종료")

if __name__ == "__main__":
    main()
