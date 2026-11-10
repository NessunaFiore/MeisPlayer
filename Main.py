import os
import sys

from PySide6.QtWidgets import QApplication

from Downloader import obtener_ruta_config
from VentanaConfig import ConfigApp
from VentanaPrincipal import MusicApp
from ui.styles import apply_dark_theme


def abrir_principal(app=None):
    app = app or QApplication.instance()
    ventana = MusicApp()
    ventana.show()
    app._mei_main_window = ventana
    return ventana


def iniciar_app():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("Mei's Player")
    app.setQuitOnLastWindowClosed(False)
    apply_dark_theme(app)

    if not os.path.exists(obtener_ruta_config()):
        ventana_config = ConfigApp(
            on_save_callback=lambda: abrir_principal(app),
            on_cancel_callback=app.quit,
        )
        ventana_config.show()
        app._mei_config_window = ventana_config
    else:
        abrir_principal(app)

    return app.exec()


if __name__ == "__main__":
    sys.exit(iniciar_app())
