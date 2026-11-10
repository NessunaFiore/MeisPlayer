import json
import os
import sys
import threading
import time

from winotify import Notification, audio
from PySide6.QtCore import (
    QObject,
    QSize,
    Qt,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtGui import (
    QAction,
    QIcon,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSystemTrayIcon,
)

from Downloader import (
    MusicDownloader,
    guardar_ultima_carpeta,
    guardar_ultimo_formato,
    obtener_ultima_carpeta,
)
from DownloaderYT import MusicDownloaderYT
from VentanaConfig import ConfigApp
from ui.styles import (
    THEME_DARK,
    aplicar_barra_titulo_oscura,
    cargar_pixmap,
    descargar_caratula,
    resource_path,
)
from ui.interfaz_principal import UiVentanaPrincipal


class UiDispatcher(QObject):
    requested = Signal(object, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.requested.connect(
            self._execute,
            Qt.ConnectionType.QueuedConnection,
        )

    @Slot(object, object)
    def _execute(self, callback, args):
        callback(*args)

    def post(self, callback, *args):
        self.requested.emit(callback, args)


class MusicApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mei's Player")
        self.resize(1040, 740)
        self.setMinimumSize(900, 640)
        self._centrado_inicial = False
        self._theme = dict(THEME_DARK)
        self._force_exit = False
        self.icon_path = resource_path(os.path.join("recursos", "imagenes", "Mei.ico"))
        if os.path.exists(self.icon_path):
            self.setWindowIcon(QIcon(self.icon_path))

        self._dispatcher = UiDispatcher(self)
        self.downloader_sp = MusicDownloader()
        self.downloader_yt = MusicDownloaderYT()
        self.songs = []
        self.items_ui = []
        self.ultima_ruta = obtener_ultima_carpeta()
        self.pausado = False
        self.descargando = False
        self._stop_download_event = threading.Event()
        self.progreso_actual = 0
        self.progreso_total = 0

        if getattr(sys, "frozen", False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        self.ruta_cache = os.path.join(base_path, "ultima_busqueda.json")

        self._create_widgets()
        self._create_tray_icon()
        QTimer.singleShot(0, lambda: aplicar_barra_titulo_oscura(self))
        self._progress_timer = QTimer(self)
        self._progress_timer.setInterval(100)
        self._progress_timer.timeout.connect(self.list_view.viewport().update)
        QTimer.singleShot(100, self.cargar_ultima_busqueda)

    def _create_widgets(self):
        self.ui = UiVentanaPrincipal(self)
        self.ui.setup_ui()

    def _select_page(self, page_index):
        self.page_stack.setCurrentIndex(page_index)
        self.nav_buttons[page_index].setChecked(True)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._centrado_inicial:
            self._centrado_inicial = True
            QTimer.singleShot(0, self._centrar_en_pantalla)

    def _centrar_en_pantalla(self):
        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(available.center())
        self.move(frame_geometry.topLeft())

    def _create_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        if os.path.exists(self.icon_path):
            self.tray_icon.setIcon(QIcon(self.icon_path))
        self.tray_icon.setToolTip("Mei's Player")
        menu = QMenu(self)
        self.action_show = QAction("Abrir", self)
        self.action_show.triggered.connect(self.mostrar_ventana)
        menu.addAction(self.action_show)
        self.action_pause = QAction("Pausar", self)
        self.action_pause.triggered.connect(self.forzar_pausa)
        menu.addAction(self.action_pause)
        self.action_resume = QAction("Reanudar", self)
        self.action_resume.triggered.connect(self.forzar_reanudar)
        menu.addAction(self.action_resume)
        menu.addSeparator()
        action_exit = QAction("Salir", self)
        action_exit.triggered.connect(self.salir_programa)
        menu.addAction(action_exit)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._tray_activated)
        self._update_tray_actions()

    def _tray_activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.mostrar_ventana()

    def _request_cover(self, index, url):
        def loaded(path):
            self._dispatcher.post(self._apply_cover, index, url, path)

        descargar_caratula(url, loaded)

    def _apply_cover(self, index, url, path):
        if path is None or index >= len(self.songs):
            return
        if self.songs[index].get("cover_url") != url:
            return
        pixmap = cargar_pixmap(path, QSize(48, 48))
        if pixmap.isNull():
            return
        self.items_ui[index]["cover_pixmap"] = pixmap
        self.model.refresh_row(index)

    def actualizar_estado(self, texto_izq=None, texto_der=None):
        if texto_izq is not None:
            self.lbl_estado_izq.setText(texto_izq)
        if texto_der is not None:
            self.lbl_estado_der.setText(texto_der)

    def _actualizar_contador_canciones(self):
        total = len(self.songs)
        nombre = "canción" if total == 1 else "canciones"
        self.lbl_lista_count.setText(f"{total} {nombre}")

    def enviar_notificacion(self, titulo, mensaje):
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon.showMessage(
                titulo,
                mensaje,
                QSystemTrayIcon.MessageIcon.Information,
                5000,
            )

    def notificar_minimizado(self):
        if not os.path.isfile(self.icon_path):
            print(f"No se encontró el icono para la notificación: {self.icon_path}")
            return

        try:
            notification = Notification(
                app_id="Mei's Player",
                title="Mei's Player minimizado",
                msg="El programa sigue ejecutándose en segundo plano.",
                icon=self.icon_path,
            )
            notification.set_audio(audio.Default, loop=False)
            notification.show()
        except Exception as error:
            print(f"No se pudo mostrar la notificación de minimizado: {error}")

    def cambiar_formato(self, formato):
        guardar_ultimo_formato(formato)

    def ocultar_ventana(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.salir_programa()
            return
        self.hide()
        if not self.tray_icon.isVisible():
            self.tray_icon.show()
            self.notificar_minimizado()
        self.actualizar_tooltip()

    def mostrar_ventana(self):
        self.tray_icon.show()
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def salir_programa(self):
        self._force_exit = True
        self.tray_icon.hide()
        self.close()
        QApplication.instance().quit()

    def forzar_pausa(self):
        if self.descargando and not self.pausado:
            self.toggle_pausa()

    def forzar_reanudar(self):
        if self.descargando and self.pausado:
            self.toggle_pausa()

    def _update_tray_actions(self):
        stop_requested = self._stop_download_event.is_set()
        self.action_pause.setEnabled(
            self.descargando and not self.pausado and not stop_requested
        )
        self.action_resume.setEnabled(
            self.descargando and self.pausado and not stop_requested
        )

    def actualizar_tooltip(self):
        if self.descargando and self.progreso_total > 0:
            tooltip = f"Descargando: {self.progreso_actual}/{self.progreso_total}"
        else:
            tooltip = "Mei's Player - En espera"
        self.tray_icon.setToolTip(tooltip)
        self._update_tray_actions()

    def cargar_ultima_busqueda(self):
        if os.path.exists(self.ruta_cache):
            try:
                with open(self.ruta_cache, "r", encoding="utf-8") as cache_file:
                    self.songs = json.load(cache_file)
                self.actualizar_lista_visual(self.songs)
                self.actualizar_estado(
                    f"Se cargaron {len(self.songs)} canciones de la búsqueda anterior."
                )
            except (OSError, ValueError) as error:
                self.actualizar_estado(f"Error al cargar caché: {error}")

    def guardar_busqueda(self):
        try:
            with open(self.ruta_cache, "w", encoding="utf-8") as cache_file:
                json.dump(self.songs, cache_file, ensure_ascii=False, indent=4)
        except OSError as error:
            print(f"No se pudo guardar la caché: {error}")

    def limpiar_busqueda(self):
        if not self.songs:
            return
        answer = QMessageBox.question(
            self,
            "Limpiar",
            "¿Estás seguro de que deseas borrar la búsqueda actual?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.songs = []
        self.items_ui = []
        self.model.set_records(self.songs, self.items_ui)
        self._actualizar_contador_canciones()
        self._actualizar_reportes()
        self.list_view.scrollToTop()
        try:
            if os.path.exists(self.ruta_cache):
                os.remove(self.ruta_cache)
        except OSError as error:
            QMessageBox.warning(
                self,
                "Error",
                f"No se pudo borrar la caché: {error}",
            )
        self.actualizar_estado("Búsqueda limpiada.", "")

    def cambiar_api_keys(self):
        answer = QMessageBox.question(
            self,
            "Cambiar API Keys",
            "¿Estás seguro de que deseas cambiar tus llaves de API?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self.config_window = ConfigApp(
            on_save_callback=self._credenciales_actualizadas,
            parent=self,
        )
        self.config_window.setWindowModality(Qt.WindowModality.WindowModal)
        self.config_window.show()

    def _credenciales_actualizadas(self):
        try:
            self.downloader_sp = MusicDownloader()
        except Exception as error:
            QMessageBox.critical(
                self.config_window,
                "Error",
                f"No se pudo iniciar el backend con las nuevas llaves: {error}",
            )
            self.show()
            return
        self.show()

    def toggle_pausa(self):
        if self._stop_download_event.is_set():
            return
        self.pausado = not self.pausado
        if self.pausado:
            self.btn_pausar.setText("Reanudar")
            self.actualizar_estado(texto_der="Pausado.")
        else:
            self.btn_pausar.setText("Pausar")
            self.actualizar_estado(texto_der="Reanudado.")
        self.actualizar_tooltip()

    def iniciar_busqueda(self):
        url = self.url_entry.text().strip()
        if not url:
            QMessageBox.warning(self, "URL vacía", "Por favor, introduce una URL.")
            return
        self.btn_buscar.setEnabled(False)
        self.btn_limpiar.setEnabled(False)
        threading.Thread(
            target=self._buscar_en_hilo,
            args=(url,),
            daemon=True,
        ).start()

    def _buscar_en_hilo(self, url):
        try:
            if "youtube.com" in url or "youtu.be" in url:
                self._dispatcher.post(
                    self.actualizar_estado,
                    "Obteniendo metadatos de YouTube...",
                    "",
                )
                canciones = self.downloader_yt.search_songs(url)
            else:
                self._dispatcher.post(
                    self.actualizar_estado,
                    "Buscando canciones en Spotify...",
                    "",
                )
                canciones = self.downloader_sp.search_songs(url)
            self._dispatcher.post(self._actualizar_lista_y_visual, canciones)
        except Exception as error:
            self._dispatcher.post(self._busqueda_fallida, error)

    def _busqueda_fallida(self, error):
        self.actualizar_estado(f"Error en la búsqueda: {error}", "")
        self.btn_buscar.setEnabled(True)
        self.btn_limpiar.setEnabled(True)

    def _crear_modelo_item(self, index, song=None):
        song = song if song is not None else self.songs[index]
        error_reason = song.get("_download_error")
        return {
            "index": index,
            "selected": True,
            "state": "error" if error_reason else "pending",
            "started_at": None,
            "cover_pixmap": None,
            "cover_requested": False,
            "error_reason": error_reason,
        }

    def _actualizar_lista_y_visual(self, canciones):
        if not canciones:
            self.actualizar_estado("No se encontraron canciones.", "")
            self.btn_buscar.setEnabled(True)
            self.btn_limpiar.setEnabled(True)
            return

        nuevas_canciones = list(canciones)
        nuevas_items = [
            self._crear_modelo_item(index, song)
            for index, song in enumerate(nuevas_canciones)
        ]
        self.songs = nuevas_canciones + self.songs
        self.items_ui = nuevas_items + self.items_ui
        for index, item in enumerate(self.items_ui):
            item["index"] = index

        self.model.set_records(self.songs, self.items_ui)
        self._actualizar_contador_canciones()
        self._actualizar_reportes()
        self.actualizar_estado(
            f"Se cargaron {len(canciones)} canciones nuevas. Total: {len(self.songs)}",
            "",
        )
        self.list_view.scrollToTop()
        self.btn_buscar.setEnabled(True)
        self.btn_limpiar.setEnabled(True)
        self.guardar_busqueda()
        self.url_entry.clear()

    def actualizar_lista_visual(self, canciones):
        self.items_ui = [
            self._crear_modelo_item(index)
            for index in range(len(canciones))
        ]
        self.model.set_records(self.songs, self.items_ui)
        self._actualizar_contador_canciones()
        self._actualizar_reportes()
        self.list_view.scrollToTop()

    def toggle_all(self):
        nuevo_estado = not self.items_ui[0]["selected"] if self.items_ui else False
        for item in self.items_ui:
            item["selected"] = nuevo_estado
        self.model.refresh_all()

    def iniciar_descarga(self):
        canciones, ui_items = [], []
        for item in self.items_ui:
            if item["selected"]:
                canciones.append(self.songs[item["index"]])
                ui_items.append(item)

        if not canciones:
            QMessageBox.information(
                self,
                "Selección",
                "Marca al menos una canción.",
            )
            return

        carpeta = QFileDialog.getExistingDirectory(
            self,
            "Selecciona la carpeta",
            self.ultima_ruta,
        )
        if not carpeta:
            return
        self.ultima_ruta = carpeta
        guardar_ultima_carpeta(carpeta)

        self.descargando = True
        self.pausado = False
        self._stop_download_event.clear()
        self.progreso_total = len(canciones)
        self.progreso_actual = 0
        self.btn_descargar.setEnabled(False)
        self.btn_buscar.setEnabled(False)
        self.btn_limpiar.setEnabled(False)
        self.btn_pausar.setEnabled(True)
        self.btn_pausar.setText("Pausar")
        self.btn_detener.setEnabled(True)
        self.btn_detener.setText("Detener")
        self.scrollbar.setEnabled(False)
        self._progress_timer.start()
        self.actualizar_tooltip()

        threading.Thread(
            target=self._descargar_lote_en_hilo,
            args=(canciones, ui_items, self.combo_formato.currentText(), carpeta),
            daemon=True,
        ).start()

    def _descargar_lote_en_hilo(self, canciones, ui_items, formato, carpeta_destino):
        total = len(canciones)
        exitos, fallos = 0, 0
        detenida = False
        for idx, (cancion, ui_item) in enumerate(zip(canciones, ui_items)):
            while self.pausado and not self._stop_download_event.is_set():
                time.sleep(0.1)
            if self._stop_download_event.is_set():
                detenida = True
                break

            self.progreso_actual = idx + 1
            texto_izq = f"[{self.progreso_actual}/{total}] {cancion['name']}"
            self._dispatcher.post(self.actualizar_estado, texto_izq, None)
            self._dispatcher.post(self._actualizar_estado_ui, ui_item, "Descargando...")
            self._dispatcher.post(self._centrar_cancion_en_lista, ui_item)

            downloader = (
                self.downloader_yt
                if "youtube.com" in cancion["url"] or "youtu.be" in cancion["url"]
                else self.downloader_sp
            )
            try:
                path = downloader.download_song(
                    cancion,
                    formato,
                    carpeta_destino,
                )
            except Exception as error:
                print(f"Error al descargar '{cancion['name']}': {error}")
                path = None
                error_reason = str(error)
            else:
                error_reason = (
                    getattr(downloader, "last_error", None)
                    or "El descargador no indicó el motivo del fallo."
                )

            if path:
                exitos += 1
                self._dispatcher.post(
                    self._actualizar_estado_ui,
                    ui_item,
                    "Descargado",
                    True,
                )
            else:
                fallos += 1
                self._dispatcher.post(
                    self._actualizar_estado_ui,
                    ui_item,
                    "Error",
                    False,
                    error_reason,
                )
            self._dispatcher.post(self.actualizar_tooltip)

        if self._stop_download_event.is_set():
            detenida = True
        self._dispatcher.post(self._descarga_terminada, exitos, fallos, detenida)

    def detener_descarga(self):
        if not self.descargando or self._stop_download_event.is_set():
            return
        self._stop_download_event.set()
        self.pausado = False
        self.btn_pausar.setEnabled(False)
        self.btn_detener.setEnabled(False)
        self.btn_detener.setText("Deteniendo...")
        self.actualizar_estado(
            texto_der="Se detendrá al terminar la canción actual."
        )
        self.actualizar_tooltip()

    def _centrar_cancion_en_lista(self, ui_item):
        if not self.descargando or not self.songs:
            return
        index = self.model.index(ui_item["index"], 0)
        self.list_view.scrollTo(
            index,
            QAbstractItemView.ScrollHint.PositionAtCenter,
        )

    def _actualizar_estado_ui(
        self,
        ui_item,
        estado,
        desmarcar=False,
        error_reason=None,
    ):
        state_by_label = {
            "Descargando...": "downloading",
            "Descargado": "completed",
            "Error": "error",
        }
        ui_item["state"] = state_by_label[estado]
        ui_item["started_at"] = time.monotonic() if estado == "Descargando..." else None
        song = self.songs[ui_item["index"]]
        if estado == "Error":
            ui_item["error_reason"] = (
                error_reason or "El descargador no indicó el motivo del fallo."
            )
            song["_download_error"] = ui_item["error_reason"]
        elif estado == "Descargado":
            ui_item["error_reason"] = None
            song.pop("_download_error", None)
        elif estado == "Descargando...":
            ui_item["error_reason"] = None
            song.pop("_download_error", None)
        if desmarcar:
            ui_item["selected"] = False
        self.model.refresh_row(ui_item["index"])
        self._actualizar_reportes()

    def _actualizar_reportes(self):
        failed_items = [
            (self.songs[item["index"]], item)
            for item in self.items_ui
            if item["state"] == "error"
        ]
        self.reportes_page.set_failures(failed_items)

    def _subir_fallidas_al_inicio(self):
        entradas = list(zip(self.songs, self.items_ui))
        entradas.sort(key=lambda entrada: entrada[1]["state"] != "error")
        self.songs = [song for song, _ in entradas]
        self.items_ui = [item for _, item in entradas]
        for index, item in enumerate(self.items_ui):
            item["index"] = index
        self.model.set_records(self.songs, self.items_ui)

    def _descarga_terminada(self, exitos, fallos, detenida=False):
        self.descargando = False
        self.pausado = False
        self.progreso_actual = 0
        self.progreso_total = 0
        self._progress_timer.stop()
        self.btn_descargar.setEnabled(True)
        self.btn_buscar.setEnabled(True)
        self.btn_limpiar.setEnabled(True)
        self.btn_pausar.setEnabled(False)
        self.btn_pausar.setText("Pausar")
        self.btn_detener.setEnabled(False)
        self.btn_detener.setText("Detener")
        self._stop_download_event.clear()
        self.scrollbar.setEnabled(True)
        if fallos:
            self._subir_fallidas_al_inicio()
        self.list_view.scrollToTop()
        self.guardar_busqueda()

        estado = "Descarga detenida." if detenida else "Proceso finalizado."
        self.actualizar_estado(estado, f"{exitos} exitosas, {fallos} fallidas.")
        self.actualizar_tooltip()
        if detenida:
            return
        if fallos:
            self.enviar_notificacion(
                "Descarga finalizada",
                f"Se procesaron {exitos} canciones.\nHubo {fallos} errores.",
            )
        else:
            self.enviar_notificacion(
                "Descarga finalizada",
                f"¡Todas las {exitos} canciones se descargaron correctamente!",
            )

    def closeEvent(self, event):
        if self._force_exit:
            event.accept()
            return
        self.ocultar_ventana()
        event.ignore()
