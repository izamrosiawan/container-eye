import os
import cv2
import time
import winsound
import threading
from PyQt6.QtCore import QThread, pyqtSignal
from src.camera import CameraStream
from src.detector import ContainerDetector
from src.hud import draw_hud
from src.db import InspectionDatabase
from config import (
    PORT_NAME, GATE_NAME, CAMERA_SOURCE, CLASS_NAMES, CLASS_COLORS,
    CRITICAL_CLASSES, SNAPSHOT_DIR, MODEL_PATH, CONF_THRESHOLD
)

def trigger_audio_alarm():
    try:
        winsound.Beep(2000, 200)
    except Exception:
        pass

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(object)
    telemetry_signal = pyqtSignal(dict)
    log_signal = pyqtSignal(dict)

    def __init__(self, camera_source=CAMERA_SOURCE):
        super().__init__()
        self.camera_source = camera_source
        self.is_running = True
        self.is_paused = False
        self.mute_alarm = False
        self.detector = ContainerDetector(MODEL_PATH, conf_thresh=CONF_THRESHOLD)
        self.db = InspectionDatabase()

    def set_source(self, source):
        self.camera_source = source

    def run(self):
        cam = CameraStream(self.camera_source)
        last_time = time.time()
        fps = 0.0
        last_alarm_time = 0

        while self.is_running:
            if self.is_paused:
                time.sleep(0.05)
                continue

            ret, frame, label_path, frame_id = cam.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            # Deteksi Kerusakan
            detections, latency_ms = self.detector.detect(frame, label_path=label_path)

            # Hitung Smooth FPS
            now = time.time()
            fps = 0.9 * fps + 0.1 * (1.0 / max(1e-5, now - last_time))
            last_time = now

            # Render HUD ke frame
            annotated_frame, is_critical = draw_hud(
                frame.copy(), detections, latency_ms, fps,
                PORT_NAME, GATE_NAME, frame_id,
                CLASS_NAMES, CLASS_COLORS, CRITICAL_CLASSES
            )

            # Keputusan Kelaikan Gerbang
            if is_critical:
                status = "REJECT"
                if not self.mute_alarm and (now - last_alarm_time > 1.2):
                    last_alarm_time = now
                    threading.Thread(target=trigger_audio_alarm, daemon=True).start()
            elif len(detections) > 0:
                status = "CAUTION"
            else:
                status = "PASS"

            # Auto-save & Log ke DB jika Cacat Kritis
            snap_path = ""
            if is_critical and (now - last_alarm_time < 0.2):
                snap_name = f"ALERT_{time.strftime('%Y%m%d_%H%M%S')}_{frame_id}"
                snap_path = os.path.join(SNAPSHOT_DIR, snap_name)
                cv2.imwrite(snap_path, frame)
                
                defects_str = ", ".join([CLASS_NAMES.get(d['class_id'], '') for d in detections])
                self.db.log_record(frame_id, status, len(detections), defects_str, latency_ms, snap_path)
                self.log_signal.emit({
                    "time": time.strftime("%H:%M:%S"),
                    "feed": frame_id,
                    "status": status,
                    "count": len(detections),
                    "snapshot": snap_path
                })

            # Emit sinyal frame dan telemetri ke GUI
            self.change_pixmap_signal.emit(annotated_frame)
            self.telemetry_signal.emit({
                "fps": fps,
                "latency_ms": latency_ms,
                "status": status,
                "defect_count": len(detections),
                "is_critical": is_critical
            })

            time.sleep(0.01)

        cam.release()

    def capture_manual_snapshot(self, frame):
        snap_name = f"MANUAL_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
        snap_path = os.path.join(SNAPSHOT_DIR, snap_name)
        cv2.imwrite(snap_path, frame)
        return snap_path

    def stop(self):
        self.is_running = False
        self.wait()
