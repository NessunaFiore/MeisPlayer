import math
import time
import tkinter as tk
from styles import crear_rectangulo_redondeado


class DownloadProgressBar(tk.Canvas):
    def __init__(self, master, width=170, height=22, **kwargs):
        super().__init__(
            master,
            width=width,
            height=height,
            highlightthickness=0,
            bd=0,
            bg=master.cget("bg"),
            **kwargs,
        )
        self._progress = 0.0
        self._state = "pending"
        self._started_at = None
        self._after_id = None
        self._colors = {
            "background": master.cget("bg"),
            "foreground": "#333333",
            "track": "#BDBDBD",
            "outline": "#AAAAAA",
        }
        self.bind("<Configure>", self._draw)
        self._draw()

    def start(self):
        self._cancel_animation()
        self._state = "downloading"
        self._progress = 0.0
        self._started_at = time.monotonic()
        self._draw()
        self._animate()

    def complete(self):
        self._cancel_animation()
        self._state = "completed"
        self._progress = 1.0
        self._draw()

    def fail(self):
        self._cancel_animation()
        self._state = "error"
        self._progress = 1.0
        self._draw()

    def _animate(self):
        if self._state != "downloading" or self._started_at is None:
            return

        elapsed = time.monotonic() - self._started_at
        self._progress = min(0.92, 0.92 * (1 - math.exp(-elapsed / 8)))
        self._draw()
        self._after_id = self.after(100, self._animate)

    def _cancel_animation(self):
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None

    def _draw(self, _event=None):
        width = self.winfo_width()
        height = self.winfo_height()
        if width <= 1 or height <= 1:
            return

        background = self._colors["track"]
        fill = "#4CAF50" if self._state in ("downloading", "completed") else "#E53935"
        if self._state == "pending":
            fill = background

        self.delete("all")
        crear_rectangulo_redondeado(
            self, 0, 0, width, height, height / 2,
            fill=background, outline=self._colors["outline"], width=1,
        )
        if self._progress > 0:
            progress_width = max(height / 2, width * self._progress)
            crear_rectangulo_redondeado(
                self, 0, 0, min(width, progress_width), height, height / 2,
                fill=fill, outline="",
            )

        labels = {
            "pending": "(pendiente)",
            "downloading": "DESCARGANDO",
            "completed": "COMPLETADO",
            "error": "ERROR",
        }
        self.create_text(
            width / 2,
            height / 2,
            text=labels[self._state],
            fill="#FFFFFF" if self._state != "pending" else self._colors["foreground"],
            font=("Helvetica", 8, "bold"),
        )

    def set_background(self, color):
        self.configure(bg=color)
        self._colors["background"] = color
        self._draw()

    def set_theme(self, background, foreground, track, outline):
        self._colors.update(
            background=background,
            foreground=foreground,
            track=track,
            outline=outline,
        )
        self.configure(bg=background)
        self._draw()
