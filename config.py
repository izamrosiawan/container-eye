import os

PORT_NAME = "PELABUHAN TANJUNG PERAK SURABAYA"
GATE_NAME = "INSPECTION GATE 03 - AUTO PORTAL"

CAMERA_SOURCE = "assets/sample_images"

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

CONF_THRESHOLD = 0.30
IOU_THRESHOLD = 0.45

CLASS_NAMES = {
    0: "Dent",
    1: "Rust",
    2: "Hole",
    3: "Deframe"
}

CLASS_COLORS = {
    "Dent": (0, 215, 255),      # Kuning / Emas
    "Rust": (0, 140, 255),      # Oranye
    "Hole": (0, 0, 255),        # Merah Menyala (Kritis)
    "Deframe": (255, 0, 255)    # Magenta (Kritis)
}

CRITICAL_CLASSES = ["Hole", "Deframe"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT_DIR = os.path.join(BASE_DIR, "logs", "snapshots")
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

MODEL_PATH = os.path.join(BASE_DIR, "models", "best.pt")
