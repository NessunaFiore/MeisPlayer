import hashlib
import os
import sys
import urllib.request
import ctypes
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase, QPixmap


THEME_DARK = {
    "background": "#120913",
    "foreground": "#F8EAF4",
    "secondary": "#BDA9BB",
    "hover": "#35172F",
    "field": "#1D0D1D",
    "button": "#2A1027",
    "button_active": "#4A1841",
    "track": "#35172F",
    "outline": "#81265F",
    "accent": "#F044A8",
    "success": "#35B45A",
    "error": "#F06483",
}

_cover_download_executor = ThreadPoolExecutor(
    max_workers=4,
    thread_name_prefix="cover-download",
)


def resource_path(relative_path):
    source_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    base_path = getattr(sys, "_MEIPASS", source_path)
    return os.path.join(base_path, relative_path)


def apply_dark_theme(app):
    app.setStyle("Fusion")
    app.setStyleSheet(
        f"""
        QWidget {{
            background-color: {THEME_DARK["background"]};
            color: {THEME_DARK["foreground"]};
            font-family: "Segoe UI";
            font-size: 10pt;
        }}
        QFrame#sidebar {{
            background-color: #1B0B1C;
            border-right: 1px solid {THEME_DARK["outline"]};
        }}
        QFrame#songPanel {{
            background-color: #170A18;
            border: 1px solid {THEME_DARK["outline"]};
            border-radius: 14px;
        }}
        QFrame#actionBar {{
            background-color: #1A0B1B;
            border: 1px solid {THEME_DARK["accent"]};
            border-radius: 12px;
        }}
        QLineEdit, QComboBox {{
            background-color: {THEME_DARK["field"]};
            border: 1px solid #6E2454;
            border-radius: 10px;
            padding: 9px 12px;
            selection-background-color: {THEME_DARK["accent"]};
        }}
        QComboBox::drop-down {{ border: 0; padding-right: 7px; }}
        QComboBox QAbstractItemView {{
            background-color: {THEME_DARK["field"]};
            selection-background-color: {THEME_DARK["button_active"]};
            border: 1px solid {THEME_DARK["outline"]};
        }}
        QPushButton {{
            background-color: {THEME_DARK["button"]};
            border: 1px solid #7D285F;
            border-radius: 10px;
            padding: 9px 13px;
        }}
        QPushButton:hover {{ background-color: {THEME_DARK["button_active"]}; }}
        QPushButton:disabled {{ color: {THEME_DARK["secondary"]}; }}
        QPushButton#primaryButton {{
            background-color: {THEME_DARK["accent"]};
            color: #21091B;
            border: 1px solid {THEME_DARK["accent"]};
            font-weight: 700;
        }}
        QPushButton#primaryButton:hover {{ background-color: #FF68BC; }}
        QToolButton#navButton {{
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 12px;
            padding: 4px 2px;
            font-size: 9pt;
        }}
        QToolButton#navButton:hover {{
            background-color: {THEME_DARK["hover"]};
            border-color: #6E2454;
        }}
        QToolButton#navButton:checked {{
            background-color: #571445;
            border-color: {THEME_DARK["accent"]};
            color: #FFFFFF;
        }}
        QListView {{
            background-color: transparent;
            border: none;
            outline: 0;
            padding: 3px 8px;
        }}
        QTableWidget {{
            background-color: #170A18;
            alternate-background-color: #1D0D1D;
            border: 1px solid {THEME_DARK["outline"]};
            border-radius: 10px;
            gridline-color: #3B1A34;
            selection-background-color: #571445;
        }}
        QHeaderView::section {{
            background-color: #281127;
            color: {THEME_DARK["foreground"]};
            border: none;
            border-bottom: 1px solid {THEME_DARK["outline"]};
            padding: 8px;
            font-weight: 700;
        }}
        QScrollBar:vertical {{
            background-color: {THEME_DARK["track"]};
            width: 12px;
            margin: 2px;
            border-radius: 5px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {THEME_DARK["accent"]};
            min-height: 28px;
            border-radius: 5px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QToolTip {{
            background-color: {THEME_DARK["field"]};
            color: {THEME_DARK["foreground"]};
            border: 1px solid {THEME_DARK["outline"]};
        }}
        """
    )


def aplicar_barra_titulo_oscura(ventana):
    if sys.platform != "win32":
        return

    try:
        dwmapi = ctypes.WinDLL("dwmapi")
        set_window_attribute = dwmapi.DwmSetWindowAttribute
        set_window_attribute.argtypes = (
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_void_p,
            ctypes.c_uint,
        )
        set_window_attribute.restype = ctypes.c_long
        hwnd = ctypes.c_void_p(int(ventana.winId()))

        dark_mode = ctypes.c_int(1)
        for attribute in (20, 19):
            result = set_window_attribute(
                hwnd,
                attribute,
                ctypes.byref(dark_mode),
                ctypes.sizeof(dark_mode),
            )
            if result == 0:
                break

        caption_color = ctypes.c_uint(0x272120)
        set_window_attribute(
            hwnd,
            35,
            ctypes.byref(caption_color),
            ctypes.sizeof(caption_color),
        )
        text_color = ctypes.c_uint(0xF2F0F0)
        set_window_attribute(
            hwnd,
            36,
            ctypes.byref(text_color),
            ctypes.sizeof(text_color),
        )
    except (AttributeError, OSError) as error:
        print(f"No se pudo aplicar la barra de título oscura: {error}")


def cargar_fuente_custom():
    ruta_fuente = resource_path(os.path.join("recursos", "fuentes", "Milesdane.ttf"))
    if not os.path.isfile(ruta_fuente):
        print(f"No se encontró la fuente Milesdane: {ruta_fuente}")
        return QFont("Segoe UI", 36, QFont.Weight.Bold)

    font_id = QFontDatabase.addApplicationFont(ruta_fuente)
    familias = QFontDatabase.applicationFontFamilies(font_id) if font_id >= 0 else []
    if not familias:
        print(f"No se pudo cargar la fuente Milesdane: {ruta_fuente}")
        return QFont("Segoe UI", 36, QFont.Weight.Bold)

    return QFont(familias[0], 36, QFont.Weight.Bold)


def obtener_ruta_cache():
    if getattr(sys, "frozen", False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cache_dir = os.path.join(base_path, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def descargar_caratula(url, callback):
    if not url:
        callback(None)
        return

    nombre_archivo = hashlib.md5(url.encode("utf-8")).hexdigest() + ".jpg"
    ruta_local = os.path.join(obtener_ruta_cache(), nombre_archivo)
    if os.path.exists(ruta_local):
        callback(ruta_local)
        return

    def descargar():
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            with urllib.request.urlopen(request, timeout=10) as response:
                image_data = response.read()
            with open(ruta_local, "wb") as image_file:
                image_file.write(image_data)
        except Exception as error:
            print(f"Error descargando carátula: {error}")
            callback(None)
            return
        callback(ruta_local)

    _cover_download_executor.submit(descargar)


def cargar_pixmap(ruta, tamaño=None):
    pixmap = QPixmap(ruta)
    if pixmap.isNull():
        return QPixmap()
    if tamaño is not None:
        return pixmap.scaled(
            tamaño,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
    return pixmap
