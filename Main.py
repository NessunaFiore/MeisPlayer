# Main.py
import tkinter as tk
import os
from Downloader import obtener_ruta_config
from VentanaConfig import ConfigApp
from VentanaPrincipal import MusicApp

def iniciar_app():
    config_path = obtener_ruta_config()
    
    if not os.path.exists(config_path):
        root_config = tk.Tk()
        app_config = ConfigApp(root_config, on_save_callback=abrir_principal)
        root_config.mainloop()
    else:
        abrir_principal()

def abrir_principal():
    root_main = tk.Tk()
    app_main = MusicApp(root_main)
    root_main.mainloop()

if __name__ == "__main__":
    iniciar_app()