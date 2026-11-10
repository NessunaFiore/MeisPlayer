from PySide6.QtCore import (
    QAbstractListModel,
    QEvent,
    QModelIndex,
    QRect,
    QRectF,
    QSize,
    Qt,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QPushButton,
    QStackedWidget,
    QStyle,
    QStyledItemDelegate,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ui.acerca import AcercaPage
from ui.apoyar import ApoyarPage
from ui.configuracion import ConfiguracionPage
from ui.reportes import ReportesPage
from progress_bar import draw_progress_bar
from ui.styles import THEME_DARK, cargar_fuente_custom
from Downloader import obtener_ultimo_formato


ROW_HEIGHT = 64


class SongListModel(QAbstractListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.songs = []
        self.items = []

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.songs)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self.items):
            return None
        if role == Qt.ItemDataRole.CheckStateRole:
            return (
                Qt.CheckState.Checked
                if self.items[index.row()]["selected"]
                else Qt.CheckState.Unchecked
            )
        if role == Qt.ItemDataRole.UserRole:
            return self.songs[index.row()]
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if (
            role != Qt.ItemDataRole.CheckStateRole
            or not index.isValid()
            or index.row() >= len(self.items)
        ):
            return False
        self.items[index.row()]["selected"] = value == Qt.CheckState.Checked
        self.dataChanged.emit(
            index,
            index,
            [Qt.ItemDataRole.CheckStateRole],
        )
        return True

    def set_records(self, songs, items):
        self.beginResetModel()
        self.songs = songs
        self.items = items
        self.endResetModel()

    def refresh_row(self, row):
        if 0 <= row < len(self.items):
            index = self.index(row, 0)
            self.dataChanged.emit(
                index,
                index,
                [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.CheckStateRole],
            )

    def refresh_all(self):
        if self.items:
            self.dataChanged.emit(
                self.index(0, 0),
                self.index(len(self.items) - 1, 0),
                [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.CheckStateRole],
            )


