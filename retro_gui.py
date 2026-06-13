import sys
import os
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QPixmap, QImage

from music import MusicPlayer

class SkinPlayerGUI(QWidget):
    def __init__(self, skin_path):
        super().__init__()
        self.player = MusicPlayer()
        self.skin_path = skin_path
        self.current_title = ""
        self.scroll_pos = 0
        
        self.initUI()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(300)

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        img = QImage(self.skin_path).convertToFormat(QImage.Format_ARGB32)
        # Limpiar el fondo negro de la IA
        for y in range(img.height()):
            for x in range(img.width()):
                color = img.pixelColor(x, y)
                if color.red() < 20 and color.green() < 20 and color.blue() < 20:
                    color.setAlpha(0)
                    img.setPixelColor(x, y, color)
        
        pixmap = QPixmap.fromImage(img).scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.resize(pixmap.width(), pixmap.height())
        self.setMask(pixmap.mask())

        # Centrar
        qr = self.frameGeometry()
        cp = QApplication.desktop().screenGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        self.bg_label = QLabel(self)
        self.bg_label.setPixmap(pixmap)
        self.bg_label.setGeometry(0, 0, pixmap.width(), pixmap.height())

        # Pantalla del iPod (Parche Blanco calculado sobre el bounding box)
        self.screen_bg = QLabel(self)
        self.screen_bg.setGeometry(115, 45, 170, 130)
        self.screen_bg.setStyleSheet("background-color: #e5e5e5; border: 2px solid #222; border-radius: 5px;")

        # Título Animado (Marquee)
        self.screen = QLabel("IPOD READY", self)
        self.screen.setGeometry(120, 60, 160, 20)
        self.screen.setStyleSheet("font-family: Menlo, monospace; font-size: 14px; color: black; font-weight: bold; background: transparent;")

        # Búsqueda
        self.entry = QLineEdit(self)
        self.entry.setPlaceholderText("Buscar canción...")
        self.entry.setGeometry(120, 110, 160, 24)
        self.entry.setStyleSheet("background: transparent; color: black; border: 1px solid #999; font-family: Menlo, monospace; font-size: 12px; border-radius: 3px;")
        self.entry.returnPressed.connect(self.search_music)

        # Controles (Click Wheel - centro aprox 200x277)
        play_btn = QPushButton(self)
        play_btn.setGeometry(180, 310, 40, 40)
        play_btn.setStyleSheet("background: transparent; border: none;")
        play_btn.clicked.connect(self.player.pause_resume)

        next_btn = QPushButton(self)
        next_btn.setGeometry(240, 260, 40, 40)
        next_btn.setStyleSheet("background: transparent; border: none;")
        next_btn.clicked.connect(self.player.next)

        stop_btn = QPushButton(self)
        stop_btn.setGeometry(180, 220, 40, 40)
        stop_btn.setStyleSheet("background: transparent; border: none;")
        stop_btn.clicked.connect(self.player.stop)

        # Botón Cerrar Oculto
        close_btn = QPushButton("✖", self)
        close_btn.setGeometry(290, 20, 20, 20)
        close_btn.setStyleSheet("color: rgba(255,0,0,150); background: transparent; border: none; font-weight: bold; font-size: 16px;")
        close_btn.clicked.connect(self.close)
        
        self.oldPos = self.pos()

    def search_music(self):
        query = self.entry.text()
        if query:
            self.current_title = query
            self.scroll_pos = 0
            self.entry.clear()
            self.player.play(query)

    def update_display(self):
        title = self.player.get_current_song()
        if not title:
            title = self.current_title
            
        if title:
            if len(title) > 18:
                display_text = title[self.scroll_pos:self.scroll_pos+18]
                self.scroll_pos += 1
                if self.scroll_pos > len(title):
                    self.scroll_pos = 0
            else:
                display_text = title
            self.screen.setText(display_text)
        else:
            self.screen.setText("IPOD READY")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Buscar imagen del iPod en skins/
    skin_file = None
    if os.path.exists("skins"):
        for f in os.listdir("skins"):
            if "ipod" in f.lower() and f.endswith(".png"):
                skin_file = os.path.join("skins", f)
                break
            
    if not skin_file:
        print("No se encontró la imagen del iPod en la carpeta skins.")
        sys.exit(1)
        
    ex = SkinPlayerGUI(skin_file)
    ex.show()
    sys.exit(app.exec_())
