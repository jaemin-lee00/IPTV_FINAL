from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QIcon, QPalette, QBrush, QLinearGradient, QColor
from PyQt5.QtCore import Qt
import os


class MainScreen(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.setWindowTitle("영화 VOD 안내 UI")
        self.setGeometry(100, 100, 1200, 700)
        self.app = app  # 앱 참조 저장
        self.initUI()

    def initUI(self):
        # 메인 위젯 설정
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # 배경 그라데이션 설정
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0.0, QColor("#000000"))
        gradient.setColorAt(1.0, QColor("#495057"))

        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setPalette(palette)

        # 메인 레이아웃
        main_layout = QHBoxLayout()

        # 툴바 설정
        self.setup_toolbar(main_layout)

        # 배너와 콘텐츠 영역 설정
        content_layout = QVBoxLayout()
        self.setup_banner(content_layout)  # 배너 추가
        self.add_middle_mention(content_layout)  # 멘트 추가
        self.show_movie_content(content_layout)  # 영화 포스터 추가

        # 메인 레이아웃에 콘텐츠 추가
        main_layout.addLayout(content_layout)
        main_widget.setLayout(main_layout)

    def setup_toolbar(self, layout):
        """왼쪽 툴바 설정"""
        toolbar_layout = QVBoxLayout()
        toolbar_layout.setAlignment(Qt.AlignTop)

        # 툴바 버튼 추가
        tool_buttons = [
            {"name": "홈", "icon": "2차/home.png"},
            {"name": "검색", "icon": "2차/search.png"},
            {"name": "설정", "icon": "2차/setting.png"},
            {"name": "movie", "icon": "2차/movie.png"}
        ]

        for tool in tool_buttons:
            button = QPushButton()
            button.setFixedSize(50, 50)
            button.setStyleSheet("border: none; background-color: transparent;")
            if os.path.exists(tool["icon"]):
                button.setIcon(QIcon(tool["icon"]))
                button.setIconSize(button.size())
            else:
                button.setText(tool["name"])
                button.setStyleSheet("color: white; font-size: 12px;")
            toolbar_layout.addWidget(button)

        # 툴바 영역 구성
        toolbar_widget = QWidget()
        toolbar_widget.setLayout(toolbar_layout)
        toolbar_widget.setFixedWidth(60)
        toolbar_widget.setStyleSheet("background-color: #333333;")
        layout.addWidget(toolbar_widget)

    def setup_banner(self, layout):
        """배너 설정"""
        banner_label = QLabel()
        banner_pixmap = QPixmap("2차/배너.png")  # 배너 이미지 경로
        if not banner_pixmap.isNull():
            banner_pixmap = banner_pixmap.scaled(
                self.width() - 60, 240, Qt.IgnoreAspectRatio, Qt.SmoothTransformation
            )
            banner_label.setPixmap(banner_pixmap)
        banner_label.setFixedHeight(250)
        layout.addWidget(banner_label)

    def add_middle_mention(self, layout):
        """배너 아래 멘트 추가"""
        mention_label = QLabel("고객님을 위한 다시보기 추천 순위")
        mention_label.setAlignment(Qt.AlignLeft)
        mention_label.setStyleSheet("font-size: 20px; color: white; font-weight: bold; margin: 10px;")
        layout.addWidget(mention_label)

    def show_movie_content(self, layout):
        """영화 포스터 콘텐츠 추가"""
        poster_layout = QHBoxLayout()
        poster_layout.setContentsMargins(0, 0, 0, 30)
        poster_layout.setSpacing(5)

        movies = [
            {"poster": "2차/poster1.jpg", "id": 0},
            {"poster": "2차/poster2.jpg", "id": 1},
            {"poster": "2차/poster3.jpg", "id": 2},
            {"poster": "2차/poster4.jpg", "id": 3},
            {"poster": "2차/poster5.jpg", "id": 4},
        ]

        for movie in movies:
            poster_button = QPushButton()
            poster_button.setStyleSheet("border: none;")  # 버튼 테두리 제거
            poster_button.setFixedSize(210, 280)  # 포스터 크기 고정

            # 포스터 이미지 로드
            if os.path.exists(movie["poster"]):
                pixmap = QPixmap(movie["poster"]).scaled(
                    210, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                poster_button.setIcon(QIcon(pixmap))
                poster_button.setIconSize(pixmap.size())
            else:
                poster_button.setText("이미지 없음")
                poster_button.setStyleSheet("color: white; font-size: 14px;")

            # 포스터 클릭 시 상세 화면 이동
            poster_button.clicked.connect(lambda _, movie_id=movie["id"]: self.go_to_detail_screen(movie_id))
            poster_layout.addWidget(poster_button)

        # 포스터가 중앙 정렬되도록 설정
        container = QWidget()
        container.setLayout(poster_layout)
        container_layout = QVBoxLayout()
        container_layout.addWidget(container)
        container_layout.setAlignment(Qt.AlignCenter)  # 포스터를 중앙 정렬
        layout.addLayout(container_layout)

    def go_to_detail_screen(self, movie_id):
        """상세 화면으로 이동"""
        from detail_screen import DetailScreen
        self.app.setCentralWidget(DetailScreen(self.app, movie_id))
