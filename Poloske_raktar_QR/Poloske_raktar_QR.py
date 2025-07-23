import cv2
from threading import Thread
import tkinter as tk
from PIL import Image, ImageTk

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

# Tkinter GUI
class App(tk.Tk):
    def __init__(self, video_stream):
        super().__init__()
        self.title("QR Scanner")
        self.attributes("-fullscreen", True)
        self.video_stream = video_stream
        self.qr_data = None

        # Kamera képet megjelenítő Frame (az ablak kb 2/3 részét foglalja)
        video_frame = tk.Frame(self, bg="black")
        video_frame.place(relx=0, rely=0, relwidth=0.4, relheight=0.8)

        # Info rész - például QR kód szöveg megjelenítése
        info_frame = tk.Frame(self, bg="white")
        info_frame.place(relx=0.4, rely=0, relwidth=0.7, relheight=0.8)

        self.qr_label = tk.Label(info_frame, text="QR kód nincs detektálva", font=("Arial", 14), bg="white", wraplength=280)
        self.qr_label.pack(padx=10, pady=20)

        # Zöld jelzés
        self.green_notification = tk.Frame(self, bg="gray")
        self.green_notification.place(relx=0, rely=0.8, relwidth=1, relheight=0.2)

        # Kamera képet megjelenítő Label (ide tesszük a képet)
        self.video_label = tk.Label(video_frame)
        self.video_label.pack(fill=tk.BOTH, expand=True)

        self.qr_detector = cv2.QRCodeDetector()

        self.update_frame()

    def update_frame(self):
        frame = self.video_stream.read()
        if frame is not None:
            # QR kód detektálás
            data, points, _ = self.qr_detector.detectAndDecode(frame)

            if points is not None and data:
                if data != self.qr_data:
                    self.qr_data = data
                    
                    expected_value = "PALLET"
                    if expected_value in data:  # ha jó QR kódot olvas be
                        self.qr_label.config(text=f"QR kód detektálva:\n{data}")
                        self.green_notification.config(bg="green") # turn green
                    else:   # ha rossz QR kódot olvas be
                        self.qr_label.config(text=f"Rossz QR kód:\n{data}")
                        self.green_notification.config(bg="red")  # turn red

                    self.after(3000, self.reset_notification)  # 3 másodperc után visszaállítja a színt
            else:
                self.qr_data = None

            # BGR -> RGB konverzió
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            
            img = img.resize((600, 600), Image.Resampling.LANCZOS)


            imgtk = ImageTk.PhotoImage(image=img)

            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

        # Újramegjelenítés 30 ms-ként (~33 FPS)
        self.after(30, self.update_frame)

    def reset_notification(self):
        self.green_notification.config(bg="gray")
        self.qr_label.config(text="Új QR kód nincs detektálva")

    def on_closing(self):
        self.video_stream.stop()
        self.destroy()

if __name__ == "__main__":
    vs = VideoStream(rtsp_url)
    app = App(vs)
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
