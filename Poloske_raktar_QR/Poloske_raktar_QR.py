import cv2
from threading import Thread

# Async video stream class
class VideoStream:
    def __init__(self, src):
        self.src = src
        self.cap = cv2.VideoCapture(self.src)
        self.frame = None
        self.running = True
        self.thread = Thread(target=self.update, daemon=True)
        self.thread.start()

    def update(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                self.frame = frame

    def read(self):
        return self.frame

    def stop(self):
        self.running = False
        self.thread.join()
        self.cap.release()

# --- Dahua RTSP substream (lower latency) ---
rtsp_url = "rtsp://admin:Portal2008@192.168.6.88:554/cam/realmonitor?channel=1&subtype=1"

#szoveg

# Start the video stream
vs = VideoStream(rtsp_url)
qr_detector = cv2.QRCodeDetector()

print("Press ESC to exit")

while True:
    frame = vs.read()
    if frame is None:
        continue

    # Detect QR code
    data, points, _ = qr_detector.detectAndDecode(frame)
    if points is not None and data:
        print(f"QR Code Detected: {data}")
        # Draw QR bounding box
        pts = points[0].astype(int)
        for i in range(len(pts)):
            cv2.line(frame, tuple(pts[i]), tuple(pts[(i+1)%4]), (0, 255, 0), 2)

    cv2.imshow("QR Code Scanner (RTSP Stream)", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

# Cleanup
vs.stop()
cv2.destroyAllWindows()
