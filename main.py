import os
import cv2
import time
import winsound
import threading
from config import (
    PORT_NAME, GATE_NAME, CAMERA_SOURCE, WINDOW_WIDTH, WINDOW_HEIGHT,
    CLASS_NAMES, CLASS_COLORS, CRITICAL_CLASSES, SNAPSHOT_DIR, MODEL_PATH,
    CONF_THRESHOLD
)
from src.camera import CameraStream
from src.detector import ContainerDetector
from src.hud import draw_hud

def play_alarm():
    try:
        winsound.Beep(1800, 250)
    except Exception:
        pass

def main():
    print("=" * 60)
    print(f" CONTAINER-EYE : CCTV EDGE INSPECTOR")
    print(f" Port: {PORT_NAME}")
    print(f" Gate: {GATE_NAME}")
    print("=" * 60)
    print(" [Petunjuk Operator]")
    print(" - Tekan 'q' untuk keluar")
    print(" - Tekan 's' untuk simpan snapshot manual")
    print(" - Tekan 'm' untuk toggle mute alarm")
    print("=" * 60)

    cam = CameraStream(CAMERA_SOURCE)
    detector = ContainerDetector(MODEL_PATH, conf_thresh=CONF_THRESHOLD)

    cv2.namedWindow("Container-Eye CCTV Monitor", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Container-Eye CCTV Monitor", WINDOW_WIDTH, WINDOW_HEIGHT)

    last_time = time.time()
    fps = 0.0
    last_alarm_time = 0
    mute_alarm = False

    while True:
        ret, frame, label_path, frame_id = cam.read()
        if not ret or frame is None:
            time.sleep(0.01)
            continue

        # Resize ke tampilan kerja jika perlu
        frame = cv2.resize(frame, (WINDOW_WIDTH, WINDOW_HEIGHT))

        # Deteksi kerusakan
        detections, latency_ms = detector.detect(frame, label_path=label_path)

        # Hitung FPS
        now = time.time()
        fps = 0.9 * fps + 0.1 * (1.0 / max(1e-5, now - last_time))
        last_time = now

        # Render HUD
        annotated_frame, is_critical = draw_hud(
            frame, detections, latency_ms, fps,
            PORT_NAME, GATE_NAME, frame_id,
            CLASS_NAMES, CLASS_COLORS, CRITICAL_CLASSES
        )

        # Trigger alarm jika terdeteksi kerusakan kritis
        if is_critical and not mute_alarm:
            if now - last_alarm_time > 1.5:
                last_alarm_time = now
                threading.Thread(target=play_alarm, daemon=True).start()
                # Simpan snapshot bukti otomatis
                snap_name = f"ALERT_{time.strftime('%Y%m%d_%H%M%S')}_{frame_id}"
                snap_path = os.path.join(SNAPSHOT_DIR, snap_name)
                cv2.imwrite(snap_path, frame)

        cv2.imshow("Container-Eye CCTV Monitor", annotated_frame)
        key = cv2.waitKey(20) & 0xFF

        if key == ord('q'):
            break
        elif key == ord('s'):
            snap_name = f"MANUAL_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(os.path.join(SNAPSHOT_DIR, snap_name), frame)
            print(f"[SNAPSHOT] Tersimpan ke logs/snapshots/{snap_name}")
        elif key == ord('m'):
            mute_alarm = not mute_alarm
            print(f"[ALARM] Mute status: {mute_alarm}")

    cam.release()
    cv2.destroyAllWindows()
    print("[SYSTEM] Monitor CCTV dihentikan.")

if __name__ == "__main__":
    main()
