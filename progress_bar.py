import time

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter

from ui.styles import THEME_DARK


RUNNING_PROGRESS_LIMIT = 0.92
RUNNING_PROGRESS_SECONDS = 24


def progress_fraction(state, started_at):
    if state in ("completed", "error"):
        return 1.0
    if state != "downloading" or started_at is None:
        return 0.0
    elapsed = max(0.0, time.monotonic() - started_at)
    progress_time = min(elapsed / RUNNING_PROGRESS_SECONDS, 1.0)
    eased_progress = 1 - (1 - progress_time) ** 3
    return RUNNING_PROGRESS_LIMIT * eased_progress


def draw_progress_bar(painter, rect, state, started_at):
    track_rect = QRectF(rect)
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QColor(THEME_DARK["outline"]))
    painter.setBrush(QColor(THEME_DARK["track"]))
    painter.drawRoundedRect(track_rect, track_rect.height() / 2, track_rect.height() / 2)

    fraction = progress_fraction(state, started_at)
    if fraction > 0:
        fill_color = (
            THEME_DARK["error"] if state == "error" else THEME_DARK["success"]
        )
        fill_rect = QRectF(track_rect)
        fill_rect.setWidth(max(track_rect.height(), track_rect.width() * fraction))
        fill_rect.setWidth(min(track_rect.width(), fill_rect.width()))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(fill_color))
        painter.drawRoundedRect(fill_rect, fill_rect.height() / 2, fill_rect.height() / 2)

    labels = {
        "pending": "Pendiente",
        "downloading": "Descargando...",
        "completed": "Completado",
        "error": "Error",
    }
    painter.setPen(
        QColor(THEME_DARK["foreground"] if state == "pending" else "#FFFFFF")
    )
    painter.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
    painter.drawText(
        track_rect,
        Qt.AlignmentFlag.AlignCenter,
        labels.get(state, "(pendiente)"),
    )
    painter.restore()
