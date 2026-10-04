import os
import sys
import cv2
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QFileDialog, QMessageBox
)
from PyQt6.QtGui import QImage, QPixmap, QFont
from PyQt6.QtCore import Qt, pyqtSlot

from config import PORT_NAME, GATE_NAME, CAMERA_SOURCE, SNAPSHOT_DIR
from src.worker import RealtimeCameraWorker

class CleanCCTVViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Container-Eye | {PORT_NAME} - {GATE_NAME}")
        self.resize(1150, 720)
        self.setStyleSheet('''
            QMainWindow { background-color: #0c0d10; }
            QWidget { color: #e2e8f0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
            QFrame#VideoBox { background-color: #000000; border: 1px solid #1e293b; border-radius: 4px; }
            QPushButton {
                background-color: #1e293b; color: #f8fafc; border: 1px solid #334155;
                border-radius: 4px; padding: 6px 14px; font-weight: 600; font-size: 11px;
            }
            QPushButton:hover { background-color: #334155; }
        ''')

        self.last_frame = None
        self._init_ui()
        self._start_worker(CAMERA_SOURCE)

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 1. Header Bar: Bersih, Minimalis, Informasi Penting Saja
        header = QHBoxLayout()
        self.lbl_title = QLabel(f"● LIVE CAM | {PORT_NAME} - {GATE_NAME}")
        self.lbl_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #10b981;")
        
        self.lbl_telemetry = QLabel("FPS: -- | INFER: -- ms")
        self.lbl_telemetry.setStyleSheet("font-size: 12px; color: #94a3b8; font-family: monospace;")
        
        header.addWidget(self.lbl_title)
        header.addStretch()
        header.addWidget(self.lbl_telemetry)
        layout.addLayout(header)

        # 2. Layar Kamera CCTV (Fokus Utama Terbesar)
        self.video_box = QFrame()
        self.video_box.setObjectName("VideoBox")
        vbox_layout = QVBoxLayout(self.video_box)
        vbox_layout.setContentsMargins(0, 0, 0, 0)

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setText("Menghubungkan ke hardware kamera realtime...")
        vbox_layout.addWidget(self.video_label)
        layout.addWidget(self.video_box, stretch=1)

        # 3. Banner Status Kelaikan (Satu Garis Elegan di Bawah Kamera)
        self.status_bar = QFrame()
        self.status_bar.setStyleSheet("background-color: #0f2317; border: 1px solid #10b981; border-radius: 4px; padding: 6px;")
        s_layout = QHBoxLayout(self.status_bar)
        s_layout.setContentsMargins(12, 6, 12, 6)

        self.lbl_status = QLabel("STATUS: GATE PASS — KONTAINER LAIK OPERASIONAL")
        self.lbl_status.setStyleSheet("font-size: 12px; font-weight: bold; color: #10b981;")
        self.lbl_defects = QLabel("Defek: 0")
        self.lbl_defects.setStyleSheet("font-size: 11px; color: #94a3b8;")

        s_layout.addWidget(self.lbl_status)
        s_layout.addStretch()
        s_layout.addWidget(self.lbl_defects)
        layout.addWidget(self.status_bar)

        # 4. Toolbar Bawah (Hanya Tombol Esensial Operator)
        toolbar = QHBoxLayout()
        self.btn_snap = QPushButton("Ambil Snapshot [S]")
        self.btn_snap.clicked.connect(self._manual_snapshot)

        self.btn_mute = QPushButton("Mute Alarm [M]")
        self.btn_mute.setCheckable(True)
        self.btn_mute.clicked.connect(self._toggle_mute)

        self.btn_open_folder = QPushButton("Buka Folder Foto Bukti")
        self.btn_open_folder.clicked.connect(lambda: os.startfile(SNAPSHOT_DIR))

        toolbar.addWidget(self.btn_snap)
        toolbar.addWidget(self.btn_mute)
        toolbar.addWidget(self.btn_open_folder)
        toolbar.addStretch()
        layout.addLayout(toolbar)

    def _start_worker(self, source):
        self.worker = RealtimeCameraWorker(source)
        self.worker.frame_signal.connect(self._update_frame)
        self.worker.telemetry_signal.connect(self._update_telemetry)
        self.worker.alert_signal.connect(self._on_alert)
        self.worker.start()

    @pyqtSlot(object)
    def _update_frame(self, frame):
        self.last_frame = frame
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        
        tw = self.video_label.width()
        th = self.video_label.height()
        if tw > 0 and th > 0:
            pix = QPixmap.fromImage(qt_img).scaled(tw, th, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.video_label.setPixmap(pix)

    @pyqtSlot(dict)
    def _update_telemetry(self, data):
        self.lbl_telemetry.setText(f"FPS: {data['fps']:.1f} | INFER: {data['latency_ms']:.1f} ms")
        self.lbl_defects.setText(f"Objek Terdeteksi: {data['count']}")

        if data["is_critical"]:
            self.status_bar.setStyleSheet("background-color: #2b0f0f; border: 1px solid #ef4444; border-radius: 4px; padding: 6px;")
            self.lbl_status.setText("STATUS: GATE HOLD / REJECT — CACAT KRITIS DITEMUKAN")
            self.lbl_status.setStyleSheet("font-size: 12px; font-weight: bold; color: #ef4444;")
        elif data["count"] > 0:
            self.status_bar.setStyleSheet("background-color: #261f0a; border: 1px solid #eab308; border-radius: 4px; padding: 6px;")
            self.lbl_status.setText("STATUS: GATE CAUTION — ANOMALI TERDETEKSI")
            self.lbl_status.setStyleSheet("font-size: 12px; font-weight: bold; color: #eab308;")
        else:
            self.status_bar.setStyleSheet("background-color: #0f2317; border: 1px solid #10b981; border-radius: 4px; padding: 6px;")
            self.lbl_status.setText("STATUS: GATE PASS — LAIK OPERASIONAL")
            self.lbl_status.setStyleSheet("font-size: 12px; font-weight: bold; color: #10b981;")

    @pyqtSlot(str)
    def _on_alert(self, msg):
        pass

    def _manual_snapshot(self):
        if self.last_frame is not None:
            name = f"MANUAL_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
            path = os.path.join(SNAPSHOT_DIR, name)
            cv2.imwrite(path, self.last_frame)
            QMessageBox.information(self, "Snapshot", f"Foto tersimpan:\n{name}")

    def _toggle_mute(self):
        self.worker.mute_alarm = self.btn_mute.isChecked()
        self.btn_mute.setText("Unmute Alarm" if self.worker.mute_alarm else "Mute Alarm [M]")

    def closeEvent(self, event):
        self.worker.stop()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = CleanCCTVViewer()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
