import os
import time
from ultralytics import YOLO

class ContainerDetector:
    def __init__(self, model_path, conf_thresh=0.35):
        self.conf_thresh = conf_thresh
        self.model = YOLO(model_path)

    def detect(self, frame):
        t0 = time.perf_counter()
        results = self.model.predict(frame, conf=self.conf_thresh, verbose=False)
        detections = []
        for r in results:
            for b in r.boxes:
                xyxy = b.xyxy[0].cpu().numpy().astype(int)
                conf = float(b.conf[0].cpu().numpy())
                cls_id = int(b.cls[0].cpu().numpy())
                detections.append({
                    "box": xyxy.tolist(),
                    "class_id": cls_id,
                    "confidence": conf
                })
        latency_ms = (time.perf_counter() - t0) * 1000.0
        return detections, latency_ms
