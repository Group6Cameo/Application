from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel


class FaceTrackingWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Face Tracking Feed Placeholder"))
        self.setLayout(layout)
