import time
import logging
from logging_setup import setup_logging
from model_loader import load_model
from audio_recorder import record_audio
from audio_processor import process_audio_file
from qa_processor import KoreanQAProcessor

Target_Seconds = 5

def main():
    setup_logging()
    start_time = time.time()
    
    logging.info("모델 로딩 시작...")
    model = load_model()
    
    audio_filename = record_audio(seconds=Target_Seconds)

    segments, info = process_audio_file(model, audio_filename)
    if segments is None:
        logging.error("STT 변환 실패")
        return
    

    transcribed_text = " ".join([segment.text for segment in segments])
    logging.info(f"변환된 텍스트: {transcribed_text}")
    
    qa_processor = KoreanQAProcessor()
    
    questions = [
        ("이름", "이름이 무엇입니까?"),
        ("나이", "나이가 몇살입니까?"),
        ("직업", "직업이 무엇입니까?"),
        ("취미", "취미가 무엇입니까?"),
        ("TF", "김철수는 좋은 사람입니까?"),
        ("GENDER", "김철수는 어떤 성별입니까?"),
        ("CHOICE", "김철수의 직업은?", ["의사", "교사", "소프트웨어 엔지니어", "요리사"])
    ]
    
    for q_type, question, *choices in questions:
        if choices:
            answer = qa_processor.get_answer(question, transcribed_text, q_type, choices[0])
        else:
            answer = qa_processor.get_answer(question, transcribed_text, q_type)
        logging.info(f"질문: {question}")
        logging.info(f"답변: {answer}")
        print(f"질문: {question}")
        print(f"답변: {answer}")
        print("-" * 30)
    
    total_time = time.time() - start_time
    logging.info(f"총 소요 시간: {total_time/60:.1f}분 ({total_time:.1f}초)")

if __name__ == "__main__":
    main()