from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class ReportesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(12)

        title = QLabel("Reportes de descargas")
        title.setStyleSheet("font-size: 20pt; font-weight: 700; color: #F044A8;")
        layout.addWidget(title)

        self.count_label = QLabel("Canciones fallidas: 0")
        self.count_label.setStyleSheet("color: #D8C6D4;")
        layout.addWidget(self.count_label)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(
            ["Canción", "Artista", "Motivo del fallo"]
        )
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 240)
        self.table.setColumnWidth(1, 180)
        layout.addWidget(self.table, 1)
        self.set_failures([])

    def set_failures(self, failed_items):
        self.table.clearSpans()
        self.count_label.setText(f"Canciones fallidas: {len(failed_items)}")
        if not failed_items:
            self.table.setRowCount(1)
            empty_item = QTableWidgetItem("No hay canciones fallidas.")
            empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(0, 0, empty_item)
            self.table.setSpan(0, 0, 1, 3)
            return

        self.table.setRowCount(len(failed_items))
        for row, (song, item) in enumerate(failed_items):
            self.table.setItem(
                row,
                0,
                QTableWidgetItem(song.get("name", "Desconocida")),
            )
            self.table.setItem(
                row,
                1,
                QTableWidgetItem(song.get("artist", "Desconocido")),
            )
            self.table.setItem(
                row,
                2,
                QTableWidgetItem(
                    item.get("error_reason")
                    or "El descargador no indicó el motivo del fallo."
                ),
            )
