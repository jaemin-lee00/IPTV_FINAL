from transformers import pipeline, AutoModelForQuestionAnswering, AutoTokenizer
from kiwipiepy import Kiwi

class KoreanQAProcessor:
    def __init__(self):
        # 한국어 QA에 더 적합한 모델로 변경
        self.model_name = "monologg/koelectra-base-v3-finetuned-korquad"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForQuestionAnswering.from_pretrained(self.model_name)
        self.qa_pipeline = pipeline(
            "question-answering",
            model=self.model,
            tokenizer=self.tokenizer
        )
        self.kiwi = Kiwi()

    def extract_core_info(self, text, question_type):
        """질문 유형에 따른 핵심 정보 추출"""
        morphs = self.kiwi.analyze(text)[0][0]
        
        if question_type == "이름":
            # 사람 이름 추출 (NNP: 고유명사)
            for token, pos, _, _ in morphs:
                if pos == 'NNP' and len(token) <= 4:
                    return token
                    
        elif question_type == "나이":
            # 숫자 추출 (SN: 수사)
            for token, pos, _, _ in morphs:
                if pos == 'SN':
                    return token
                    
        elif question_type == "직업":
            # 직업 관련 명사구 추출
            job_tokens = []
            for token, pos, _, _ in morphs:
                if pos in ['NNG', 'NNP'] and token not in ['직업']:
                    job_tokens.append(token)
            return ' '.join(job_tokens)
            
        elif question_type == "취미":
            # 취미 관련 명사 추출
            hobby_tokens = []
            for token, pos, _, _ in morphs:
                if pos in ['NNG', 'NNP'] and token not in ['취미']:
                    hobby_tokens.append(token)
            return hobby_tokens[0] if hobby_tokens else ""
        
        return ""

    def get_answer(self, question, context, question_type):
        """질문에 대한 답변 추출 및 정제"""
        # QA 모델을 통한 1차 답변 추출
        result = self.qa_pipeline(question=question, context=context)
        # 질문 유형에 따른 답변 정제
        clean_answer = self.extract_core_info(result['answer'], question_type)
        return clean_answer

# QA 프로세서 초기화
qa_processor = KoreanQAProcessor()

# 테스트용 컨텍스트
context = """
김철수는 서울특별시 강남구에 살고 있습니다. 
그의 나이는 35세이고 직업은 소프트웨어 엔지니어입니다. 
취미는 테니스이며 주말마다 테니스장에서 운동을 합니다.
"""

# 질문 리스트 (질문 유형 포함)
questions = [
    ("이름", "이름이 무엇입니까?"),
    ("나이", "나이가 몇살입니까?"),
    ("직업", "직업이 무엇입니까?"),
    ("취미", "취미가 무엇입니까?")
]

# 질문별 답변 추출
for q_type, question in questions:
    answer = qa_processor.get_answer(question, context, q_type)
    print(f"질문: {question}")
    print(f"답변: {answer}")
    print("-" * 30)