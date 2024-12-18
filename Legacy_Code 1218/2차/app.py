import sys
import os
from PyQt5.QtWidgets import QApplication
from main_screen import MainScreen

if __name__ == "__main__":

    app = QApplication(sys.argv)

    # 앱 실행
    main_window = MainScreen(None)
    main_window.app = main_window  # 앱 참조
    main_window.show()

    sys.exit(app.exec_())
