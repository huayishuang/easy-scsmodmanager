from __future__ import annotations

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from easy_scsmodmanager import __app_name__, __version__
from easy_scsmodmanager.utils.i18n import t


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{__app_name__} {__version__}")
        self.setMinimumSize(QSize(1200, 720))

        placeholder = QWidget(self)
        layout = QVBoxLayout(placeholder)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        msg = QLabel(t("app.placeholder.scaffold"), placeholder)
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setStyleSheet("font-size: 16px; color: #999999;")
        layout.addWidget(msg)

        self.setCentralWidget(placeholder)
