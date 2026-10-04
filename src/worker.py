import os
import cv2
import time
import winsound
import threading
from PyQt6.QtCore import QThread, pyqtSignal
from src.camera import CameraStream
from src.detector import ContainerDetector
from src.hud import draw_clean_hud
from config import CAMERA_SOURCE, CLASS_NAMES, CLASS_COLORS, CRITICAL_CLASSES, MODEL_PATH, CONF_THRESHOLD, SNAPSHOT_DIR

def beep_alert():
    try:
        winsound.Beep(1800, 150)
    except Exception:
        pass

class RealtimeCameraWorker(QThread):
    frame_signal = pyqtSignal(object)
    telemetry_signal = pyqtSignal(dict)
    alert_signal = pyqtSignal(str)

    def __init__(self, camera_id=CAMERA_SOURCE):
        super().__init__()
        self.camera_id = camera_id
        self.is_running = True
        self.mute_alarm = False
        self.detector = ContainerDetector(MODEL_PATH, conf_thresh=CONF_THRESHOLD)

    def run(self):
        try:
            cam = CameraStream(self.camera_id)
        except Exception as e:
            print(f"[ERROR] {e}")
            return

        last_time = time.time()
        fps = 0.0
        last_alarm_time = 0

        while self.is_running:
            ret, frame = cam.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            # Inferensi YOLO Realtime
            detections, latency_ms = self.detector.detect(frame)

            # Hitung Smooth FPS
            now = time.time()
            fps = 0.9 * fps + 0.1 * (1.0 / max(1e-5, now - last_time))
            last_time = now

            # Gambar visual box yang bersih
            annotated_frame, is_critical = draw_clean_hud(
                frame, detections, CLASS_NAMES, CLASS_COLORS, CRITICAL_CLASSES
            )

            # Alarm jika ada objek kritis
            if is_critical:
                if not self.mute_alarm and (now - last_alarm_time > 1.5):
                    last_alarm_time = now
                    threading.Thread(target=beep_alert, daemon=True).start()
                    snap_path = os.path.join(SNAPSHOT_DIR, f"ALERT_{time.strftime('%Y%m%d_%H%M%S')}.jpg")
                    cv2.imwrite(snap_path, frame)
                    self.alert_signal.emit(f"Cacat Kritis Terdeteksi - Snapshot: {os.path.basename(snap_path)}")

            self.frame_signal.emit(annotated_frame)
            self.telemetry_signal.emit({
                "fps": fps,
                "latency_ms": latency_ms,
                "count": len(detections),
                "is_critical": is_critical
            })

            time.sleep(0.005)

        cam.release()

    def stop(self):
        self.is_running = False
        self.wait()