class SongDelegate(QStyledItemDelegate):
    def __init__(self, request_cover, parent=None):
        super().__init__(parent)
        self.request_cover = request_cover

    def sizeHint(self, option, index):
        width = option.rect.width() if index.isValid() else 0
        return QSize(width, ROW_HEIGHT)

    def paint(self, painter, option, index):
        model = index.model()
        song = model.data(index, Qt.ItemDataRole.UserRole)
        if not song:
            return
        item = model.items[index.row()]
        row_rect = QRectF(option.rect.adjusted(3, 2, -3, -2))
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(
            QColor(THEME_DARK["outline"] if hovered else THEME_DARK["background"])
        )
        painter.setBrush(
            QColor(THEME_DARK["hover"] if hovered else THEME_DARK["background"])
        )
        painter.drawRoundedRect(row_rect, 6, 6)

        check_rect = QRectF(row_rect.left() + 10, row_rect.center().y() - 8, 16, 16)
        is_checked = item["selected"]
        painter.setPen(
            QColor(THEME_DARK["accent"] if is_checked else THEME_DARK["outline"])
        )
        painter.setBrush(
            QColor(THEME_DARK["accent"] if is_checked else THEME_DARK["field"])
        )
        painter.drawRoundedRect(check_rect, 3, 3)
        if is_checked:
            painter.setPen(QPen(QColor("#202127"), 2))
            painter.drawLine(
                check_rect.left() + 3,
                check_rect.center().y(),
                check_rect.left() + 7,
                check_rect.bottom() - 3,
            )
            painter.drawLine(
                check_rect.left() + 7,
                check_rect.bottom() - 3,
                check_rect.right() - 3,
                check_rect.top() + 3,
            )

        cover_rect = QRectF(row_rect.left() + 36, row_rect.top() + 6, 48, 48)
        pixmap = item.get("cover_pixmap")
        if pixmap is None and song.get("cover_url") and not item.get("cover_requested"):
            item["cover_requested"] = True
            self.request_cover(index.row(), song["cover_url"])
        if isinstance(pixmap, QPixmap) and not pixmap.isNull():
            path = QPainterPath()
            path.addRoundedRect(cover_rect, 4, 4)
            painter.setClipPath(path)
            painter.drawPixmap(cover_rect.toRect(), pixmap)
            painter.setClipping(False)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(THEME_DARK["field"]))
            painter.drawRoundedRect(cover_rect, 4, 4)

        progress_width = min(170, max(125, int(row_rect.width() * 0.22)))
        progress_rect = QRectF(
            row_rect.right() - progress_width - 10,
            row_rect.center().y() - 11,
            progress_width,
            22,
        )
        text_left = cover_rect.right() + 10
        duration_width = 58
        duration_right = progress_rect.left() - 10
        duration_left = duration_right - duration_width
        text_width = max(30, int(duration_left - 10 - text_left))

        title_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor(THEME_DARK["foreground"]))
        title = QFontMetrics(title_font).elidedText(
            song.get("name", ""),
            Qt.TextElideMode.ElideRight,
            text_width,
        )
        painter.drawText(
            QRect(
                int(text_left),
                int(row_rect.top() + 8),
                text_width,
                20,
            ),
            int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
            title,
        )

        metadata_font = QFont("Segoe UI", 8)
        painter.setFont(metadata_font)
        painter.setPen(QColor(THEME_DARK["secondary"]))
        artist = QFontMetrics(metadata_font).elidedText(
            song.get("artist", ""),
            Qt.TextElideMode.ElideRight,
            text_width,
        )
        painter.drawText(
            QRect(
                int(text_left),
                int(row_rect.top() + 31),
                text_width,
                18,
            ),
            int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
            artist,
        )
        painter.drawText(
            QRect(
                int(duration_left),
                int(row_rect.top() + 31),
                duration_width,
                18,
            ),
            int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight),
            song.get("duration_str", ""),
        )
        draw_progress_bar(
            painter,
            progress_rect,
            item["state"],
            item.get("started_at"),
        )
        painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseButtonRelease:
            if event.button() != Qt.MouseButton.LeftButton:
                return False
            check_rect = QRect(
                option.rect.left() + 13,
                option.rect.center().y() - 8,
                16,
                16,
            )
            if check_rect.contains(event.position().toPoint()):
                current = model.data(index, Qt.ItemDataRole.CheckStateRole)
                new_value = (
                    Qt.CheckState.Unchecked
                    if current == Qt.CheckState.Checked
                    else Qt.CheckState.Checked
                )
                return model.setData(index, new_value, Qt.ItemDataRole.CheckStateRole)
        return False


