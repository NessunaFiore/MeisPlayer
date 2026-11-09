# VentanaPrincipal.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import os
import sys
from Downloader import MusicDownloader, obtener_ruta_config

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def centrar_ventana(ventana, ancho, alto):
    ventana.update_idletasks()
    x = (ventana.winfo_screenwidth() // 2) - (ancho // 2)
    y = (ventana.winfo_screenheight() // 2) - (alto // 2)
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

class MusicApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mei´s Player")
        centrar_ventana(self.root, 850, 580)
        
        try: self.root.iconbitmap(resource_path("Mei.ico"))
        except: pass
        
        self.downloader = MusicDownloader()
        self.songs = []
        self.ultima_ruta = os.path.expanduser("~")
        
        self.pausado = False
        self.descargando = False

        # --- Frame superior ---
        frame_top = ttk.Frame(root, padding="10")
        frame_top.pack(fill="x")

        ttk.Label(frame_top, text="URL:").pack(side="left", padx=(0, 5))
        self.url_entry = ttk.Entry(frame_top, width=60)
        self.url_entry.pack(side="left", expand=True, fill="x", padx=(0, 5))
        self.btn_buscar = ttk.Button(frame_top, text="Buscar", command=self.iniciar_busqueda)
        self.btn_buscar.pack(side="left")

        # --- Frame central ---
        frame_list = ttk.Frame(root, padding="10")
        frame_list.pack(fill="both", expand=True)

        columns = ("Check", "#", "Título", "Artista", "Álbum", "Dur", "Año", "Estado")
        self.tree = ttk.Treeview(frame_list, columns=columns, show="headings", height=12)
        
        self.tree.heading("Check", text="✔")
        self.tree.heading("#", text="#")
        self.tree.heading("Título", text="Título")
        self.tree.heading("Artista", text="Artista")
        self.tree.heading("Álbum", text="Álbum")
        self.tree.heading("Dur", text="Dur")
        self.tree.heading("Año", text="Año")
        self.tree.heading("Estado", text="Estado")
        
        self.tree.column("Check", width=35, anchor="center")
        self.tree.column("#", width=40, anchor="center")
        self.tree.column("Título", width=200)
        self.tree.column("Artista", width=100)
        self.tree.column("Álbum", width=120)
        self.tree.column("Dur", width=45, anchor="center")
        self.tree.column("Año", width=45, anchor="center")
        self.tree.column("Estado", width=150, anchor="center")
        
        self.tree.configure(selectmode="extended")
        scrollbar = ttk.Scrollbar(frame_list, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<Button-1>", self.toggle_check)

        # --- Frame inferior ---
        frame_bottom = ttk.Frame(root, padding="10")
        frame_bottom.pack(fill="x")

        ttk.Button(frame_bottom, text="Marcar Todo", command=self.toggle_all).pack(side="left", padx=(0, 10))

        ttk.Label(frame_bottom, text="Formato:").pack(side="left", padx=(0, 5))
        self.formato_var = tk.StringVar(value="mp3")
        self.combo_formato = ttk.Combobox(frame_bottom, textvariable=self.formato_var, values=["mp3", "m4a", "flac", "wav"], state="readonly", width=6)
        self.combo_formato.pack(side="left", padx=(0, 10))

        self.btn_descargar = ttk.Button(frame_bottom, text="Descargar Seleccionadas", command=self.iniciar_descarga)
        self.btn_descargar.pack(side="left", padx=(0, 5))

        self.btn_pausar = ttk.Button(frame_bottom, text="Pausar", command=self.toggle_pausa, state="disabled")
        self.btn_pausar.pack(side="left")

        # --- Botón para cambiar API Keys ---
        self.btn_api = ttk.Button(frame_bottom, text="Cambiar API Keys", command=self.cambiar_api_keys)
        self.btn_api.pack(side="right")

        # --- Frame de Logs ---
        frame_log = ttk.Frame(root, padding="10")
        frame_log.pack(fill="x", side="bottom")
        self.log_text = tk.Text(frame_log, height=4, state="disabled", bg="#f0f0f0")
        self.log_text.pack(fill="x")

    def log(self, mensaje):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, mensaje + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def cambiar_api_keys(self):
        respuesta = messagebox.askyesno("Cambiar API Keys", "¿Estás seguro de que deseas cambiar tus llaves de API?\nSe cerrará la aplicación y se te pedirán nuevas llaves al abrirla de nuevo.")
        if respuesta:
            config_path = obtener_ruta_config()
            if os.path.exists(config_path):
                try:
                    os.remove(config_path)
                    self.root.destroy()
                    import Main
                    Main.iniciar_app()
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo borrar el archivo de configuración: {e}")

    def toggle_pausa(self):
        self.pausado = not self.pausado
        if self.pausado:
            self.btn_pausar.config(text="Reanudar")
            self.log("Pausando descarga, se podra reanudar al terminar la canción actual.")
        else:
            self.btn_pausar.config(text="Pausar")
            self.log("Reanudando descarga(s)...")

    def toggle_check(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == "#1":
                item = self.tree.identify_row(event.y)
                if item:
                    current_val = self.tree.item(item, "values")[0]
                    new_val = "☐" if current_val == "☑" else "☑"
                    values = list(self.tree.item(item, "values"))
                    values[0] = new_val
                    self.tree.item(item, values=values)

    def toggle_all(self):
        children = self.tree.get_children()
        if not children: return
        marcar = any(self.tree.item(i, "values")[0] == "☐" for i in children)
        nuevo_estado = "☑" if marcar else "☐"
        for item in children:
            values = list(self.tree.item(item, "values"))
            values[0] = nuevo_estado
            self.tree.item(item, values=values)

    def iniciar_busqueda(self):
        url = self.url_entry.get().strip()
        if not url: return messagebox.showwarning("URL vacía", "Por favor, introduce una URL.")
        
        self.log("Buscando canciones...")
        self.btn_buscar.config(state="disabled")
        threading.Thread(target=self._buscar_en_hilo, args=(url,), daemon=True).start()

    def _buscar_en_hilo(self, url):
        canciones = self.downloader.search_songs(url)
        self.root.after(0, self._actualizar_lista, canciones)

    def _actualizar_lista(self, canciones):
        for item in self.tree.get_children(): self.tree.delete(item)
        self.songs = canciones
        
        if not canciones:
            self.log("No se encontraron canciones.")
            self.btn_buscar.config(state="normal")
            return

        for i, song in enumerate(canciones):
            self.tree.insert("", "end", values=(
                "☐", i+1, song['name'], song['artist'], 
                song['album'], song['duration_str'], song['year'], "Pendiente"
            ))
        
        self.log(f"Se encontraron {len(canciones)} canciones. ¡Listas para descargar!")
        self.btn_buscar.config(state="normal")

    def iniciar_descarga(self):
        canciones, items = [], []
        for item in self.tree.get_children():
            if self.tree.item(item, "values")[0] == "☑":
                index = int(self.tree.item(item, "values")[1]) - 1
                canciones.append(self.songs[index])
                items.append(item)

        if not canciones: return messagebox.showinfo("Selección", "Marca al menos una canción.")

        carpeta = filedialog.askdirectory(title="Selecciona la carpeta", initialdir=self.ultima_ruta)
        if not carpeta: return
        self.ultima_ruta = carpeta

        self.descargando = True
        self.pausado = False
        self.btn_descargar.config(state="disabled")
        self.btn_buscar.config(state="disabled")
        self.btn_pausar.config(state="normal", text="Pausar")
        
        formato = self.formato_var.get()
        threading.Thread(target=self._descargar_lote_en_hilo, args=(canciones, items, formato, carpeta), daemon=True).start()

    def _descargar_lote_en_hilo(self, canciones, items, formato, carpeta_destino):
        total = len(canciones)
        self.root.after(0, self.log, f"Iniciando proceso de {total} canciones en: {carpeta_destino}")
        
        tiempo_estimado_seg = total * 2 
        minutos = tiempo_estimado_seg // 60
        self.root.after(0, self.log, f"Tiempo estimado de descarga: ~{minutos} minutos.")

        exitos, fallos = 0, 0

        for idx, (cancion, item_id) in enumerate(zip(canciones, items)):
            while self.pausado:
                time.sleep(1) 

            self.root.after(0, self._actualizar_estado_item, item_id, "Descargando...")
            
            path = self.downloader.download_song(cancion, formato, carpeta_destino)
            
            if path:
                exitos += 1
                self.root.after(0, self._desmarcar_item, item_id, "Listo / Ya existía")
            else:
                fallos += 1
                self.root.after(0, self._actualizar_estado_item, item_id, "Falló")
                
            progreso_msg = f"[{idx+1}/{total}] {cancion['name']}"
            self.root.after(0, self.log, progreso_msg)

        self.root.after(0, self._descarga_terminada, exitos, fallos)

    def _desmarcar_item(self, item_id, estado):
        values = list(self.tree.item(item_id, "values"))
        values[0] = "☐"
        values[7] = estado
        self.tree.item(item_id, values=values)
        self.tree.see(item_id)

    def _actualizar_estado_item(self, item_id, estado):
        values = list(self.tree.item(item_id, "values"))
        values[7] = estado
        self.tree.item(item_id, values=values)

    def _descarga_terminada(self, exitos, fallos):
        self.descargando = False
        self.btn_descargar.config(state="normal")
        self.btn_buscar.config(state="normal")
        self.btn_pausar.config(state="disabled", text="Pausar")
        
        self.log(f"--- Proceso finalizado: {exitos} exitosas, {fallos} fallidas ---")
        
        if fallos > 0:
            messagebox.showwarning("Descarga finalizada", f"Se procesaron {exitos} canciones.\n\nHubo {fallos} errores. Las fallidas quedaron marcadas para reintentar.")
        else:
            messagebox.showinfo("Descarga finalizada", "¡Todas las canciones se descargaron o ya existían!")