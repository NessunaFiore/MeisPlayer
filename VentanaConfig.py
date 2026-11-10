import json
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from Downloader import obtener_ruta_config
from ui.styles import resource_path


class ConfigApp(QDialog):
    def __init__(self, on_save_callback, on_cancel_callback=None, parent=None):
        super().__init__(parent)
        self.on_save_callback = on_save_callback
        self.on_cancel_callback = on_cancel_callback
        self._saved = False

        self.setWindowTitle("Configuración inicial - Mei's Player")
        icon_path = resource_path(os.path.join("recursos", "imagenes", "Mei.ico"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.setFixedSize(460, 310)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(12)

        title = QLabel("¡Bienvenido a Mei's Player!")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16pt; font-weight: 700;")
        layout.addWidget(title)

        description = QLabel(
            "Para usar la aplicación necesitas tus propias llaves de Spotify.\n"
            "Si no sabes cómo obtenerlas, consulta el tutorial."
        )
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)
        layout.addWidget(description)

        form = QFormLayout()
        self.entry_id = QLineEdit()
        self.entry_secret = QLineEdit()
        self.entry_secret.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Client ID:", self.entry_id)
        form.addRow("Client Secret:", self.entry_secret)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        tutorial_button = QPushButton("Ver tutorial")
        tutorial_button.clicked.connect(self.mostrar_tutorial)
        save_button = QPushButton("Guardar y abrir app")
        save_button.clicked.connect(self.guardar_config)
        buttons.addWidget(tutorial_button)
        buttons.addWidget(save_button)
        layout.addLayout(buttons)
        self._centrar()

    def _centrar(self):
        screen = self.screen().availableGeometry()
        self.move(
            screen.center().x() - self.width() // 2,
            screen.center().y() - self.height() // 2,
        )

    def mostrar_tutorial(self):
        tutorial = QDialog(self)
        tutorial.setWindowTitle("Tutorial: Cómo obtener tus API Keys")
        tutorial.setWindowIcon(self.windowIcon())
        tutorial.resize(800, 600)

        layout = QVBoxLayout(tutorial)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 12, 20, 12)

        pasos = [
            (
                "1. Ve al Spotify Developer Dashboard",
                "Inicia sesión con tu cuenta de Spotify y haz clic en 'Create app'.",
                "tutorial_1.jpg",
            ),
            (
                "2. Configura tu app",
                "Llena los datos. En 'Redirect URIs' coloca exactamente: "
                "http://127.0.0.1:8080/callback\nHaz clic en 'Save' y luego "
                "copia tu Client ID y Client Secret.",
                "tutorial_2.jpg",
            ),
            (
                "3. Pega tus llaves aquí",
                "Vuelve a esta ventana y pega el Client ID y el Client Secret "
                "en los recuadros correspondientes.",
                "tutorial_3.jpg",
            ),
        ]

        for index, (title, text, image_name) in enumerate(pasos):
            step_title = QLabel(title)
            step_title.setStyleSheet("font-size: 12pt; font-weight: 700;")
            content_layout.addWidget(step_title)
            if index == 0:
                link_label = QLabel(
                    text
                    + ' <a href="https://developer.spotify.com/dashboard">'
                    "Spotify Developer Dashboard</a>"
                )
                link_label.setOpenExternalLinks(True)
                link_label.setWordWrap(True)
                content_layout.addWidget(link_label)
            else:
                step_text = QLabel(text)
                step_text.setWordWrap(True)
                content_layout.addWidget(step_text)

            image_path = resource_path(
                os.path.join("recursos", "imagenes", image_name)
            )
            image = QPixmap(image_path)
            if image.isNull():
                image_label = QLabel(f"[Imagen no encontrada: {image_name}]")
                image_label.setStyleSheet("color: #E53935;")
            else:
                image_label = QLabel()
                image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                image_label.setPixmap(
                    image.scaled(
                        700,
                        300,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
            content_layout.addWidget(image_label)

        scroll.setWidget(content)
        layout.addWidget(scroll)
        close_button = QPushButton("Cerrar tutorial")
        close_button.clicked.connect(tutorial.accept)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignLeft)
        tutorial.exec()

    def guardar_config(self):
        client_id = self.entry_id.text().strip()
        client_secret = self.entry_secret.text().strip()
        if not client_id or not client_secret:
            QMessageBox.warning(
                self,
                "Campos vacíos",
                "Por favor, introduce ambas llaves.",
            )
            return

        try:
            config_path = obtener_ruta_config()
            config_data = {}
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as config_file:
                    saved_config = json.load(config_file)
                if not isinstance(saved_config, dict):
                    raise ValueError("El archivo de configuración no es válido.")
                config_data.update(saved_config)

            config_data.update(
                {
                    "CLIENT_ID": client_id,
                    "CLIENT_SECRET": client_secret,
                }
            )
            with open(config_path, "w", encoding="utf-8") as config_file:
                json.dump(config_data, config_file, indent=4)
        except (OSError, ValueError) as error:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo guardar la configuración: {error}",
            )
            return

        self._saved = True
        QMessageBox.information(
            self,
            "Configuración guardada",
            "Las llaves se guardaron correctamente.",
        )
        self.on_save_callback()
        self.accept()

    def closeEvent(self, event):
        if not self._saved and self.on_cancel_callback is not None:
            self.on_cancel_callback()
        super().closeEvent(event)
