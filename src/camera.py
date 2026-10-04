import os
import glob
import cv2
import time

class CameraStream:
    def __init__(self, source):
        self.source = source
        self.is_image_folder = False
        self.cap = None
        self.image_files = []
        self.current_idx = 0
        self.last_img_time = 0
        self.cycle_interval = 2.5

        if isinstance(source, str) and os.path.isdir(source):
            self.is_image_folder = True
            exts = ("*.png", "*.jpg", "*.jpeg")
            for ext in exts:
                self.image_files.extend(glob.glob(os.path.join(source, ext)))
            self.image_files = sorted(self.image_files)
            if not self.image_files:
                raise ValueError(f"Tidak ada file citra di {source}")
        else:
            self.cap = cv2.VideoCapture(source)
            if not self.cap.isOpened():
                raise RuntimeError(f"Gagal membuka input kamera/video: {source}")

    def read(self):
        if self.is_image_folder:
            now = time.time()
            if now - self.last_img_time > self.cycle_interval:
                self.last_img_time = now
                self.current_idx = (self.current_idx + 1) % len(self.image_files)
            
            img_path = self.image_files[self.current_idx]
            frame = cv2.imread(img_path)
            label_path = os.path.splitext(img_path)[0] + ".txt"
            return True, frame, label_path, os.path.basename(img_path)
        else:
            ret, frame = self.cap.read()
            if not ret and isinstance(self.source, str):
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
            return ret, frame, None, "LIVE_FEED"

    def release(self):
        if self.cap is not None:
            self.cap.release()
