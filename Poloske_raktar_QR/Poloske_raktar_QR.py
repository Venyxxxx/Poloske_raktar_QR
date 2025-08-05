import cv2
from threading import Thread
import tkinter as tk
from PIL import Image, ImageTk
from pyzbar.pyzbar import decode
import numpy as np
from tkhtmlview import HTMLLabel
import time
import json

# Async video stream class
class VideoStream:
    def __init__(self, src):
        self.src = src
        self.cap = None
        self.frame = None
        self.running = True
        self.thread = Thread(target=self.update, daemon=True)
        self.thread.start()
        


    def update(self):
       print(f"[DEBUG] VideoStream thread started for source: {self.src}")
       while self.running:
            if self.cap is None or not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.src, cv2.CAP_FFMPEG)
                if not self.cap.isOpened():
                    print("[INFO] Kamera nem elérhető, újrapróbálkozás...")
                    self.frame = None
                    for _ in range(10):  # Check for stop every 0.1s for 1s
                        if not self.running:
                            return
                        time.sleep(0.1)
                    continue
            ret, frame = self.cap.read()
            if ret:
                self.frame = frame
            else:
                print("[INFO] Nem sikerült képkockát olvasni, újrapróbálkozás...")
                self.frame = None
                self.cap.release()
                self.cap = None
       print(f"[DEBUG] Exiting stream thread for {self.src}")

    def read(self):
        return self.frame

    def stop(self):
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=2)
        if self.cap:
            self.cap.release()


def load_cameras(json_path="config.json"):
    with open(json_path, "r", encoding="latin-1") as f:
        data = json.load(f)
    return data["cameras"]

# Tkinter -
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("QR Scanner")
        self.attributes("-fullscreen", True)
        self.video_stream = None
        self.detected_qr_data = []
        self.qr_locked = False

        self.cameras = load_cameras()
        self.camera_names = [cam["name"] for cam in self.cameras]
        self.selected_camera = tk.StringVar(value=self.camera_names[0])

        # Kamera kiválasztó menü
        camera_selector = tk.OptionMenu(self, self.selected_camera, *self.camera_names)
        camera_selector.config(font=("Arial", 14))
        camera_selector.place(relx=0.02, rely=0.01)

        # Event kezelő a kamera váltására
        self.selected_camera.trace_add("write", lambda *args: self.change_camera(self.selected_camera.get()))

        # Kamera kép Frame
        video_frame = tk.Frame(self, bg="black")
        video_frame.place(relx=0, rely=0.05, relwidth=0.5, relheight=0.75)

        # Kamera várokozó szöveg
        self.waiting_label = tk.Label(video_frame, text="Kamera betöltése...", font=("Arial", 24))
        self.waiting_label.pack(fill=tk.BOTH, expand=True)

        # QR Info rész
        self.info_frame = tk.Frame(self, bg="white")
        self.info_frame.place(relx=0.5, rely=0, relwidth=0.5, relheight=0.8)

        # Színes értesítő sáv
        self.green_notification = tk.Frame(self, bg="gray")
        self.green_notification.place(relx=0, rely=0.8, relwidth=1, relheight=0.2)

        self.video_label = tk.Label(video_frame)
        self.video_label.pack(fill=tk.BOTH, expand=True)

        default_url = self.get_selected_camera_url()
        self.video_stream = VideoStream(default_url)

        # Folyamatos frissítés
        self.after(30, self.update_frame)

    def get_selected_camera_url(self):
        selected_name = self.selected_camera.get()
        for cam in self.cameras:
            if cam["name"] == selected_name:
                # print(f"[DEBUG] URL for selected camera ({selected_name}): {cam['url']}")
                return cam["url"]
        return None

    
    def change_camera(self, selected_name):
             url = self.get_selected_camera_url()
             if url:
                # print(f"[INFO] Changing to new camera: {selected_name}")
                if self.video_stream:
                    self.video_stream.stop()
                    self.video_stream = None
                self.after(300, lambda: self.start_new_stream(url))

    def start_new_stream(self, url):
        self.video_stream = VideoStream(url)

    def show_api_response(self, qr_data):
        
        try:
            with open("index.html", "r", encoding="utf-8") as file:
                html_content = file.read()
        except Exception as e:
                html_content = f"<h3>Nem sikerült betölteni a HTML fájlt:<br>{str(e)}</h3>"

        html_label = HTMLLabel(self.info_frame, html=html_content)
        html_label.pack(fill="both", expand=True)

    def update_frame(self):
        frame = self.video_stream.read() if self.video_stream else None
        if frame is not None:
            # print("[DEBUG] Got frame from current video stream.")
            self.waiting_label.pack_forget()
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
                        # self.qr_label.config(text=f"Helyes QR kód:\n{data}")
                        self.green_notification.config(bg="green")
                        self.qr_locked = True
                        self.after(5000, self.reset_notification)
                        
                        self.show_api_response(data)

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
        # self.qr_label.config(text="QR kód nincs detektálva")
        for widget in self.info_frame.winfo_children():
            widget.destroy()

        self.qr_locked = False

    def on_closing(self):
        self.video_stream.stop()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
