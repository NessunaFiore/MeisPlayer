# styles.py
import os
import sys
import math
import ctypes
from ctypes import wintypes
import tkinter.font as tkfont
from tkinter import ttk
import urllib.request
import hashlib
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageTk

# Paleta de colores (Manteniendo un tono limpio)
COLOR_BG = "#F5F5F5"       # Fondo general
COLOR_ROW_BG = "#F5F5F5"   # Fondo de las filas
COLOR_TEXT_PRIMARY = "#000000" # Texto principal (Título)
COLOR_TEXT_SECONDARY = "#585757" # Texto secundario (Artista)
COLOR_HOVER = "#E0E0E0"    # Color al pasar el mouse (marco sutil)
THEME_LIGHT = {
    "background": COLOR_BG,
    "foreground": COLOR_TEXT_PRIMARY,
    "secondary": COLOR_TEXT_SECONDARY,
    "hover": COLOR_HOVER,
    "field": "#FFFFFF",
    "button": "#E8E8E8",
    "button_active": "#D6D6D6",
    "track": "#D1D1D1",
    "outline": "#BDBDBD",
    "field_outline": "#FFFFFF",
}
THEME_DARK = {
    "background": "#202127",
    "foreground": "#F0F0F2",
    "secondary": "#B6B7C0",
    "hover": "#33353E",
    "field": "#2B2D35",
    "button": "#373943",
    "button_active": "#484B57",
    "track": "#3A3C45",
    "outline": "#555862",
    "field_outline": "#2B2D35",
}
_cover_download_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="cover-download")

def aplicar_barra_titulo_oscura(ventana):
    """Solicita a Windows el modo oscuro para la barra de título nativa."""
    if sys.platform != "win32":
        return
    try:
        dwmapi = ctypes.WinDLL("dwmapi")
        user32 = ctypes.WinDLL("user32")
        user32.GetParent.argtypes = (ctypes.c_void_p,)
        user32.GetParent.restype = ctypes.c_void_p
        dwmapi.DwmSetWindowAttribute.argtypes = (
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_void_p,
            ctypes.c_uint,
        )
        dwmapi.DwmSetWindowAttribute.restype = ctypes.c_long
        hwnd = ctypes.c_void_p(ventana.winfo_id())
        hwnd_marco = user32.GetParent(hwnd) or hwnd
        valor = ctypes.c_int(1)
        for atributo in (20, 19):
            if dwmapi.DwmSetWindowAttribute(
                hwnd_marco,
                atributo,
                ctypes.byref(valor),
                ctypes.sizeof(valor),
            ) == 0:
                return
        print("Windows no pudo activar el modo oscuro para la barra de título.")
    except (AttributeError, OSError) as error:
        print(f"No se pudo aplicar la barra de título oscura: {error}")

def configurar_estilos_oscuro(ventana):
    """Aplica la paleta oscura a los widgets ttk y al fondo de la ventana."""
    ventana.configure(bg=THEME_DARK["background"])
    ttk_style = ttk.Style(ventana)
    ttk_style.theme_use("clam")
    ttk_style.configure(
        ".",
        background=THEME_DARK["background"],
        foreground=THEME_DARK["foreground"],
    )
    ttk_style.configure(
        "TFrame",
        background=THEME_DARK["background"],
    )
    ttk_style.configure(
        "TLabel",
        background=THEME_DARK["background"],
        foreground=THEME_DARK["foreground"],
    )
    ttk_style.configure(
        "TButton",
        background=THEME_DARK["button"],
        foreground=THEME_DARK["foreground"],
        bordercolor=THEME_DARK["outline"],
        focuscolor=THEME_DARK["outline"],
        padding=(8, 4),
    )
    ttk_style.map(
        "TButton",
        background=[
            ("active", THEME_DARK["button_active"]),
            ("disabled", THEME_DARK["background"]),
        ],
        foreground=[("disabled", THEME_DARK["secondary"])],
    )
    ttk_style.configure(
        "TEntry",
        fieldbackground=THEME_DARK["field"],
        foreground=THEME_DARK["foreground"],
        insertcolor=THEME_DARK["foreground"],
        bordercolor=THEME_DARK["outline"],
    )
    ttk_style.configure(
        "TCombobox",
        fieldbackground=THEME_DARK["field"],
        background=THEME_DARK["button"],
        foreground=THEME_DARK["foreground"],
        arrowcolor=THEME_DARK["foreground"],
        bordercolor=THEME_DARK["outline"],
    )
    ttk_style.map(
        "TCombobox",
        fieldbackground=[("readonly", THEME_DARK["field"])],
        foreground=[("readonly", THEME_DARK["foreground"])],
        selectbackground=[("readonly", THEME_DARK["field"])],
        selectforeground=[("readonly", THEME_DARK["foreground"])],
    )
    ttk_style.configure(
        "Vertical.TScrollbar",
        background=THEME_DARK["button"],
        troughcolor=THEME_DARK["track"],
        arrowcolor=THEME_DARK["foreground"],
        bordercolor=THEME_DARK["background"],
    )
    ventana.option_add("*TCombobox*Listbox.background", THEME_DARK["field"])
    ventana.option_add("*TCombobox*Listbox.foreground", THEME_DARK["foreground"])
    ventana.option_add("*TCombobox*Listbox.selectBackground", THEME_DARK["button_active"])
    ventana.option_add("*TCombobox*Listbox.selectForeground", THEME_DARK["foreground"])

