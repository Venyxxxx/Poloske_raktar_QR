import cv2
from threading import Thread
import tkinter as tk
from PIL import Image, ImageTk
from pyzbar.pyzbar import decode
import numpy as np

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

# --- Dahua RTSP substream ---
rtsp_url = "rtsp://admin:Portal2008@192.168.6.88:554/cam/realmonitor?channel=1&subtype=1"

# Tkinter GUI
class App(tk.Tk):
    def __init__(self, video_stream):
        super().__init__()
        self.title("QR Scanner")
        self.attributes("-fullscreen", True)
        self.video_stream = video_stream
        self.detected_qr_data = []
        self.qr_locked = False

        # Kamera kép Frame
        video_frame = tk.Frame(self, bg="black")
        video_frame.place(relx=0, rely=0, relwidth=0.5, relheight=0.8)

        # QR Info rész
        info_frame = tk.Frame(self, bg="white")
        info_frame.place(relx=0.5, rely=0, relwidth=0.5, relheight=0.8)

        self.qr_label = tk.Label(info_frame, text="QR kód nincs detektálva", font=("Arial", 24), bg="white", wraplength=350)
        self.qr_label.pack(padx=10, pady=20)

        # Színes értesítő sáv
        self.green_notification = tk.Frame(self, bg="gray")
        self.green_notification.place(relx=0, rely=0.8, relwidth=1, relheight=0.2)

        self.video_label = tk.Label(video_frame)
        self.video_label.pack(fill=tk.BOTH, expand=True)

        self.update_frame()

    def update_frame(self):
        frame = self.video_stream.read()
        if frame is not None:
            decoded_objects = decode(frame)
            good_qr_found = False
            any_qr_found = False

            for obj in decoded_objects:
                data = obj.data.decode("utf-8")
                any_qr_found = True

                # Doboz kirajzolása
                pts = obj.polygon
                if len(pts) > 4:
                    hull = cv2.convexHull(np.array(pts, dtype=np.float32))
                    pts = list(map(tuple, np.squeeze(hull)))
                else:
                    pts = list(map(tuple, pts))

                for i in range(len(pts)):
                    cv2.line(frame, pts[i], pts[(i + 1) % len(pts)], (0, 255, 0), 2)

                if "PALLET" in data:
                    if not self.qr_locked:
                        if data not in self.detected_qr_data:
                            print(f"Helyes QR: {data}")
                            self.detected_qr_data.append(data)
                        self.qr_label.config(text=f"Helyes QR kód:\n{data}")
                        self.green_notification.config(bg="green")
                        self.qr_locked = True
                        self.after(5000, self.reset_notification)
                        good_qr_found = True
                        break

            if good_qr_found:
                self.after(5000, self.reset_notification)

            # Kép konvertálás
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)

            width = self.video_label.winfo_width()
            height = self.video_label.winfo_height()
            if width > 0 and height > 0:
                img = img.resize((width, height), Image.Resampling.LANCZOS)

            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

        self.after(30, self.update_frame)

    def reset_notification(self):
        self.green_notification.config(bg="gray")
        self.qr_label.config(text="QR kód nincs detektálva")
        self.qr_locked = False


    def on_closing(self):
        self.video_stream.stop()
        self.destroy()

if __name__ == "__main__":
    vs = VideoStream(rtsp_url)
    app = App(vs)
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
