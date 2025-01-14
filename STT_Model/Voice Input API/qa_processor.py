from transformers import pipeline, AutoModelForQuestionAnswering, AutoTokenizer
from kiwipiepy import Kiwi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
import logging

'''
after modify the number control text
'''

class KoreanQAProcessor:
    def __init__(self):
        self.model_name = "monologg/koelectra-base-v3-finetuned-korquad"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForQuestionAnswering.from_pretrained(self.model_name)
        self.qa_pipeline = pipeline(
            "question-answering",
            model=self.model,
            tokenizer=self.tokenizer
        )
        self.kiwi = Kiwi()
        
        self.positive_words = {'예', '네', '맞아요', '그렇습니다', '마십니다', '합니다', '좋습니다'}
        self.negative_words = {'아니요', '아니오', '아닙니다', '안', '않', '없'}
        
        self.walking_levels = {
            '매우': 10000,
            '많이': 8000,
            '보통': 7000,
            '조금': 5600,
            '거의': 3000
        }

    def extract_name(self, text):
        """이름 추출"""
        # "이름은 XXX" 패턴 찾기
        name_pattern = re.search(r'이름[은는이가]\s*([가-힣]{2,4})', text)
        if name_pattern:
            return name_pattern.group(1)
        
        # 형태소 분석으로 이름 후보 찾기
        morphs = self.kiwi.analyze(text)
        for word, pos, _, _ in morphs[0]:
            if pos == 'NNP' and len(word) >= 2 and len(word) <= 4:
                return word
        return None

    def extract_number(self, text):
        """숫자 추출"""
        # 숫자 패턴 찾기 (정수 또는 소수)
        numbers = re.findall(r'\d+\.?\d*', text)
        if numbers:
            return numbers[0]
        
        # 한글 숫자 변환
        korean_numbers = {'일':1, '이':2, '삼':3, '사':4, '오':5, 
                         '육':6, '칠':7, '팔':8, '구':9, '십':10}
        for kor, num in korean_numbers.items():
            if kor in text:
                return str(num)
        return None

    def check_yes_no(self, text):
        """예/아니오 응답 확인"""
        text = text.lower()
        
        # 긍정 단어 확인
        if any(word in text for word in self.positive_words):
            return "예"
            
        # 부정 단어 확인
        if any(word in text for word in self.negative_words):
            return "아니오"
            
        return None

    def extract_walking_level(self, text):
        """걷기 운동량 수준 추출"""
        for level, steps in self.walking_levels.items():
            if level in text:
                return steps
        return 7000  # 기본값: 보통

    def get_answer(self, question, context, question_type):
        """질문 유형에 따른 답변 추출"""
        logging.info(f"Processing answer - Type: {question_type}, Context: {context}")
        
        try:
            if question_type == 'name':
                answer = self.extract_name(context)
                logging.info(f"Extracted name: {answer}")
                return answer

            elif question_type == 'age':
                answer = self.extract_number(context)
                logging.info(f"Extracted age: {answer}")
                return answer

            elif question_type == 'sex':
                if '남' in context:
                    return '남자'
                elif '여' in context:
                    return '여자'
                return None

            elif question_type in ['weight', 'height', 'sleepTime', 'heartRate']:
                answer = self.extract_number(context)
                logging.info(f"Extracted number for {question_type}: {answer}")
                return answer

            elif question_type in ['drink', 'smoke', 'fatigue', 'cholesterol']:
                answer = self.check_yes_no(context)
                logging.info(f"Extracted yes/no for {question_type}: {answer}")
                return answer

            elif question_type == 'walking':
                answer = self.extract_walking_level(context)
                logging.info(f"Extracted walking level: {answer}")
                return answer

            elif question_type in ['systolicBP', 'diastolicBP']:
                numbers = re.findall(r'\d+', context)
                if len(numbers) >= 2:
                    return numbers[0] if question_type == 'systolicBP' else numbers[1]
                return None

            logging.warning(f"Unknown question type: {question_type}")
            return None

        except Exception as e:
            logging.error(f"Error processing answer: {str(e)}")
            return None