def crear_rectangulo_redondeado(canvas, x1, y1, x2, y2, radio, **kwargs):
    """Dibuja un rectángulo redondeado sin las distorsiones del spline de Tk."""
    radio = max(0, min(radio, (x2 - x1) / 2, (y2 - y1) / 2))
    puntos = []
    esquinas = (
        (x1 + radio, y1 + radio, 180, 270),
        (x2 - radio, y1 + radio, 270, 360),
        (x2 - radio, y2 - radio, 0, 90),
        (x1 + radio, y2 - radio, 90, 180),
    )
    for centro_x, centro_y, inicio, fin in esquinas:
        for paso in range(9):
            angulo = math.radians(inicio + (fin - inicio) * paso / 8)
            puntos.extend((
                centro_x + radio * math.cos(angulo),
                centro_y + radio * math.sin(angulo),
            ))
    return canvas.create_polygon(*puntos, smooth=False, **kwargs)

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- LÓGICA DE LA FUENTE ---
def cargar_fuente_custom(ventana):
    """Carga Milesdane para este proceso y devuelve la fuente del título."""
    ruta_fuente = resource_path("Milesdane.ttf")
    if not os.path.isfile(ruta_fuente):
        print(f"No se encontró la fuente Milesdane: {ruta_fuente}")
        return ("Helvetica", 28, "bold")

    if sys.platform != "win32":
        print("La carga privada de Milesdane solo está configurada para Windows.")
        return ("Helvetica", 28, "bold")

    try:
        gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
        add_font = gdi32.AddFontResourceExW
        add_font.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.LPVOID)
        add_font.restype = wintypes.INT
        if add_font(ruta_fuente, 0x10, None) == 0:
            raise OSError("Windows no pudo registrar Milesdane.ttf.")
    except (AttributeError, OSError) as error:
        print(f"No se pudo cargar Milesdane: {error}")
        return ("Helvetica", 28, "bold")

    return ("Milesdane Trial", 28, "bold")

# --- LÓGICA DE CACHÉ PARA CARÁTULAS ---
def obtener_ruta_cache():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.abspath(".")
    cache_dir = os.path.join(base_path, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

def descargar_caratula(url, callback):
    """Descarga la carátula en un hilo para no bloquear la interfaz y llama al callback cuando termina."""
    if not url:
        callback(None)
        return

    cache_dir = obtener_ruta_cache()
    # Creamos un nombre de archivo único basado en la URL
    nombre_archivo = hashlib.md5(url.encode()).hexdigest() + ".jpg"
    ruta_local = os.path.join(cache_dir, nombre_archivo)

    if os.path.exists(ruta_local):
        callback(ruta_local)
        return

    def _descargar():
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response, open(ruta_local, 'wb') as out_file:
                out_file.write(response.read())
            callback(ruta_local)
        except Exception as e:
            print(f"Error descargando carátula: {e}")
            callback(None)

    _cover_download_executor.submit(_descargar)

def crear_imagen_tk(ruta, tamaño=(48, 48)):
    """Crea una imagen compatible con Tkinter redimensionada."""
    try:
        img = Image.open(ruta)
        img = img.resize(tamaño, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except:
        return None