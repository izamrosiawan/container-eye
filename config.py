import os

# Konfigurasi CCTV Kamera Realtime
PORT_NAME = "PELABUHAN TANJUNG PERAK"
GATE_NAME = "GATE 03"

# Default Camera Hardware ID: 0 (Webcam / USB Camera / RTSP Link)
CAMERA_SOURCE = 0

# Ambang Batas Deteksi
CONF_THRESHOLD = 0.35

# Kategori Cacat Fisik Kontainer (YOLO Classes)
CLASS_NAMES = {
    0: "Dent",
    1: "Rust",
    2: "Hole",
    3: "Deframe"
}

# Warna Garis BGR (OpenCV)
CLASS_COLORS = {
    "Dent": (0, 215, 255),      # Kuning
    "Rust": (0, 140, 255),      # Oranye
    "Hole": (0, 0, 255),        # Merah
    "Deframe": (255, 0, 255)    # Magenta
}

# Kerusakan Kritis yang Membatalkan Kelaikan IICL-6
CRITICAL_CLASSES = ["Hole", "Deframe"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT_DIR = os.path.join(BASE_DIR, "logs", "snapshots")
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

MODEL_PATH = os.path.join(BASE_DIR, "models", "yolov8n.pt")