class UiVentanaPrincipal:
    def __init__(self, window):
        self.window = window

    def setup_ui(self):
        window = self.window
        central = QWidget()
        window.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(116)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 14, 8, 14)
        sidebar_layout.setSpacing(10)
        sidebar_layout.addStretch(1)

        window.page_stack = QStackedWidget()
        window.nav_group = QButtonGroup(window)
        window.nav_group.setExclusive(True)
        window.nav_buttons = []
        navigation = [
            ("Inicio", 0, "home"),
            ("Reportes", 1, "report"),
            ("Apoyar", 2, "heart"),
            ("Configuración", 3, "settings"),
            ("Acerca de", 4, "info"),
        ]
        for label, page_index, icon_name in navigation:
            button = QToolButton()
            button.setText(label)
            button.setIcon(make_icon(icon_name))
            button.setIconSize(QSize(22, 22))
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            button.setObjectName("navButton")
            button.setFixedSize(100, 82)
            button.setCheckable(True)
            button.clicked.connect(
                lambda checked=False, index=page_index: window._select_page(index)
            )
            window.nav_group.addButton(button, page_index)
            sidebar_layout.addWidget(
                button,
                alignment=Qt.AlignmentFlag.AlignHCenter,
            )
            window.nav_buttons.append(button)
        sidebar_layout.addStretch(1)
        root_layout.addWidget(sidebar)

        home_page = QWidget()
        layout = QVBoxLayout(home_page)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(12)

        heading_layout = QVBoxLayout()
        heading_layout.setSpacing(0)
        logo_layout = QHBoxLayout()
        logo_layout.setSpacing(12)
        note_before = QLabel()
        note_before.setPixmap(make_icon("music").pixmap(QSize(62, 62)))
        logo_layout.addWidget(note_before, alignment=Qt.AlignmentFlag.AlignVCenter)
        logo = QLabel("Mei's Player")
        logo_font = cargar_fuente_custom()
        logo.setFont(logo_font)
        logo.setStyleSheet(
            f"color: #F044A8; font-family: '{logo_font.family()}';"
            f"font-size: {min(logo_font.pointSize(), 34)}pt; font-weight: bold;"
        )
        logo_layout.addWidget(logo)
        note_after = QLabel()
        note_after.setPixmap(make_icon("music").pixmap(QSize(62, 62)))
        logo_layout.addWidget(note_after, alignment=Qt.AlignmentFlag.AlignVCenter)
        logo_layout.addStretch()
        heading_layout.addLayout(logo_layout)
        subtitle = QLabel("Descarga tu música favorita de Spotify y YouTube")
        subtitle.setStyleSheet("color: #D8C6D4; font-size: 11pt;")
        heading_layout.addWidget(subtitle)
        layout.addLayout(heading_layout)

        search_layout = QHBoxLayout()
        window.url_entry = QLineEdit()
        window.url_entry.setPlaceholderText(
            "Pega aquí el enlace de Spotify o YouTube"
        )
        window.url_entry.returnPressed.connect(window.iniciar_busqueda)
        search_layout.addWidget(window.url_entry, 1)
        window.btn_buscar = QPushButton("Buscar")
        window.btn_buscar.setIcon(make_icon("search", "#21091B"))
        window.btn_buscar.setObjectName("primaryButton")
        window.btn_buscar.clicked.connect(window.iniciar_busqueda)
        search_layout.addWidget(window.btn_buscar)
        window.btn_limpiar = QPushButton("Limpiar")
        window.btn_limpiar.setIcon(make_icon("trash"))
        window.btn_limpiar.clicked.connect(window.limpiar_busqueda)
        layout.addLayout(search_layout)

        action_bar = QFrame()
        action_bar.setObjectName("actionBar")
        actions_layout = QHBoxLayout(action_bar)
        actions_layout.setContentsMargins(10, 5, 10, 5)
        actions_layout.setSpacing(8)
        window.btn_marcar = QPushButton("Marcar Todo")
        window.btn_marcar.setIcon(make_icon("check"))
        window.btn_marcar.setFlat(True)
        window.btn_marcar.clicked.connect(window.toggle_all)
        actions_layout.addWidget(window.btn_marcar)
        actions_layout.addWidget(_separator())
        actions_layout.addWidget(QLabel("Formato:"))
        window.combo_formato = QComboBox()
        window.combo_formato.addItems(["mp3", "m4a", "flac", "wav"])
        formato = obtener_ultimo_formato()
        if formato in ("mp3", "m4a", "flac", "wav"):
            window.combo_formato.setCurrentText(formato)
        window.combo_formato.currentTextChanged.connect(window.cambiar_formato)
        window.combo_formato.setFixedWidth(92)
        actions_layout.addWidget(window.combo_formato)
        actions_layout.addWidget(_separator())
        window.btn_descargar = QPushButton("Descargar seleccionadas")
        window.btn_descargar.setIcon(make_icon("download"))
        window.btn_descargar.setFlat(True)
        window.btn_descargar.clicked.connect(window.iniciar_descarga)
        actions_layout.addWidget(window.btn_descargar)
        actions_layout.addWidget(_separator())
        window.btn_pausar = QPushButton("Pausar")
        window.btn_pausar.setIcon(make_icon("pause"))
        window.btn_pausar.setFlat(True)
        window.btn_pausar.setEnabled(False)
        window.btn_pausar.clicked.connect(window.toggle_pausa)
        actions_layout.addWidget(window.btn_pausar)
        window.btn_detener = QPushButton("Detener")
        window.btn_detener.setIcon(make_icon("stop"))
        window.btn_detener.setFlat(True)
        window.btn_detener.setEnabled(False)
        window.btn_detener.clicked.connect(window.detener_descarga)
        actions_layout.addWidget(window.btn_detener)
        window.btn_limpiar.setFlat(True)
        actions_layout.addWidget(window.btn_limpiar)
        actions_layout.addStretch()
        window.lbl_estado_der = QLabel("")
        window.lbl_estado_der.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        actions_layout.addWidget(window.lbl_estado_der)

        status_layout = QHBoxLayout()
        window.lbl_estado_izq = QLabel("Listo.")
        window.lbl_estado_izq.setStyleSheet("color: #D8C6D4;")
        status_layout.addWidget(window.lbl_estado_izq)
        status_layout.addStretch()
        layout.addWidget(action_bar)
        layout.addLayout(status_layout)

        song_panel = QFrame()
        song_panel.setObjectName("songPanel")
        song_panel_layout = QVBoxLayout(song_panel)
        song_panel_layout.setContentsMargins(0, 0, 0, 4)
        song_panel_layout.setSpacing(0)
        list_header = QHBoxLayout()
        list_header.setContentsMargins(14, 8, 14, 6)
        window.lbl_lista_header = QLabel("Lista de canciones")
        window.lbl_lista_header.setStyleSheet(
            "font-weight: 700; font-size: 11pt;"
        )
        window.lbl_lista_count = QLabel("0 canciones")
        window.lbl_lista_count.setStyleSheet("color: #D8C6D4;")
        list_header.addWidget(window.lbl_lista_header)
        list_header.addStretch()
        list_header.addWidget(window.lbl_lista_count)
        song_panel_layout.addLayout(list_header)
        window.list_view = QListView()
        window.list_view.setMouseTracking(True)
        window.list_view.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )
        window.list_view.setVerticalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )
        window.list_view.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        window.list_view.setUniformItemSizes(True)
        window.model = SongListModel(window)
        window.list_view.setModel(window.model)
        window.delegate = SongDelegate(window._request_cover, window.list_view)
        window.list_view.setItemDelegate(window.delegate)
        song_panel_layout.addWidget(window.list_view, 1)
        layout.addWidget(song_panel, 1)
        window.scrollbar = window.list_view.verticalScrollBar()
        window.page_stack.addWidget(home_page)

        window.reportes_page = ReportesPage()
        window.page_stack.addWidget(window.reportes_page)
        window.apoyar_page = ApoyarPage()
        window.page_stack.addWidget(window.apoyar_page)
        window.configuracion_page = ConfiguracionPage()
        window.configuracion_page.cambiar_api_solicitado.connect(
            window.cambiar_api_keys
        )
        window.page_stack.addWidget(window.configuracion_page)
        window.acerca_page = AcercaPage()
        window.page_stack.addWidget(window.acerca_page)

        root_layout.addWidget(window.page_stack, 1)
        window.nav_buttons[0].setChecked(True)
        window._actualizar_reportes()


