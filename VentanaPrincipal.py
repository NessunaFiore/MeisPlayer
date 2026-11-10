# VentanaPrincipal.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import os
import sys
import json
from PIL import Image
import tkinter.font as tkfont
import pystray
from winotify import Notification, audio

# Importamos el nuevo archivo de estilos
from styles import (
    cargar_fuente_custom, descargar_caratula, crear_imagen_tk,
    crear_rectangulo_redondeado, resource_path, THEME_DARK,
    aplicar_barra_titulo_oscura, configurar_estilos_oscuro,
)

from Downloader import (
    MusicDownloader, obtener_ruta_config, 
    obtener_ultima_carpeta, guardar_ultima_carpeta,
    obtener_ultimo_formato, guardar_ultimo_formato
)
from DownloaderYT import MusicDownloaderYT
from progress_bar import DownloadProgressBar

ROW_HEIGHT = 64
ROW_OVERSCAN = 6
SCROLL_FRAME_MS = 16
SCROLL_MAX_STEP = 48

def centrar_ventana(ventana, ancho, alto):
    x = (ventana.winfo_screenwidth() // 2) - (ancho // 2)
    y = (ventana.winfo_screenheight() // 2) - (alto // 2)
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

class MusicApp:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()
        self.root.title("Mei´s Player")
        self.root.geometry("850x650")
        self._theme = dict(THEME_DARK)
        self._theme_style = ttk.Style(self.root)
        configurar_estilos_oscuro(self.root)
        self._configurar_estilos_ttk()
        centrar_ventana(self.root, 850, 650)
        
        try: self.root.iconbitmap(resource_path("Mei.ico"))
        except: pass
        
        self.root.protocol('WM_DELETE_WINDOW', self.ocultar_ventana)
        self.icono_bandeja = None
        self.texto_tooltip = "Mei's Player"

        self.downloader_sp = MusicDownloader()
        self.downloader_yt = MusicDownloaderYT()
        
        self.songs = []
        self.items_ui = []
        self._visible_rows = {}
        self._render_after_id = None
        self._scroll_after_id = None
        self._scroll_target = None
        self.ultima_ruta = obtener_ultima_carpeta()
        
        self.pausado = False
        self.descargando = False
        self.progreso_actual = 0
        self.progreso_total = 0

        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.abspath(".")
        self.ruta_cache = os.path.join(base_path, "ultima_busqueda.json")

        # --- TÍTULO PRINCIPAL (Logo) ---
        fuente_logo = cargar_fuente_custom(self.root)
        self.lbl_logo = tk.Label(root, text="Mei´s Player", font=fuente_logo, bg=self._theme["background"], fg="#552D50")
        self.lbl_logo._mei_theme_role = "accent"
        self.lbl_logo.pack(pady=(15, 5))

        # --- BARRA DE BÚSQUEDA (Centrada y corta) ---
        frame_search = tk.Frame(root, bg=self._theme["background"])
        frame_search.pack(pady=(5, 15))

        tk.Label(frame_search, text="URL:", bg=self._theme["background"], fg=self._theme["foreground"]).pack(side="left", padx=(0, 5))
        self.entry_canvas = tk.Canvas(
            frame_search,
            width=400,
            height=40,
            bg=self._theme["background"],
            highlightthickness=0,
            bd=0,
            highlightbackground=self._theme["background"],
            highlightcolor=self._theme["background"],
        )
        self.entry_canvas.pack(side="left", padx=(0, 10))
        self.entry_background_id = crear_rectangulo_redondeado(
            self.entry_canvas, 1, 1, 399, 39, 10,
            fill=self._theme["field"],
            outline=self._theme["field_outline"],
        )
        self.url_entry = tk.Entry(
            self.entry_canvas,
            width=48,
            font=("Helvetica", 11),
            relief="flat",
            bd=0,
            highlightthickness=0,
            bg=self._theme["field"],
            fg=self._theme["foreground"],
            insertbackground=self._theme["foreground"],
        )
        self.entry_canvas.create_window(
            12, 20, window=self.url_entry, anchor="w", width=376, height=28
        )
        
        self.btn_buscar = ttk.Button(frame_search, text="Buscar", command=self.iniciar_busqueda, style="Mei.TButton")
        self.btn_buscar.pack(side="left")
        
        self.btn_limpiar = ttk.Button(frame_search, text="Limpiar", command=self.limpiar_busqueda, style="Mei.TButton")
        self.btn_limpiar.pack(side="left", padx=(5, 0))
        # --- FRANJA DE ESTADO ---
        frame_status = tk.Frame(root, bg=self._theme["background"])
        frame_status.pack(fill="x", padx=20, pady=(0, 10))
        
        self.lbl_estado_izq = tk.Label(frame_status, text="Listo.", font=("Helvetica", 10, "bold"), bg=self._theme["background"], fg=self._theme["foreground"], anchor="w")
        self.lbl_estado_izq.pack(side="left", fill="x", expand=True)
        
        self.lbl_estado_der = tk.Label(frame_status, text="", font=("Helvetica", 10, "bold"), bg=self._theme["background"], fg=self._theme["foreground"], anchor="e", width=15)
        self.lbl_estado_der.pack(side="right")

        # --- LISTA DE CANCIONES (Canvas con Scroll) ---
        # Contenedor principal de la lista
        self.frame_list_container = tk.Frame(root, bg=self._theme["background"])
        self.frame_list_container.pack(fill="both", expand=True, padx=20)

        # Canvas y Scrollbar
        self.canvas = tk.Canvas(self.frame_list_container, bg=self._theme["background"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(
            self.frame_list_container,
            orient="vertical",
            command=self.canvas.yview,
            style="Mei.Vertical.TScrollbar",
        )
        
        self.canvas.configure(yscrollcommand=self._actualizar_scrollbar)
        self.canvas.bind("<Configure>", self._al_cambiar_tamano_canvas)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)
        self.scrollbar.bind("<ButtonPress-1>", self._cancelar_desplazamiento_suave, add="+")

        # --- FRAME INFERIOR (CONTROLES) ---
        frame_bottom = tk.Frame(root, bg=self._theme["background"])
        frame_bottom.pack(fill="x", side="bottom", padx=20, pady=15)

        ttk.Button(frame_bottom, text="Marcar Todo", command=self.toggle_all, style="Mei.TButton").pack(side="left", padx=(0, 10))

        tk.Label(frame_bottom, text="Formato:", bg=self._theme["background"], fg=self._theme["foreground"]).pack(side="left", padx=(0, 5))
        self.formato_var = tk.StringVar(value=obtener_ultimo_formato())
        self.combo_formato = ttk.Combobox(frame_bottom, textvariable=self.formato_var, values=["mp3", "m4a", "flac", "wav"], state="readonly", width=6, style="Mei.TCombobox")
        self.combo_formato.pack(side="left", padx=(0, 10))
        self.combo_formato.bind("<<ComboboxSelected>>", self.cambiar_formato)

        self.btn_descargar = ttk.Button(frame_bottom, text="Descargar Seleccionadas", command=self.iniciar_descarga, style="Mei.TButton")
        self.btn_descargar.pack(side="left", padx=(0, 5))

        self.btn_pausar = ttk.Button(frame_bottom, text="Pausar", command=self.toggle_pausa, state="disabled", style="Mei.TButton")
        self.btn_pausar.pack(side="left")

        self.btn_api = ttk.Button(frame_bottom, text="Cambiar API Keys", command=self.cambiar_api_keys, style="Mei.TButton")
        self.btn_api.pack(side="right")
        
        self.root.deiconify()
        self.root.after_idle(aplicar_barra_titulo_oscura, self.root)
        self.root.after(100, self.cargar_ultima_busqueda)

    def _configurar_estilos_ttk(self):
        self._theme_style.configure(
            "Mei.TButton",
            background=self._theme["button"],
            foreground=self._theme["foreground"],
            bordercolor=self._theme["outline"],
            focuscolor=self._theme["outline"],
            padding=(8, 4),
        )
        self._theme_style.map(
            "Mei.TButton",
            background=[("active", self._theme["button_active"]), ("disabled", self._theme["background"])],
            foreground=[("disabled", self._theme["secondary"])],
        )
        self._theme_style.configure(
            "Mei.TCombobox",
            fieldbackground=self._theme["field"],
            background=self._theme["button"],
            foreground=self._theme["foreground"],
            arrowcolor=self._theme["foreground"],
            bordercolor=self._theme["outline"],
        )
        self._theme_style.map(
            "Mei.TCombobox",
            fieldbackground=[("readonly", self._theme["field"])],
            foreground=[("readonly", self._theme["foreground"])],
            selectbackground=[("readonly", self._theme["field"])],
            selectforeground=[("readonly", self._theme["foreground"])],
        )
        self.root.option_add("*TCombobox*Listbox.background", self._theme["field"])
        self.root.option_add("*TCombobox*Listbox.foreground", self._theme["foreground"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", self._theme["button_active"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", self._theme["foreground"])
        self._theme_style.configure(
            "Mei.Vertical.TScrollbar",
            background=self._theme["button"],
            troughcolor=self._theme["track"],
            arrowcolor=self._theme["foreground"],
            bordercolor=self._theme["background"],
        )

    def _on_mousewheel(self, event):
        widget = self.root.winfo_containing(event.x_root, event.y_root)
        dentro_lista = False
        while widget is not None:
            if widget is self.frame_list_container:
                dentro_lista = True
                break
            widget = getattr(widget, "master", None)
        if not dentro_lista:
            return None
        if self.descargando:
            return "break"

        if getattr(event, "num", None) == 4:
            delta_pixels = -24
        elif getattr(event, "num", None) == 5:
            delta_pixels = 24
        else:
            delta_pixels = max(-48, min(48, -event.delta * 0.5))

        if not delta_pixels:
            return "break"

        current = self._get_scroll_position()
        target = self._scroll_target if self._scroll_target is not None else current
        self._set_scroll_target(target + delta_pixels)
        return "break"

    def _get_scroll_metrics(self):
        region = self.canvas.cget("scrollregion")
        if not region:
            return 0.0, 0.0, 0.0
        _, top, _, bottom = map(float, region.split())
        total = max(0.0, bottom - top)
        viewport = max(1.0, float(self.canvas.winfo_height()))
        return total, viewport, max(0.0, total - viewport)

    def _get_scroll_position(self):
        total, _, _ = self._get_scroll_metrics()
        return self.canvas.yview()[0] * total if total else 0.0

    def _set_scroll_target(self, target):
        total, _, scrollable_height = self._get_scroll_metrics()
        if total <= 0 or scrollable_height <= 0:
            return
        self._scroll_target = min(max(target, 0.0), scrollable_height)
        if self._scroll_after_id is None:
            self._scroll_after_id = self.root.after(
                SCROLL_FRAME_MS,
                self._animar_desplazamiento,
            )

    def _animar_desplazamiento(self):
        self._scroll_after_id = None
        total, _, _ = self._get_scroll_metrics()
        if total <= 0 or self._scroll_target is None:
            return

        current = self._get_scroll_position()
        difference = self._scroll_target - current
        if abs(difference) <= 1:
            self.canvas.yview_moveto(self._scroll_target / total)
            self._scroll_target = None
            return

        step = min(abs(difference), SCROLL_MAX_STEP)
        next_position = current + (step if difference > 0 else -step)
        self.canvas.yview_moveto(next_position / total)
        self._scroll_after_id = self.root.after(
            SCROLL_FRAME_MS,
            self._animar_desplazamiento,
        )

    def _cancelar_desplazamiento_suave(self, _event=None):
        if self._scroll_after_id is not None:
            self.root.after_cancel(self._scroll_after_id)
            self._scroll_after_id = None
        self._scroll_target = None

    def _al_cambiar_tamano_canvas(self, event):
        self.canvas.itemconfigure("song-row", width=event.width)
        self._programar_renderizado_visible()

    def _actualizar_scrollbar(self, first, last):
        self.scrollbar.set(first, last)
        self._programar_renderizado_visible()

    def _programar_renderizado_visible(self):
        if self._render_after_id is None:
            self._render_after_id = self.root.after_idle(self._renderizar_filas_visibles)

    def _actualizar_region_desplazamiento(self):
        alto = max(1, len(self.songs) * ROW_HEIGHT)
        self.canvas.configure(scrollregion=(0, 0, max(1, self.canvas.winfo_width()), alto))
        self._programar_renderizado_visible()

    def _renderizar_filas_visibles(self):
        self._render_after_id = None
        if not self.songs:
            self._destruir_filas_montadas()
            return

        top = self.canvas.canvasy(0)
        bottom = top + max(1, self.canvas.winfo_height())
        first = max(0, int(top // ROW_HEIGHT) - ROW_OVERSCAN)
        last = min(len(self.songs), int(bottom // ROW_HEIGHT) + ROW_OVERSCAN + 1)
        visible_indices = set(range(first, last))

        for index in tuple(self._visible_rows):
            if index not in visible_indices:
                self._desmontar_fila(index)

        for index in range(first, last):
            if index not in self._visible_rows:
                self.crear_fila_visual(index, self.songs[index], self.items_ui[index])

    def _desmontar_fila(self, index):
        item = self._visible_rows.pop(index)
        item['selected'] = item['var_check'].get()
        if item['progress']._state == "downloading":
            item['state'] = "downloading"
        item['progress']._cancel_animation()
        self.canvas.delete(item['canvas_id'])
        item['frame'].destroy()
        item['frame'] = None
        item['var_check'] = None
        item['progress'] = None
        item['lbl_img'] = None
        item['canvas_id'] = None

    def _destruir_filas_montadas(self):
        for index in tuple(self._visible_rows):
            self._desmontar_fila(index)

    def actualizar_estado(self, texto_izq=None, texto_der=None):
        if texto_izq is not None:
            self.lbl_estado_izq.config(text=texto_izq)
        if texto_der is not None:
            self.lbl_estado_der.config(text=texto_der)

    def enviar_notificacion(self, titulo, mensaje, app_id="Mei's Player"):
        try:
            icon_path = resource_path("Mei.ico")
            if not os.path.exists(icon_path): icon_path = None
            toast = Notification(app_id=app_id, title=titulo, msg=mensaje, icon=icon_path)
            toast.set_audio(audio.Default, loop=False)
            toast.show()
        except Exception as e:
            print(f"No se pudo enviar la notificación: {e}")

    def cambiar_formato(self, event=None):
        guardar_ultimo_formato(self.formato_var.get())

    # ==========================================
    # LÓGICA DE LA BANDEJA DEL SISTEMA
    # ==========================================
    def ocultar_ventana(self):
        self.root.withdraw()
        try: image = Image.open(resource_path("Mei.ico"))
        except: image = Image.new('RGB', (64, 64), color=(0, 0, 0))

        menu = pystray.Menu(
            pystray.MenuItem('Abrir', self.mostrar_ventana, default=True),
            pystray.MenuItem('Pausar', self.pausar_desde_bandeja, enabled=lambda item: self.descargando and not self.pausado),
            pystray.MenuItem('Reanudar', self.reanudar_desde_bandeja, enabled=lambda item: self.descargando and self.pausado),
            pystray.MenuItem('Salir', self.salir_programa)
        )

        self.icono_bandeja = pystray.Icon("MeisPlayer", image, self.texto_tooltip, menu)
        self.enviar_notificacion("Mei's Player Minimizado", "El programa sigue ejecutándose en segundo plano.")
        threading.Thread(target=self.icono_bandeja.run, daemon=True).start()

    def mostrar_ventana(self, icon=None, item=None):
        if self.icono_bandeja:
            self.icono_bandeja.stop()
            self.icono_bandeja = None
        self.root.deiconify()

    def salir_programa(self, icon=None, item=None):
        if self.icono_bandeja: self.icono_bandeja.stop()
        self.root.destroy()

    def pausar_desde_bandeja(self, icon, item): self.root.after(0, self.forzar_pausa)
    def reanudar_desde_bandeja(self, icon, item): self.root.after(0, self.forzar_reanudar)
    def forzar_pausa(self):
        if not self.pausado: self.toggle_pausa()
    def forzar_reanudar(self):
        if self.pausado: self.toggle_pausa()

    def actualizar_tooltip(self):
        if self.descargando and self.progreso_total > 0:
            self.texto_tooltip = f"Descargando: {self.progreso_actual}/{self.progreso_total}"
        else:
            self.texto_tooltip = "Mei's Player - En espera"
        
        if self.icono_bandeja:
            self.icono_bandeja.title = self.texto_tooltip
            self.icono_bandeja.update_menu()
    # ==========================================

    def cargar_ultima_busqueda(self):
        if os.path.exists(self.ruta_cache):
            try:
                with open(self.ruta_cache, 'r', encoding='utf-8') as f:
                    self.songs = json.load(f)
                self.actualizar_lista_visual(self.songs)
                self.actualizar_estado(f"Se cargaron {len(self.songs)} canciones de la búsqueda anterior.")
            except Exception as e:
                self.actualizar_estado(f"Error al cargar caché: {e}")

    def guardar_busqueda(self):
        try:
            with open(self.ruta_cache, 'w', encoding='utf-8') as f:
                json.dump(self.songs, f, ensure_ascii=False, indent=4)
        except Exception as e: print(f"No se pudo guardar la caché: {e}")

    def limpiar_busqueda(self):
        if not self.songs: return
        if messagebox.askyesno("Limpiar", "¿Estás seguro de que deseas borrar la búsqueda actual?"):
            self._destruir_filas_montadas()
            self.songs = []
            self.items_ui = []
            self._cancelar_desplazamiento_suave()
            self.canvas.yview_moveto(0)
            self._actualizar_region_desplazamiento()
            self.url_entry.delete(0, tk.END)
            if os.path.exists(self.ruta_cache):
                try: os.remove(self.ruta_cache)
                except: pass
            self.actualizar_estado("Búsqueda limpiada.", "")

    def cambiar_api_keys(self):
        respuesta = messagebox.askyesno("Cambiar API Keys", "¿Estás seguro de que deseas cambiar tus llaves de API?\nSe cerrará la aplicación y se te pedirán nuevas llaves al abrirla de nuevo.")
        if respuesta:
            config_path = obtener_ruta_config()
            if os.path.exists(config_path):
                try:
                    os.remove(config_path)
                    self.salir_programa()
                    import Main
                    Main.iniciar_app()
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo borrar el archivo de configuración: {e}")

    def toggle_pausa(self):
        self.pausado = not self.pausado
        if self.pausado:
            self.btn_pausar.config(text="Reanudar")
            self.actualizar_estado(texto_der="Pausado.")
        else:
            self.btn_pausar.config(text="Pausar")
            self.actualizar_estado(texto_der="Reanudado.")
        self.actualizar_tooltip()

    def iniciar_busqueda(self):
        url = self.url_entry.get().strip()
        if not url: return messagebox.showwarning("URL vacía", "Por favor, introduce una URL.")
        
        self.btn_buscar.config(state="disabled")
        self.btn_limpiar.config(state="disabled")
        threading.Thread(target=self._buscar_en_hilo, args=(url,), daemon=True).start()

    def _buscar_en_hilo(self, url):
        try:
            if "youtube.com" in url or "youtu.be" in url:
                self.root.after(0, self.actualizar_estado, "Obteniendo metadatos de YouTube...", "")
                canciones = self.downloader_yt.search_songs(url)
            else:
                self.root.after(0, self.actualizar_estado, "Buscando canciones en Spotify...", "")
                canciones = self.downloader_sp.search_songs(url)
            self.root.after(0, self._actualizar_lista_y_visual, canciones)
        except Exception as error:
            self.root.after(0, self._busqueda_fallida, error)

    def _busqueda_fallida(self, error):
        self.actualizar_estado(f"Error en la búsqueda: {error}", "")
        self.btn_buscar.config(state="normal")
        self.btn_limpiar.config(state="normal")

    def _actualizar_lista_y_visual(self, canciones):
        if not canciones:
            self.actualizar_estado("No se encontraron canciones.", "")
            self.btn_buscar.config(state="normal")
            self.btn_limpiar.config(state="normal")
            return

        self._destruir_filas_montadas()
        nuevas_canciones = list(canciones)
        nuevas_items = [self._crear_modelo_item(index) for index in range(len(nuevas_canciones))]
        self.songs = nuevas_canciones + self.songs
        self.items_ui = nuevas_items + self.items_ui
        for index, item in enumerate(self.items_ui):
            item['index'] = index
            
        self.actualizar_estado(f"Se cargaron {len(canciones)} canciones nuevas. Total: {len(self.songs)}", "")
        self._cancelar_desplazamiento_suave()
        self.canvas.yview_moveto(0)
        self._actualizar_region_desplazamiento()
        self.btn_buscar.config(state="normal")
        self.btn_limpiar.config(state="normal")
        self.guardar_busqueda()
        self.url_entry.delete(0, tk.END)

    def actualizar_lista_visual(self, canciones):
        self._destruir_filas_montadas()
        self.items_ui = [
            self._crear_modelo_item(index)
            for index in range(len(canciones))
        ]
        self._cancelar_desplazamiento_suave()
        self.canvas.yview_moveto(0)
        self._actualizar_region_desplazamiento()

    @staticmethod
    def _crear_modelo_item(index):
        return {
            'index': index,
            'selected': True,
            'state': 'pending',
            'frame': None,
            'var_check': None,
            'progress': None,
            'canvas_id': None,
        }

    def crear_fila_visual(self, index, song, item_data):
        paleta = self._theme
        row = tk.Frame(self.canvas, bg=paleta["background"], pady=2, padx=5, height=ROW_HEIGHT - 4)
        row.pack_propagate(False)
        canvas_id = self.canvas.create_window(
            (0, index * ROW_HEIGHT),
            window=row,
            anchor="nw",
            width=max(1, self.canvas.winfo_width()),
            height=ROW_HEIGHT,
            tags=("song-row",),
        )
        
        # Checkbox simulado
        var_check = tk.BooleanVar(value=item_data['selected'])
        chk = tk.Checkbutton(
            row,
            variable=var_check,
            bg=paleta["background"],
            activebackground=paleta["hover"],
            selectcolor=paleta["field"],
            fg=paleta["foreground"],
            command=lambda: item_data.update(selected=var_check.get()),
        )
        chk.pack(side="left", padx=(5, 10))
        
        # Carátula (Placeholder mientras carga)
        cover_frame = tk.Frame(row, bg=paleta["background"], width=48, height=48)
        cover_frame.pack_propagate(False)
        cover_frame.pack(side="left", padx=(0, 10))
        lbl_img = tk.Label(cover_frame, bg=paleta["background"])
        lbl_img.pack(fill="both", expand=True)
        
        # Datos de la canción
        frame_info = tk.Frame(row, bg=paleta["background"])
        frame_info.pack(side="left", fill="x", expand=True)
        
        lbl_titulo = tk.Label(frame_info, text=song['name'], font=("Helvetica", 11, "bold"), bg=paleta["background"], fg=paleta["foreground"], anchor="w")
        lbl_titulo.pack(fill="x")
        
        frame_metadata = tk.Frame(frame_info, bg=paleta["background"])
        frame_metadata.pack(fill="x")
        lbl_artista = tk.Label(frame_metadata, text=song['artist'], font=("Helvetica", 9), bg=paleta["background"], fg=paleta["secondary"], anchor="w")
        lbl_artista._mei_theme_role = "secondary"
        lbl_artista.pack(side="left")
        
        lbl_duracion = tk.Label(frame_metadata, text=song['duration_str'], bg=paleta["background"], fg=paleta["secondary"])
        lbl_duracion._mei_theme_role = "secondary"
        lbl_duracion.pack(side="left", padx=(8, 0))
        
        # Estado de descarga
        barra_progreso = DownloadProgressBar(row)
        barra_progreso.pack(side="left", padx=10)
        if item_data['state'] == "downloading":
            barra_progreso.start()
        elif item_data['state'] == "completed":
            barra_progreso.complete()
        elif item_data['state'] == "error":
            barra_progreso.fail()
        
        # Guardamos las referencias para actualizarlas luego
        item_data.update({
            'frame': row, 'var_check': var_check, 'progress': barra_progreso,
            'lbl_img': lbl_img, 'index': index, 'canvas_id': canvas_id,
            'song_url': song.get('cover_url')
        })
        self.items_ui[index] = item_data
        self._visible_rows[index] = item_data

        # Efecto Hover (Marco al pasar el mouse)
        def cambiar_fondo(color):
            pendientes = [row]
            while pendientes:
                widget = pendientes.pop()
                if isinstance(widget, DownloadProgressBar):
                    widget.set_background(color)
                elif isinstance(widget, tk.Canvas):
                    widget.configure(bg=color)
                elif isinstance(widget, (tk.Frame, tk.Label, tk.Checkbutton)):
                    widget.configure(bg=color)
                    if isinstance(widget, tk.Checkbutton):
                        widget.configure(activebackground=color)
                pendientes.extend(widget.winfo_children())

        def on_enter(_event):
            row.config(highlightbackground=self._theme["outline"], highlightthickness=1)
            cambiar_fondo(self._theme["hover"])

        def on_leave(_event):
            row.config(highlightbackground=self._theme["background"], highlightthickness=0)
            cambiar_fondo(self._theme["background"])
        
        row.bind("<Enter>", on_enter)
        row.bind("<Leave>", on_leave)
        # Propagamos el evento hover a los hijos para que no parpadee
        for child in row.winfo_children():
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)
        barra_progreso.bind("<Enter>", on_enter)
        barra_progreso.bind("<Leave>", on_leave)
        for child in frame_info.winfo_children():
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)
        for child in frame_metadata.winfo_children():
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)

        titulo_original = song['name']
        fuente_titulo = tkfont.Font(root=self.root, font=lbl_titulo.cget("font"))

        def ajustar_titulo(_event=None):
            ancho = frame_info.winfo_width()
            if ancho <= 1:
                return
            ancho_maximo = ancho / 2 - fuente_titulo.measure("00")
            if fuente_titulo.measure(titulo_original) <= ancho_maximo:
                lbl_titulo.config(text=titulo_original)
                return

            sufijo = "..."
            izquierda, derecha = 0, len(titulo_original)
            while izquierda < derecha:
                medio = (izquierda + derecha + 1) // 2
                if fuente_titulo.measure(titulo_original[:medio] + sufijo) <= ancho_maximo:
                    izquierda = medio
                else:
                    derecha = medio - 1
            lbl_titulo.config(text=titulo_original[:izquierda] + sufijo)

        frame_info.bind("<Configure>", ajustar_titulo)
        self.root.after_idle(ajustar_titulo)

        # Descargar carátula asíncronamente
        if song.get('cover_url'):
            def actualizar_img(ruta_local):
                if ruta_local:
                    def aplicar_imagen():
                        if not lbl_img.winfo_exists():
                            return
                        img_tk = crear_imagen_tk(ruta_local, (48, 48))
                        if img_tk:
                            lbl_img.config(image=img_tk)
                            lbl_img.image = img_tk # Evitar Garbage Collector

                    self.root.after(0, aplicar_imagen)
            descargar_caratula(song['cover_url'], actualizar_img)

    def toggle_all(self):
        nuevo_estado = not self.items_ui[0]['selected'] if self.items_ui else False
        for item in self.items_ui:
            item['selected'] = nuevo_estado
            if item['var_check'] is not None:
                item['var_check'].set(nuevo_estado)

    def iniciar_descarga(self):
        canciones, ui_items = [], []
        for item in self.items_ui:
            if item['selected']:
                canciones.append(self.songs[item['index']])
                ui_items.append(item)

        if not canciones: return messagebox.showinfo("Selección", "Marca al menos una canción.")

        carpeta = filedialog.askdirectory(title="Selecciona la carpeta", initialdir=self.ultima_ruta)
        if not carpeta: return
        self.ultima_ruta = carpeta
        guardar_ultima_carpeta(carpeta)

        self.descargando = True
        self.pausado = False
        self.progreso_total = len(canciones)
        self.progreso_actual = 0
        
        self.btn_descargar.config(state="disabled")
        self.btn_buscar.config(state="disabled")
        self.btn_limpiar.config(state="disabled")
        self.btn_pausar.config(state="normal", text="Pausar")
        self.scrollbar.state(["disabled"])
        
        self.actualizar_tooltip()
        
        formato = self.formato_var.get()
        threading.Thread(target=self._descargar_lote_en_hilo, args=(canciones, ui_items, formato, carpeta), daemon=True).start()

    def _descargar_lote_en_hilo(self, canciones, ui_items, formato, carpeta_destino):
        total = len(canciones)
        exitos, fallos = 0, 0

        for idx, (cancion, ui_item) in enumerate(zip(canciones, ui_items)):
            while self.pausado:
                time.sleep(1) 

            self.progreso_actual = idx + 1
            
            texto_izq = f"[{self.progreso_actual}/{total}] {cancion['name']}"
            self.root.after(0, self.actualizar_estado, texto_izq, None)
            self.root.after(0, self._actualizar_estado_ui, ui_item, "Descargando...")
            self.root.after(0, self._centrar_cancion_en_lista, ui_item)
            
            try:
                if "youtube.com" in cancion['url'] or "youtu.be" in cancion['url']:
                    path = self.downloader_yt.download_song(cancion, formato, carpeta_destino)
                else:
                    path = self.downloader_sp.download_song(cancion, formato, carpeta_destino)
            except Exception as error:
                print(f"Error al descargar '{cancion['name']}': {error}")
                path = None
            
            if path:
                exitos += 1
                self.root.after(0, self._actualizar_estado_ui, ui_item, "Descargado", True)
            else:
                fallos += 1
                self.root.after(0, self._actualizar_estado_ui, ui_item, "Error", False)

            self.root.after(0, self.actualizar_tooltip)

        self.root.after(0, self._descarga_terminada, exitos, fallos)

    def _centrar_cancion_en_lista(self, ui_item):
        if not self.descargando or not self.songs:
            return
        total, viewport, scrollable_height = self._get_scroll_metrics()
        if total <= 0 or scrollable_height <= 0:
            return
        self._cancelar_desplazamiento_suave()
        centro_fila = ui_item["index"] * ROW_HEIGHT + ROW_HEIGHT / 2
        posicion = min(max(centro_fila - viewport / 2, 0), scrollable_height)
        self.canvas.yview_moveto(posicion / total)

    def _actualizar_estado_ui(self, ui_item, estado, desmarcar=False):
        state_by_label = {
            "Descargando...": "downloading",
            "Descargado": "completed",
            "Error": "error",
        }
        ui_item['state'] = state_by_label[estado]
        progress = ui_item['progress']
        if estado == "Descargando...":
            if progress is not None:
                progress.start()
        elif estado == "Descargado":
            if progress is not None:
                progress.complete()
        elif estado == "Error":
            if progress is not None:
                progress.fail()
        if desmarcar:
            ui_item['selected'] = False
            if ui_item['var_check'] is not None:
                ui_item['var_check'].set(False)

    def _subir_fallidas_al_inicio(self):
        self._destruir_filas_montadas()
        entradas = list(zip(self.songs, self.items_ui))
        entradas.sort(key=lambda entrada: entrada[1]["state"] != "error")
        self.songs = [cancion for cancion, _item in entradas]
        self.items_ui = [item for _cancion, item in entradas]
        for index, item in enumerate(self.items_ui):
            item['index'] = index

    def _descarga_terminada(self, exitos, fallos):
        self.descargando = False
        self.progreso_actual = 0
        self.progreso_total = 0
        
        self.btn_descargar.config(state="normal")
        self.btn_buscar.config(state="normal")
        self.btn_limpiar.config(state="normal")
        self.btn_pausar.config(state="disabled", text="Pausar")
        self.scrollbar.state(["!disabled"])
        if fallos:
            self._subir_fallidas_al_inicio()
        self._cancelar_desplazamiento_suave()
        self.canvas.yview_moveto(0)
        self._actualizar_region_desplazamiento()
        if fallos:
            self.guardar_busqueda()
        
        self.actualizar_estado("Proceso finalizado.", f"{exitos} exitosas, {fallos} fallidas.")
        self.actualizar_tooltip()
        
        if fallos > 0:
            self.enviar_notificacion("Descarga Finalizada", f"Se procesaron {exitos} canciones.\nHubo {fallos} errores.")
        else:
            self.enviar_notificacion("Descarga Finalizada", f"¡Todas las {exitos} canciones se descargaron correctamente!")