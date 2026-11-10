# VentanaConfig.py
import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import json
import webbrowser  
from PIL import Image, ImageTk
from Downloader import obtener_ruta_config
from styles import THEME_DARK, aplicar_barra_titulo_oscura, configurar_estilos_oscuro

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def centrar_ventana(ventana, ancho, alto):
    ventana.update_idletasks()
    x = (ventana.winfo_screenwidth() // 2) - (ancho // 2)
    y = (ventana.winfo_screenheight() // 2) - (alto // 2)
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

class ConfigApp:
    def __init__(self, root, on_save_callback):
        self.root = root
        self.root.title("Configuración Inicial - Mei's Player")
        configurar_estilos_oscuro(self.root)
        centrar_ventana(self.root, 420, 380)
        self.root.resizable(False, False)
        self.on_save_callback = on_save_callback
        self.root.after_idle(aplicar_barra_titulo_oscura, self.root)
        
        try: self.root.iconbitmap(resource_path("Mei.ico"))
        except: pass

        ttk.Label(root, text="¡Bienvenido a Mei's Player!", font=("Helvetica", 14, "bold")).pack(pady=10)
        ttk.Label(root, text="Para usar la app, necesitas tus propias llaves de Spotify.\nSi no sabes cómo obtenerlas, haz clic en el botón de Tutorial.", justify="center").pack(pady=5)

        frame_form = ttk.Frame(root, padding="20")
        frame_form.pack(fill="x")

        ttk.Label(frame_form, text="Client ID:").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_id = ttk.Entry(frame_form, width=40)
        self.entry_id.grid(row=0, column=1, pady=5)

        ttk.Label(frame_form, text="Client Secret:").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_secret = ttk.Entry(frame_form, width=40, show="*")
        self.entry_secret.grid(row=1, column=1, pady=5)

        frame_btn = ttk.Frame(root)
        frame_btn.pack(pady=20)

        ttk.Button(frame_btn, text="Ver Tutorial", command=self.mostrar_tutorial).pack(side="left", padx=10)
        ttk.Button(frame_btn, text="Guardar y Abrir App", command=self.guardar_config).pack(side="left", padx=10)

    def mostrar_tutorial(self):
        tut_win = tk.Toplevel(self.root)
        tut_win.title("Tutorial: Cómo obtener tus API Keys")
        configurar_estilos_oscuro(tut_win)
        centrar_ventana(tut_win, 800, 600)
        tut_win.after_idle(aplicar_barra_titulo_oscura, tut_win)
        
        try: tut_win.iconbitmap(resource_path("Mei.ico"))
        except: pass
        
        frame_bottom = ttk.Frame(tut_win, padding="10")
        frame_bottom.pack(side="bottom", fill="x")
        
        ttk.Button(frame_bottom, text="Cerrar Tutorial", command=tut_win.destroy).pack(side="left")

        frame_scroll = ttk.Frame(tut_win)
        frame_scroll.pack(side="top", fill="both", expand=True)

        canvas = tk.Canvas(
            frame_scroll,
            bg=THEME_DARK["background"],
            highlightthickness=0,
            bd=0,
        )
        scrollbar = ttk.Scrollbar(frame_scroll, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- IMÁGENES CAMBIADAS A .jpg ---
        pasos = [
            ("1. Ve al Spotify Developer Dashboard", "Inicia sesión con tu cuenta de Spotify y haz clic en 'Create app'.", "tutorial_1.jpg"),
            ("2. Configura tu app", "Llena los datos. En 'Redirect URIs' coloca exactamente: http://127.0.0.1:8080/callback\nHaz clic en 'Save' y luego copia tu Client ID y Client Secret.", "tutorial_2.jpg"),
            ("3. Pega tus llaves aquí", "Vuelve a esta ventana y pega el Client ID y el Client Secret en los recuadros correspondientes.", "tutorial_3.jpg")
        ]

        for i, (titulo, texto, img_nombre) in enumerate(pasos):
            ttk.Label(scrollable_frame, text=titulo, font=("Helvetica", 12, "bold")).pack(pady=(20, 5), anchor="w", padx=20)
            
            if i == 0:
                frame_link = ttk.Frame(scrollable_frame)
                frame_link.pack(pady=5, anchor="w", padx=20)
                
                ttk.Label(frame_link, text=texto + " Haz clic aquí: ").pack(side="left")
                
                link = tk.Label(
                    frame_link,
                    text="Spotify Developer Dashboard",
                    bg=THEME_DARK["background"],
                    fg="#8AB4F8",
                    cursor="hand2",
                    font=("Helvetica", 10, "underline"),
                )
                link.pack(side="left")
                link.bind("<Button-1>", lambda e: webbrowser.open_new("https://developer.spotify.com/dashboard"))
            else:
                ttk.Label(scrollable_frame, text=texto, justify="left").pack(pady=5, anchor="w", padx=20)
            
            # Imagen del paso
            try:
                img_path = resource_path(img_nombre)
                img = Image.open(img_path)
                img.thumbnail((700, 300))
                photo = ImageTk.PhotoImage(img)
                label_img = ttk.Label(scrollable_frame, image=photo)
                label_img.image = photo
                label_img.pack(pady=10)
            except Exception:
                ttk.Label(scrollable_frame, text=f"[Imagen no encontrada: {img_nombre}]", foreground="red").pack(pady=10)

    def guardar_config(self):
        client_id = self.entry_id.get().strip()
        client_secret = self.entry_secret.get().strip()

        if not client_id or not client_secret:
            messagebox.showwarning("Campos vacíos", "Por favor, introduce ambas llaves.")
            return

        config_path = obtener_ruta_config()
        config_data = {"CLIENT_ID": client_id, "CLIENT_SECRET": client_secret}
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)
            messagebox.showinfo("Configuración guardada", "Las llaves se han guardado correctamente.\nLa aplicación se iniciará ahora.")
            self.root.destroy()
            self.on_save_callback()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la configuración: {e}")