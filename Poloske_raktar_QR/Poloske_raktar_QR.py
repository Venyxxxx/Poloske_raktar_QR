import cv2
import time

# RTSP stream URL
rtsp_url = 'rtsp://admin:Portal2008@192.168.6.88:554/cam/realmonitor?channel=1&subtype=0'

# Kamera megnyitása
cap = cv2.VideoCapture(rtsp_url)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)


# QR kód detektor inicializálása
qr_detector = cv2.QRCodeDetector()

cv2.namedWindow('RTSP Stream with QR Detection', cv2.WINDOW_NORMAL)
cv2.resizeWindow('RTSP Stream with QR Detection', 1280, 720)

while True:
    start_time = time.perf_counter()
    ret, frame = cap.read()
    end_time = time.perf_counter()
    
    read_duration = (end_time - start_time) * 1000
    
    if not ret:
        print("Hiba: nem sikerült képkockát olvasni.")
        break

    # QR-kód detektálás és dekódolás
    data, bbox, _ = qr_detector.detectAndDecode(frame)
    
    # Ha van QR-kód
    if bbox is not None and data:
        # Rajzolj köré keretet
        bbox = bbox.astype(int)
        for i in range(len(bbox[0])):
            pt1 = tuple(bbox[0][i])
            pt2 = tuple(bbox[0][(i + 1) % len(bbox[0])])
            cv2.line(frame, pt1, pt2, (0, 255, 0), 2)
        
        # Írd ki a dekódolt adatot a kép tetejére
        cv2.putText(frame, f"QR: {data}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        print(f"QR kód tartalma: {data}")
    
    # Kiírjuk a pufferolási időt (képkocka olvasási időt)
    cv2.putText(frame, f"Frame read time: {read_duration:.1f} ms", (10, frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    # Kép megjelenítése
    cv2.imshow('RTSP Stream with QR Detection', frame)

    # Kilépés ESC-re (kód: 27)
    if cv2.waitKey(1) == 27:
        break

# Erőforrások felszabadítása
cap.release()
cv2.destroyAllWindows()
