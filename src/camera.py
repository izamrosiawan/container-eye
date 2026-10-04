import cv2

class CameraStream:
    def __init__(self, source=0):
        self.source = source
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            # Fallback jika kamera 0 gagal, coba string atau throw
            raise RuntimeError(f"Gagal membuka kamera input: {source}")

    def read(self):
        ret, frame = self.cap.read()
        return ret, frame

    def release(self):
        if self.cap is not None:
            self.cap.release()
