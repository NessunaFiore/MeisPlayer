from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ApoyarPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Apoya Mei's Player")
        title.setStyleSheet("font-size: 20pt; font-weight: 700; color: #F044A8;")
        layout.addWidget(title)

        message = QLabel(
            "Se supone que deberia poner aqui un boton para KO-FI o Paypal, pero soy bien webona pa ponerlo."

            
            "De momento, Mei, comparte con tus amigos, muah lov u"
        )
        message.setWordWrap(True)
        layout.addWidget(message)
        layout.addStretch()
