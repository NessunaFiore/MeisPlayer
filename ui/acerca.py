import platform

from PySide6.QtCore import Qt, qVersion
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class AcercaPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(12)

        title = QLabel("Acerca de Mei's Player")
        title.setStyleSheet("font-size: 20pt; font-weight: 700; color: #F044A8;")
        layout.addWidget(title)

        description = QLabel(
            "Aplicación de escritorio para gestionar búsquedas y descargas de música."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        system_title = QLabel("Información del sistema")
        system_title.setStyleSheet("font-size: 12pt; font-weight: 700;")
        layout.addWidget(system_title)

        system_info = QLabel(
            f"Sistema operativo: {platform.system()} {platform.release()}\n"
            f"Arquitectura: {platform.machine()}\n"
            f"Python: {platform.python_version()}\n"
            f"Qt: {qVersion()}"
        )
        system_info.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(system_info)
        layout.addStretch()