def _separator():
    separator = QFrame()
    separator.setFrameShape(QFrame.Shape.VLine)
    separator.setStyleSheet("color: #8A2C69;")
    return separator


def make_icon(name, color=None):
    scale = 2 if name == "music" else 1
    pixmap = QPixmap(24 * scale, 24 * scale)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(scale, scale)
    painter.setPen(
        QPen(
            QColor(color or THEME_DARK["accent"]),
            2,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
    )
    painter.setBrush(Qt.BrushStyle.NoBrush)

    if name == "home":
        path = QPainterPath()
        path.moveTo(3, 11)
        path.lineTo(12, 4)
        path.lineTo(21, 11)
        path.moveTo(6, 10)
        path.lineTo(6, 20)
        path.lineTo(18, 20)
        path.lineTo(18, 10)
        painter.drawPath(path)
        painter.drawRect(QRect(10, 14, 4, 6))
    elif name == "heart":
        path = QPainterPath()
        path.moveTo(12, 20)
        path.cubicTo(10, 18, 3, 13, 3, 8)
        path.cubicTo(3, 4, 9, 3, 12, 8)
        path.cubicTo(15, 3, 21, 4, 21, 8)
        path.cubicTo(21, 13, 14, 18, 12, 20)
        painter.drawPath(path)
    elif name == "settings":
        painter.drawEllipse(QRectF(8, 8, 8, 8))
        painter.drawEllipse(QRectF(10.5, 10.5, 3, 3))
        for x1, y1, x2, y2 in (
            (12, 2, 12, 6),
            (12, 18, 12, 22),
            (2, 12, 6, 12),
            (18, 12, 22, 12),
            (4.9, 4.9, 7.7, 7.7),
            (16.3, 16.3, 19.1, 19.1),
            (4.9, 19.1, 7.7, 16.3),
            (16.3, 7.7, 19.1, 4.9),
        ):
            painter.drawLine(x1, y1, x2, y2)
    elif name == "info":
        painter.drawEllipse(QRectF(3, 3, 18, 18))
        painter.drawLine(12, 11, 12, 17)
        painter.drawPoint(12, 7)
    elif name == "report":
        painter.drawRoundedRect(QRectF(4, 3, 16, 18), 2, 2)
        painter.drawLine(8, 8, 16, 8)
        painter.drawLine(8, 12, 16, 12)
        painter.drawLine(8, 16, 13, 16)
    elif name == "search":
        painter.drawEllipse(QRectF(3, 3, 13, 13))
        painter.drawLine(15, 15, 21, 21)
    elif name == "trash":
        painter.drawLine(4, 6, 20, 6)
        painter.drawLine(9, 3, 15, 3)
        painter.drawRoundedRect(QRectF(6, 7, 12, 14), 2, 2)
        painter.drawLine(10, 10, 10, 18)
        painter.drawLine(14, 10, 14, 18)
    elif name == "check":
        painter.drawLine(4, 12, 10, 18)
        painter.drawLine(10, 18, 20, 6)
    elif name == "download":
        painter.drawLine(12, 3, 12, 15)
        painter.drawLine(7, 10, 12, 15)
        painter.drawLine(12, 15, 17, 10)
        painter.drawLine(4, 19, 20, 19)
        painter.drawLine(4, 19, 4, 16)
        painter.drawLine(20, 19, 20, 16)
    elif name == "pause":
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(color or THEME_DARK["accent"]))
        painter.drawRoundedRect(QRectF(6, 4, 4, 16), 1, 1)
        painter.drawRoundedRect(QRectF(14, 4, 4, 16), 1, 1)
    elif name == "stop":
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(color or THEME_DARK["accent"]))
        painter.drawRoundedRect(QRectF(5, 5, 14, 14), 2, 2)
    elif name == "music":
        painter.setPen(
            QPen(
                QColor(color or THEME_DARK["accent"]),
                2.8,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        painter.drawLine(13, 5, 20, 3)
        painter.drawLine(13, 5, 13, 17)
        painter.drawLine(20, 3, 20, 14)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(color or THEME_DARK["accent"]))
        painter.drawEllipse(QRectF(7, 14, 7, 6))
        painter.drawEllipse(QRectF(14, 11, 7, 6))

    painter.end()
    return QIcon(pixmap)
