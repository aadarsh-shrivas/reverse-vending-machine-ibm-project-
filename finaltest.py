# ================== PART 1 ==================

import sys
import cv2
import os
import subprocess
import random
import string

from ultralytics import YOLO

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtMultimedia import QSoundEffect

# ---------------- MODEL ----------------
model = YOLO("rtdetr-l.pt")

# ---------------- CAMERA ----------------
cap = cv2.VideoCapture(0)

# ---------------- ECO THEME ----------------
BG_GRADIENT = """
QWidget {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #022c22, stop:0.5 #065f46, stop:1 #022c22);
}
"""

PRIMARY = "#22c55e"
SECONDARY = "#4ade80"
ACCENT = "#16a34a"
GLOW = "#00ffcc"
TEXT = "#d1fae5"

# ---------------- DATA ----------------
prices = {
    "bottle": 10,
    "cup": 5,
    "can": 15,
    "book": 8,
    "cell phone": 2
}

allowed_items = ["bottle", "cup", "book", "cell phone"]

def display_name(label):
    return "paper" if label == "book" else "pen" if label == "cell phone" else label

def refine_label(label, box):
    x1, y1, x2, y2 = map(int, box.xyxy[0])
    w, h = x2 - x1, y2 - y1
    ratio = h / w if w else 0
    if label == "bottle" and 1.2 < ratio < 2.2:
        return "can"
    return label

# ---------------- COUPON ----------------
def generate_coupon(points):
    prefix = "ECO"
    rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    value = points * 3
    return f"{prefix}{value}{rand}"

# ---------------- PDF ----------------
from reportlab.platypus import *
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf(receipt, total):
    path = os.path.join(os.getcwd(), "receipt.pdf")
    doc = SimpleDocTemplate(path)
    styles = getSampleStyleSheet()

    coupon = generate_coupon(total)

    title = ParagraphStyle('title', parent=styles['Title'],
                           textColor=colors.green, alignment=1)

    normal = ParagraphStyle('normal', parent=styles['Normal'], spaceAfter=8)

    highlight = ParagraphStyle('highlight',
                               parent=styles['Heading2'],
                               textColor=colors.darkgreen,
                               alignment=1)

    box_style = ParagraphStyle('box',
                               parent=styles['Heading1'],
                               alignment=1,
                               textColor=colors.white,
                               backColor=colors.green)

    content = []

    content.append(Paragraph("🌱 REVERSE VENDING MACHINE 🌱", title))
    content.append(Spacer(1, 15))

    content.append(Paragraph("🎉 Thank you for recycling!", normal))

    for item, price in receipt:
        content.append(Paragraph(f"• {item} : {price} pts", normal))

    content.append(Spacer(1, 10))
    content.append(Paragraph(f"Total Points: {total}", highlight))
    content.append(Spacer(1, 15))

    # Coupon box
    content.append(Paragraph("🎟️ YOUR REWARD", highlight))
    content.append(Spacer(1, 5))
    content.append(Paragraph(coupon, box_style))

    content.append(Spacer(1, 15))

    content.append(Paragraph(f"🌍 You recycled {len(receipt)} items!", normal))
    content.append(Paragraph("💚 Keep saving the planet!", normal))

    doc.build(content)
    return path

def open_pdf(path):
    if os.path.exists(path):
        subprocess.Popen(path, shell=True)
        # ================== PART 2 ==================

class ParticleBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.particles = []

        for _ in range(60):
            self.particles.append({
                "x": random.randint(0, 1920),
                "y": random.randint(0, 1080),
                "dx": random.uniform(-0.3, 0.3),
                "dy": random.uniform(-0.3, 0.3),
                "size": random.randint(1, 3)
            })

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_particles)
        self.timer.start(30)

    def update_particles(self):
        for p in self.particles:
            p["x"] += p["dx"]
            p["y"] += p["dy"]

            if p["x"] < 0 or p["x"] > self.width():
                p["dx"] *= -1
            if p["y"] < 0 or p["y"] > self.height():
                p["dy"] *= -1

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        for p in self.particles:
            painter.setBrush(QColor(34, 197, 94, 80))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(p["x"]), int(p["y"]), p["size"], p["size"])


class SmartRecycleApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Reverse Vending Machine")
        self.showFullScreen()
        self.setStyleSheet(BG_GRADIENT)

        # ---------- SOUND ----------
        self.click_sound = QSoundEffect()
        self.click_sound.setSource(QUrl.fromLocalFile(os.path.abspath("click.wav")))
        self.click_sound.setVolume(0.5)

        self.success_sound = QSoundEffect()
        self.success_sound.setSource(QUrl.fromLocalFile(os.path.abspath("success.wav")))
        self.success_sound.setVolume(0.6)

        # ---------- BACKGROUND ----------
        self.bg = ParticleBackground(self)
        self.bg.setGeometry(0, 0, 1920, 1080)

        # ---------- MAIN LAYOUT ----------
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(15)

        # ---------- TITLE ----------
        self.title = QLabel("🌱 REVERSE VENDING MACHINE")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont("Arial", 28, QFont.Bold))
        self.title.setStyleSheet(f"color: {PRIMARY}; letter-spacing: 2px;")
        main_layout.addWidget(self.title)

        # ---------- CAMERA ----------
        self.camera_frame = QFrame()
        self.camera_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255,255,255,0.05);
                border-radius: 20px;
                border: 1px solid rgba(255,255,255,0.2);
            }
        """)

        cam_layout = QVBoxLayout()
        self.camera_frame.setLayout(cam_layout)

        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignCenter)
        cam_layout.addWidget(self.camera_label)

        main_layout.addWidget(self.camera_frame, 5)

        # ---------- RECEIPT PANEL ----------
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            QScrollArea {
                background: rgba(255,255,255,0.05);
                border-radius: 15px;
            }
        """)

        self.scroll_content = QLabel()
        self.scroll_content.setAlignment(Qt.AlignTop)
        self.scroll_content.setStyleSheet(f"color: {TEXT}; padding: 10px;")

        self.scroll.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll, 2)

        # ---------- STATUS ----------
        self.status = QLabel("🌱 Ready to Recycle")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setFont(QFont("Arial", 16))
        self.status.setStyleSheet(f"color: {SECONDARY};")
        main_layout.addWidget(self.status)

        # ---------- BUTTONS ----------
        btn_layout = QHBoxLayout()

        self.btn1 = QPushButton()
        self.btn2 = QPushButton()
        self.exit_btn = QPushButton("EXIT")

        BTN_STYLE = f"""
        QPushButton {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {PRIMARY}, stop:1 {SECONDARY});
            color: black;
            border-radius: 18px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background: {ACCENT};
            color: white;
        }}
        QPushButton:pressed {{
            background: {GLOW};
        }}
        """

        for btn in [self.btn1, self.btn2, self.exit_btn]:
            btn.setFixedHeight(60)
            btn.setFont(QFont("Arial", 14, QFont.Bold))
            btn.setStyleSheet(BTN_STYLE)
            btn_layout.addWidget(btn)

        main_layout.addLayout(btn_layout)

        # ---------- ACTIONS ----------
        self.btn1.clicked.connect(self.button1_action)
        self.btn2.clicked.connect(self.button2_action)
        self.exit_btn.clicked.connect(self.close_app)

        # ---------- STATE ----------
        self.state = "detect"
        self.total = 0
        self.receipt = []
        self.current_label = None
        self.current_frame = None
        self.pdf_file = None

        # ---------- TIMER ----------
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)
        # ================== PART 3 ==================

    # ---------- SOUND ----------
    def play_click(self):
        if self.click_sound.isLoaded():
            self.click_sound.stop()
            self.click_sound.play()

    def play_success(self):
        if self.success_sound.isLoaded():
            self.success_sound.stop()
            self.success_sound.play()

    # ---------- ANIMATIONS ----------
    def pulse_status(self):
        anim = QPropertyAnimation(self.status, b"windowOpacity")
        anim.setDuration(400)
        anim.setStartValue(0.5)
        anim.setEndValue(1)
        anim.setLoopCount(2)
        anim.start()
        self.status.anim = anim

    def bounce(self, btn):
        rect = btn.geometry()
        anim = QPropertyAnimation(btn, b"geometry")
        anim.setDuration(120)
        anim.setStartValue(rect)
        anim.setEndValue(rect.adjusted(0, 5, 0, 5))
        anim.setEasingCurve(QEasingCurve.OutQuad)
        anim.start()
        btn.anim = anim

    def glow_camera(self):
        self.camera_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255,255,255,0.05);
                border-radius: 20px;
                border: 2px solid {GLOW};
            }}
        """)
        QTimer.singleShot(300, self.reset_camera)

    def reset_camera(self):
        self.camera_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255,255,255,0.05);
                border-radius: 20px;
                border: 1px solid rgba(255,255,255,0.2);
            }
        """)

    # ---------- EXIT ----------
    def close_app(self):
        try:
            cap.release()
        except:
            pass
        QApplication.quit()

    # ---------- BUTTON ACTIONS ----------
    def button1_action(self):
        self.bounce(self.btn1)
        self.play_click()

        if self.state == "confirm":
            name = display_name(self.current_label)
            self.total += prices[self.current_label]
            self.receipt.append((name, prices[self.current_label]))

            self.state = "next"
            self.play_success()
            self.pulse_status()

        elif self.state == "next":
            self.state = "detect"

        elif self.state == "receipt":
            open_pdf(self.pdf_file)

    def button2_action(self):
        self.bounce(self.btn2)
        self.play_click()

        if self.state == "confirm":
            self.state = "detect"

        elif self.state == "next":
            self.pdf_file = generate_pdf(self.receipt, self.total)
            self.state = "receipt"
            self.play_success()
            self.pulse_status()

        elif self.state == "receipt":
            self.receipt.clear()
            self.total = 0
            self.state = "detect"

    # ---------- UI UPDATE ----------
    def update_ui(self):
        if self.state == "detect":
            self.status.setText("🌱 Place item to recycle")
            self.btn1.setText("")
            self.btn2.setText("")
            self.scroll_content.setText("")

        elif self.state == "confirm":
            name = display_name(self.current_label)

            self.status.setText(f"♻️ {name.upper()} detected  +{prices[self.current_label]}")
            self.btn1.setText("CONFIRM")
            self.btn2.setText("REJECT")

            rgb = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            self.camera_label.setPixmap(QPixmap.fromImage(img))

        elif self.state == "next":
            self.status.setText(f"🌿 Total Points: {self.total}")
            self.btn1.setText("ADD MORE")
            self.btn2.setText("FINISH")

            receipt_text = "\n".join([f"{i} - {p}" for i, p in self.receipt])
            self.scroll_content.setText(receipt_text)

        elif self.state == "receipt":
            receipt_text = "\n".join([f"{i} - {p}" for i, p in self.receipt])

            self.scroll_content.setText(
                f"🎉 SESSION COMPLETE\n\n{receipt_text}\n\nTOTAL: {self.total}\n\n🎟️ Coupon Generated!"
            )

            self.status.setText("✅ Coupon Ready")

            self.btn1.setText("OPEN PDF")
            self.btn2.setText("NEW USER")
            # ================== PART 4 ==================

    # ---------- DETECTION LOOP ----------
    def update_frame(self):
        ret, frame = cap.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)

        if self.state == "detect":
            results = model(frame, conf=0.6)

            best_label = None
            best_conf = 0
            best_box = None

            for r in results:
                for box in r.boxes:
                    label = model.names[int(box.cls[0])]
                    conf = float(box.conf[0])

                    if label in allowed_items and conf > best_conf:
                        best_label = label
                        best_conf = conf
                        best_box = box

            if best_label:
                best_label = refine_label(best_label, best_box)

                self.current_label = best_label
                self.current_frame = frame.copy()
                self.state = "confirm"

                self.glow_camera()
                self.play_success()
                self.pulse_status()

        # ---------- CAMERA FEED ----------
        if self.state == "detect":
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            self.camera_label.setPixmap(QPixmap.fromImage(img))

        self.update_ui()


# ---------- MAIN ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = SmartRecycleApp()
    window.show()

    sys.exit(app.exec_())