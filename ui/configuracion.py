from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class ConfiguracionPage(QWidget):
    cambiar_api_solicitado = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(12)

        title = QLabel("Configuración")
        title.setStyleSheet("font-size: 20pt; font-weight: 700; color: #F044A8;")
        layout.addWidget(title)

        description = QLabel(
            "Administra las credenciales de Spotify que utiliza la aplicación."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        change_api_button = QPushButton("Cambiar API Keys")
        change_api_button.clicked.connect(self.cambiar_api_solicitado.emit)
        layout.addWidget(change_api_button, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addStretch()
