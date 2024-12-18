from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QMessageBox, QFrame
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import os
import sys

# 상위 디렉토리 경로를 파이썬 모듈 검색 경로에 추가
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if (parent_dir not in sys.path):
    sys.path.append(parent_dir)

from EQplayer import EQPlayer


class DetailScreen(QMainWindow):
    def __init__(self, app, movie_id):
        super().__init__()
        self.setWindowTitle("영화 VOD UI")
        self.setGeometry(100, 100, 1280, 800)
        self.app = app  # 앱 참조 저장
        self.current_index = movie_id  # 현재 선택된 영화 인덱스
        self.selected_index = None  # 마지막으로 클릭한 영화 인덱스
        self.category = None  # 선택된 카테고리 변수
        self.movies = [
            {"poster": "2차/poster1_detail.jpg", "desc": "전설적인 밴드 퀸과 프레디 머큐리의 열정, 음악, 그리고 영혼을 담은 감동적인 이야기.", "hashtags": ["#드라마", "#프레디머큐리", "#영혼을울리는"]},
            {"poster": "2차/poster2_detail.jpg", "desc": "실화에서 시작된 초자연적 공포, 워렌 부부가 맞서는 소름 돋는 악령의 실체!", "hashtags": ["#공포", "#실화바탕", "#심장주의"]},
            {"poster": "2차/poster3_detail.jpg", "desc": "전설은 끝나지 않는다, 존 윅의 폭발적 액션과 복수가 절정을 이루는 네 번째 이야기!", "hashtags": ["#액션", "#존윅", "#킬러의귀환"]},
            {"poster": "2차/poster4_detail.jpg", "desc": "죽음 너머의 아름다운 세계, 음악과 가족의 소중함을 노래하는 환상적인 이야기!", "hashtags": ["#애니메이션", "#눈물버튼", "#음악과가족"]},
            {"poster": "2차/poster5_detail.jpg", "desc": "감정들의 새로운 모험, 우리 마음속 또 다른 세계를 탐험하다!", "hashtags": ["#애니메이션", "#감정대탐험", "#유머와감동"]},
        ]
        self.flag = False
        self.initUI()

    def initUI(self):
        # 메인 위젯 설정
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 포스터 위 문구 추가
        self.recommendation_label = QLabel("유플러스 ai, jin-mo의 이유있는 추천작")
        self.recommendation_label.setAlignment(Qt.AlignCenter)
        self.recommendation_label.setStyleSheet("font-size: 20px; font-weight: bold; color: white; margin-bottom: 10px;")
        main_layout.addWidget(self.recommendation_label)

        # 슬라이더 영역
        self.slider_layout = QHBoxLayout()
        self.slider_layout.setContentsMargins(0, 0, 0, 0)
        self.slider_layout.setSpacing(10)
        main_layout.addLayout(self.slider_layout)

        # 설명 영역
        self.desc_label = QLabel("")
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("font-size: 18px; color: white; margin-top: 5px; margin-bottom: 5px;")
        main_layout.addWidget(self.desc_label)

        # 해시태그 영역
        self.hashtags_layout = QHBoxLayout()
        self.hashtags_layout.setContentsMargins(0, 0, 0, 0)
        self.hashtags_layout.setSpacing(3)
        self.hashtags_layout.setAlignment(Qt.AlignCenter)
        main_layout.addLayout(self.hashtags_layout)

        self.update_movie_display(animated=False)  # 초기화 시 현재 영화 표시
        self.main_widget.setLayout(main_layout)

    def update_movie_display(self, animated=True):
        """포스터와 설명 및 해시태그 업데이트"""
        # 기존 슬라이더 레이아웃 정리
        for i in reversed(range(self.slider_layout.count())):
            self.slider_layout.itemAt(i).widget().deleteLater()

        # 기존 해시태그 정리
        for i in reversed(range(self.hashtags_layout.count())):
            self.hashtags_layout.itemAt(i).widget().deleteLater()

        # 포스터 슬라이드 업데이트
        for offset in [-1, 0, 1]:  # 이전, 현재, 다음 포스터
            movie_index = (self.current_index + offset) % len(self.movies)
            movie = self.movies[movie_index]

            frame = QFrame()  # 테두리를 포함하는 프레임 생성
            frame_layout = QVBoxLayout()
            frame_layout.setContentsMargins(0, 0, 0, 0)
            frame.setLayout(frame_layout)

            poster_label = QLabel()
            poster_label.setAlignment(Qt.AlignCenter)

            # 중앙 포스터와 양옆 포스터 크기 및 스타일 설정
            if (offset == 0):  # 중앙 포스터
                poster_label.setFixedSize(900, 550)
                frame.setStyleSheet(
                    """
                    border: 4px solid white;
                    border-radius: 20px;
                    background-color: transparent;
                    """
                )
            else:  # 양옆 포스터
                poster_label.setFixedSize(300, 200)
                frame.setStyleSheet(
                    """
                    border: none;
                    border-radius: 10px;
                    background-color: transparent;
                    """
                )

            # 포스터 이미지 설정
            if (os.path.exists(movie["poster"])):
                pixmap = QPixmap(movie["poster"]).scaled(
                    poster_label.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
                )
                poster_label.setPixmap(pixmap)
            else:
                poster_label.setText("이미지 없음")
                poster_label.setStyleSheet("font-size: 18px; color: red;")

            # 마우스 클릭 이벤트 설정
            poster_label.mousePressEvent = lambda _, i=movie_index: self.on_poster_clicked(i)
            frame_layout.addWidget(poster_label)
            self.slider_layout.addWidget(frame)

        # 설명 업데이트
        self.desc_label.setText(self.movies[self.current_index]["desc"])

        # 해시태그 업데이트
        for tag in self.movies[self.current_index]["hashtags"]:
            tag_label = QLabel(tag)
            tag_label.setAlignment(Qt.AlignCenter)
            tag_label.setStyleSheet(
                """
                font-size: 16px;
                color: white;
                background-color: transparent;
                padding: 5px 10px;
                border: 1px solid #888888;
                border-radius: 3px;
                margin: 0px;
                """
            )
            self.hashtags_layout.addWidget(tag_label)

    def on_poster_clicked(self, index):
        """포스터 클릭 동작"""
        if (index == self.current_index and self.selected_index == self.current_index):
            # 이미 중앙에 있는 포스터를 다시 클릭했을 때 팝업
            self.show_popup(index)
        else:
            # 포스터를 중앙으로 이동
            self.selected_index = self.current_index
            self.current_index = index
            self.update_movie_display(animated=True)

    def show_popup(self, index):
        """팝업 창 표시"""
        reply = QMessageBox.question(
            self,
            "추천 설정",
            "추천하는 음향셋팅을 선택하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if (reply == QMessageBox.Yes):
            # 첫 번째 해시태그를 카테고리로 설정
            self.category = self.movies[index]["hashtags"][0]
            self.def_set_categories()

    def def_set_categories(self):
        """카테고리 설정"""
        player = EQPlayer()
        category_without_first_char = self.category[1:]  # Remove '#' from category
        # Load category first
        player.load_categories(category_without_first_char)
        # This will trigger equalizer settings load with the stored category
        #player.apply_category_settings()
        print(f"Setting category: {category_without_first_char}")
        player.run()

    def get_selected_category(self):
        """선택된 카테고리 반환"""
        return self.category
    
    def Is_set_categories(self):
        return self.flag

