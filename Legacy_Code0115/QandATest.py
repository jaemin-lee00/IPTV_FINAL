from transformers import pipeline, AutoModelForQuestionAnswering, AutoTokenizer
from kiwipiepy import Kiwi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

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
        
        # 긍정/부정 분석을 위한 키워드 사전
        self.positive_words = {'맞습니다', '네', '맞아요', '그렇습니다', '동의합니다', '좋습니다'}
        self.negative_words = {'아니요', '아닙니다', '틀립니다', '다릅니다', '반대합니다'}
        
        # 성별 관련 키워드 사전
        self.male_indicators = {
            '그': 0.6, '남자': 1.0, '남성': 1.0, '형': 0.8, '아들': 0.9,
            '그는': 0.7, '그가': 0.7, '형님': 0.8, '아저씨': 0.8
        }
        self.female_indicators = {
            '그녀': 0.7, '여자': 1.0, '여성': 1.0, '누나': 0.8, '딸': 0.9,
            '언니': 0.8, '아가씨': 0.8, '여사': 0.8
        }

    def analyze_tf_question(self, text):
        """긍정/부정 분석을 통한 TF 판단"""
        morphs = self.kiwi.analyze(text)[0][0]
        words = [token for token, _, _, _ in morphs]
        
        positive_score = sum(1 for word in words if word in self.positive_words)
        negative_score = sum(1 for word in words if word in self.negative_words)
        
        # 문장의 전반적인 톤 분석
        sentiment_words = {'좋': 1, '훌륭': 1, '긍정': 1, '맞': 1,
                         '나쁘': -1, '틀린': -1, '부정': -1, '다르': -1}
        
        sentiment_score = 0
        for word in words:
            for key, value in sentiment_words.items():
                if key in word:
                    sentiment_score += value
        
        final_score = positive_score - negative_score + sentiment_score
        return "O" if final_score >= 0 else "X"

    def analyze_gender_question(self, text):
        """성별 관련 키워드 가중치 분석"""
        morphs = self.kiwi.analyze(text)[0][0]
        words = [token for token, _, _, _ in morphs]
        
        male_score = 0
        female_score = 0
        
        for word in words:
            male_score += self.male_indicators.get(word, 0)
            female_score += self.female_indicators.get(word, 0)
            
        return "남자" if male_score >= female_score else "여자"

    def analyze_multiple_choice(self, answer, choices):
        """객관식 답안 분석"""
        vectorizer = TfidfVectorizer()
        
        # 선택지와 답변을 벡터화
        all_texts = choices + [answer]
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        
        # 답변과 각 선택지 간의 유사도 계산
        similarities = cosine_similarity(
            tfidf_matrix[-1:], 
            tfidf_matrix[:-1]
        )[0]
        
        # 가장 유사한 선택지의 인덱스 반환
        most_similar_idx = np.argmax(similarities)
        return str(most_similar_idx + 1)  # 1부터 시작하는 번호 반환

    def extract_core_info(self, text, question_type, choices=None):
        """질문 유형에 따른 핵심 정보 추출"""
        if question_type in ["TF", "O,X", "YN"]:
            return self.analyze_tf_question(text)
            
        elif question_type in ["GENDER", "남녀"]:
            return self.analyze_gender_question(text)
            
        elif question_type == "CHOICE" and choices:
            return self.analyze_multiple_choice(text, choices)
            
        # 기존 문장형 질문 처리
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

    def get_answer(self, question, context, question_type, choices=None):
        """질문에 대한 답변 추출 및 정제"""
        # QA 모델을 통한 1차 답변 추출
        result = self.qa_pipeline(question=question, context=context)
        # 질문 유형에 따른 답변 정제
        clean_answer = self.extract_core_info(result['answer'], question_type, choices)
        return clean_answer

# QA 프로세서 초기화
qa_processor = KoreanQAProcessor()

# 테스트용 컨텍스트
context = """
김철수는 서울특별시 강남구에 살고 있는 남성입니다.
그는 매우 성실하고 좋은 사람입니다.
그의 나이는 35세이고 직업은 소프트웨어 엔지니어입니다.
"""

# 다양한 유형의 테스트 질문
test_questions = [
    ("TF", "김철수는 좋은 사람입니까?"),
    ("GENDER", "김철수는 어떤 성별입니까?"),
    ("CHOICE", "김철수의 직업은?", ["의사", "교사", "소프트웨어 엔지니어", "요리사"])
]

# 테스트 실행
for test in test_questions:
    if len(test) == 3:
        q_type, question, choices = test
        answer = qa_processor.get_answer(question, context, q_type, choices)
    else:
        q_type, question = test
        answer = qa_processor.get_answer(question, context, q_type)
    
    print(f"질문 유형: {q_type}")
    print(f"질문: {question}")
    print(f"답변: {answer}")
    print("-" * 30)