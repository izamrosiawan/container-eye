import os
import sys
import cv2
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QComboBox, QMessageBox
)
from PyQt6.QtGui import QImage, QPixmap, QFont, QColor
from PyQt6.QtCore import Qt, pyqtSlot

from config import PORT_NAME, GATE_NAME, CAMERA_SOURCE, SNAPSHOT_DIR
from src.worker import VideoThread
from src.db import InspectionDatabase

class CCTVOperatorDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Container-Eye VMS | {PORT_NAME} - {GATE_NAME}")
        self.resize(1366, 768)
        self.setMinimumSize(1100, 650)
        self.setStyleSheet('''
            QMainWindow { background-color: #0d0f12; }
            QWidget { color: #dcdcdc; font-family: 'Segoe UI', Arial; }
            QFrame#VideoBox { background-color: #000000; border: 1px solid #2a2e39; border-radius: 4px; }
            QFrame#Sidebar { background-color: #15181e; border-left: 1px solid #2a2e39; }
            QPushButton {
                background-color: #212631; color: #ffffff; border: 1px solid #3d4452;
                border-radius: 4px; padding: 7px 14px; font-weight: bold; font-size: 11px;
            }
            QPushButton:hover { background-color: #2d3342; border-color: #5865f2; }
            QPushButton#BtnReject { background-color: #8b0000; border-color: #ff3333; }
            QPushButton#BtnReject:hover { background-color: #b30000; }
            QTableWidget {
                background-color: #101216; border: 1px solid #22262f; gridline-color: #1f232b;
                color: #e0e0e0; font-size: 11px; selection-background-color: #262c38;
            }
            QHeaderView::section {
                background-color: #1b1f27; color: #8e95a5; font-size: 10px; font-weight: bold;
                border: 1px solid #22262f; padding: 4px;
            }
            QComboBox {
                background-color: #212631; color: #ffffff; border: 1px solid #3d4452;
                border-radius: 4px; padding: 4px 8px; font-size: 11px;
            }
        ''')

        self.last_frame = None
        self.db = InspectionDatabase()
        self._init_ui()
        self._start_thread()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # =====================================================
        # KOLOM KIRI: LAYAR CCTV UTAMA & KONTROL CEPAT
        # =====================================================
        left_layout = QVBoxLayout()
        left_layout.setSpacing(8)

        # Header Info Bar
        top_bar = QHBoxLayout()
        self.lbl_gate = QLabel(f"<b>[PORTAL AKTIF]</b> {PORT_NAME} - {GATE_NAME}")
        self.lbl_gate.setStyleSheet("font-size: 12px; color: #4ade80;")
        self.lbl_fps = QLabel("FPS: 0.0 | LATENCY: 0.0 ms")
        self.lbl_fps.setStyleSheet("font-size: 12px; color: #94a3b8; font-family: monospace;")
        top_bar.addWidget(self.lbl_gate)
        top_bar.addStretch()
        top_bar.addWidget(self.lbl_fps)
        left_layout.addLayout(top_bar)

        # Layar Video Kamera (Fokus Utama)
        self.video_frame = QFrame()
        self.video_frame.setObjectName("VideoBox")
        video_inner_layout = QVBoxLayout(self.video_frame)
        video_inner_layout.setContentsMargins(0, 0, 0, 0)

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setText("Memulai stream kamera CCTV...")
        self.video_label.setStyleSheet("color: #64748b; font-size: 14px;")
        video_inner_layout.addWidget(self.video_label)
        left_layout.addWidget(self.video_frame, stretch=10)

        # Kontrol Bawah Video
        ctrl_bar = QHBoxLayout()
        self.combo_source = QComboBox()
        self.combo_source.addItem("Simulasi Test Set Pelabuhan", "assets/sample_images")
        self.combo_source.addItem("Kamera Webcam / USB Cam", 0)
        self.combo_source.currentIndexChanged.connect(self._change_camera_source)

        self.btn_browse = QPushButton("Buka Video File / RTSP...")
        self.btn_browse.clicked.connect(self._browse_source)

        self.btn_snapshot = QPushButton("Ambil Snapshot [S]")
        self.btn_snapshot.clicked.connect(self._save_manual_snapshot)

        self.btn_mute = QPushButton("Mute Alarm Audio [M]")
        self.btn_mute.setCheckable(True)
        self.btn_mute.clicked.connect(self._toggle_mute)

        ctrl_bar.addWidget(QLabel("Sumber Video:"))
        ctrl_bar.addWidget(self.combo_source)
        ctrl_bar.addWidget(self.btn_browse)
        ctrl_bar.addStretch()
        ctrl_bar.addWidget(self.btn_snapshot)
        ctrl_bar.addWidget(self.btn_mute)
        left_layout.addLayout(ctrl_bar)

        main_layout.addLayout(left_layout, stretch=7)

        # =====================================================
        # KOLOM KANAN: PANEL STATUS GERBANG & LOG EVENT
        # =====================================================
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 12, 12, 12)
        sidebar_layout.setSpacing(10)

        # 1. Status Indicator Card
        lbl_status_title = QLabel("STATUS KELAIKAN (IICL-6)")
        lbl_status_title.setStyleSheet("font-size: 10px; font-weight: bold; color: #8e95a5; letter-spacing: 1px;")
        sidebar_layout.addWidget(lbl_status_title)

        self.card_status = QFrame()
        self.card_status.setStyleSheet("background-color: #1a221a; border: 2px solid #22c55e; border-radius: 6px;")
        card_layout = QVBoxLayout(self.card_status)
        card_layout.setContentsMargins(10, 10, 10, 10)

        self.lbl_decision = QLabel("GATE PASS")
        self.lbl_decision.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_decision.setStyleSheet("font-size: 22px; font-weight: 900; color: #22c55e;")
        self.lbl_substatus = QLabel("Kontainer Laik Muat (Seaworthy)")
        self.lbl_substatus.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_substatus.setStyleSheet("font-size: 11px; color: #86efac;")
        card_layout.addWidget(self.lbl_decision)
        card_layout.addWidget(self.lbl_substatus)
        sidebar_layout.addWidget(self.card_status)

        # 2. Defect Counters
        counter_frame = QFrame()
        counter_frame.setStyleSheet("background-color: #101216; border: 1px solid #22262f; border-radius: 4px; padding: 6px;")
        c_layout = QHBoxLayout(counter_frame)
        self.lbl_count_total = QLabel("Total Defek: 0")
        self.lbl_count_total.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 11px;")
        c_layout.addWidget(self.lbl_count_total)
        sidebar_layout.addWidget(counter_frame)

        # 3. Riwayat Inspeksi & Pelanggaran
        lbl_log_title = QLabel("RIWAYAT ANOMALI & BUKTI FOTO")
        lbl_log_title.setStyleSheet("font-size: 10px; font-weight: bold; color: #8e95a5; letter-spacing: 1px; margin-top: 8px;")
        sidebar_layout.addWidget(lbl_log_title)

        self.table_logs = QTableWidget()
        self.table_logs.setColumnCount(4)
        self.table_logs.setHorizontalHeaderLabels(["Jam", "Feed ID", "Status", "Cacat"])
        self.table_logs.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_logs.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        sidebar_layout.addWidget(self.table_logs, stretch=1)

        # 4. Tombol Aksi Operator
        btn_open_folder = QPushButton("Buka Folder Snapshot Bukti")
        btn_open_folder.clicked.connect(self._open_snapshot_folder)
        sidebar_layout.addWidget(btn_open_folder)

        main_layout.addWidget(sidebar, stretch=3)

    def _start_thread(self, source=CAMERA_SOURCE):
        self.thread = VideoThread(source)
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.telemetry_signal.connect(self.update_telemetry)
        self.thread.log_signal.connect(self.add_log_row)
        self.thread.start()

    @pyqtSlot(object)
    def update_image(self, cv_img):
        self.last_frame = cv_img.copy()
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        
        target_w = self.video_label.width()
        target_h = self.video_label.height()
        if target_w > 0 and target_h > 0:
            pix = QPixmap.fromImage(qt_img).scaled(target_w, target_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.video_label.setPixmap(pix)

    @pyqtSlot(dict)
    def update_telemetry(self, data):
        self.lbl_fps.setText(f"FPS: {data['fps']:.1f} | INFER: {data['latency_ms']:.1f} ms")
        self.lbl_count_total.setText(f"Total Defek Terdeteksi: {data['defect_count']}")

        status = data['status']
        if status == "REJECT":
            self.card_status.setStyleSheet("background-color: #2b1111; border: 2px solid #ef4444; border-radius: 6px;")
            self.lbl_decision.setText("GATE HOLD / REJECT")
            self.lbl_decision.setStyleSheet("font-size: 20px; font-weight: 900; color: #ef4444;")
            self.lbl_substatus.setText("Cacat Kritis Ditemukan! Gerbang Ditahan.")
            self.lbl_substatus.setStyleSheet("font-size: 11px; color: #fca5a5;")
        elif status == "CAUTION":
            self.card_status.setStyleSheet("background-color: #2b2211; border: 2px solid #eab308; border-radius: 6px;")
            self.lbl_decision.setText("GATE CAUTION")
            self.lbl_decision.setStyleSheet("font-size: 20px; font-weight: 900; color: #eab308;")
            self.lbl_substatus.setText("Cacat Minor (Perlu Verifikasi Fisik)")
            self.lbl_substatus.setStyleSheet("font-size: 11px; color: #fde047;")
        else:
            self.card_status.setStyleSheet("background-color: #112b16; border: 2px solid #22c55e; border-radius: 6px;")
            self.lbl_decision.setText("GATE PASS")
            self.lbl_decision.setStyleSheet("font-size: 20px; font-weight: 900; color: #22c55e;")
            self.lbl_substatus.setText("Kontainer Laik Muat (IICL-6 Seaworthy)")
            self.lbl_substatus.setStyleSheet("font-size: 11px; color: #86efac;")

    @pyqtSlot(dict)
    def add_log_row(self, log):
        row_pos = self.table_logs.rowCount()
        self.table_logs.insertRow(0)
        self.table_logs.setItem(0, 0, QTableWidgetItem(log["time"]))
        self.table_logs.setItem(0, 1, QTableWidgetItem(log["feed"]))
        
        status_item = QTableWidgetItem(log["status"])
        status_item.setForeground(QColor("#ef4444" if log["status"] == "REJECT" else "#eab308"))
        self.table_logs.setItem(0, 2, status_item)
        self.table_logs.setItem(0, 3, QTableWidgetItem(str(log["count"])))

    def _save_manual_snapshot(self):
        if self.last_frame is not None:
            path = self.thread.capture_manual_snapshot(self.last_frame)
            QMessageBox.information(self, "Snapshot Berhasil", f"Foto bukti disimpan ke:\n{os.path.basename(path)}")

    def _toggle_mute(self):
        self.thread.mute_alarm = self.btn_mute.isChecked()
        self.btn_mute.setText("Unmute Alarm" if self.thread.mute_alarm else "Mute Alarm Audio [M]")

    def _open_snapshot_folder(self):
        os.startfile(SNAPSHOT_DIR)

    def _change_camera_source(self):
        source = self.combo_source.currentData()
        self.thread.stop()
        self._start_thread(source)

    def _browse_source(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Pilih File Video / Citra", "", "Video & Images (*.mp4 *.avi *.mkv *.jpg *.png)")
        if file_path:
            self.thread.stop()
            self._start_thread(file_path)

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

def launch():
    app = QApplication(sys.argv)
    window = CCTVOperatorDashboard()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    launch()
