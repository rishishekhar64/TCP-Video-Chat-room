import tkinter as tk
from tkinter import simpledialog, messagebox
from PIL import Image, ImageTk
import socket
import struct
import cv2
import threading
import time
import pyaudio
import numpy as np
from cryptography.fernet import Fernet
import base64
import hashlib

PASSWORD = "secure123"

def get_cipher_key(password):
    hash_obj = hashlib.sha256(password.encode())
    return base64.urlsafe_b64encode(hash_obj.digest())

class VideoChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Zoom Clone Client")
        self.root.geometry("800x650")

        # Network Target Request
        self.server_ip = simpledialog.askstring("Connect to Host", "Enter Server IP Address:", initialvalue="127.0.0.1")
        if not self.server_ip:
            self.root.destroy()
            return

        # Core Socket Initialization
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip, 5555))
            print(f"Network linked successfully to stream host: {self.server_ip}")
        except Exception as e:
            messagebox.showerror("Network Fault", f"Could not bind to host gateway:\n{e}")
            self.root.destroy()
            return

        # Cryptography Layer
        self.cipher = Fernet(get_cipher_key(PASSWORD))
        self.running = True

        # View Layer Setup
        self.video_frame = tk.Frame(root, bg="black")
        self.video_frame.pack(side="top", fill="both", expand=True)

        self.remote_label = tk.Label(self.video_frame, bg="black", text="Waiting for Remote Stream...", fg="gray")
        self.remote_label.pack(side="left", fill="both", expand=True)

        self.local_label = tk.Label(self.video_frame, bg="black", text="Self Preview", fg="gray")
        self.local_label.pack(side="right", fill="both", expand=True)

        chat_frame = tk.Frame(root)
        chat_frame.pack(fill="x", padx=10, pady=5)

        self.chat_box = tk.Text(chat_frame, height=5, state="disabled")
        self.chat_box.pack(fill="x")

        self.msg_entry = tk.Entry(chat_frame)
        self.msg_entry.pack(fill="x", pady=5)
        self.msg_entry.bind("<Return>", self.send_message)

        tk.Button(chat_frame, text="Send Message", command=self.send_message).pack()

        status_frame = tk.Frame(root)
        status_frame.pack(fill="x", padx=10)
        tk.Label(status_frame, text="🔒 E2E Encrypted Payload (Fernet AES-128)", fg="green").pack(side="left")

        # Native Hardware Audio Allocation
        self.p = pyaudio.PyAudio()
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16 
        self.CHANNELS = 1
        self.RATE = 44100

        self.stream = self.p.open(format=self.FORMAT, channels=self.CHANNELS,
                                   rate=self.RATE, input=True, output=True,
                                   frames_per_buffer=self.CHUNK)

        # Threaded Workers Execution
        threading.Thread(target=self.send_video, daemon=True).start()
        threading.Thread(target=self.send_audio, daemon=True).start()
        threading.Thread(target=self.receive_data, daemon=True).start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def send_message(self, event=None):
        msg = self.msg_entry.get()
        if not msg:
            return

        encrypted = self.cipher.encrypt(msg.encode())
        header = struct.pack("!BL", 1, len(encrypted)) # 1 = Text Chat
        try:
            self.socket.sendall(header + encrypted)
            self.log_message(f"You: {msg}")
            self.msg_entry.delete(0, tk.END)
        except:
            self.log_message("System: Data packet transmit failed.")

    def send_video(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

        while self.running:
            ret, frame = cap.read()
            if ret:
                self.show_image(frame, self.local_label)

                # Direct memory buffer serialization (Skip Pickle Overhead)
                _, img_encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 55])
                raw_bytes = img_encoded.tobytes()
                
                encrypted = self.cipher.encrypt(raw_bytes)
                header = struct.pack("!BL", 0, len(encrypted)) # 0 = Video Matrix
                try:
                    self.socket.sendall(header + encrypted)
                except:
                    break
            time.sleep(0.04) # Enforces safe frame cadence (~25 FPS limit)

        cap.release()

    def send_audio(self):
        while self.running:
            try:
                audio_data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                encrypted = self.cipher.encrypt(audio_data)
                header = struct.pack("!BL", 2, len(encrypted)) # 2 = Audio Wave
                self.socket.sendall(header + encrypted)
            except:
                break
            time.sleep(0.01)

    def receive_data(self):
        buffer = b""
        header_size = 5

        while self.running:
            try:
                while len(buffer) < header_size:
                    chunk = self.socket.recv(16384)
                    if not chunk:
                        return
                    buffer += chunk

                msg_type, size = struct.unpack("!BL", buffer[:header_size])
                buffer = buffer[header_size:]

                while len(buffer) < size:
                    chunk = self.socket.recv(16384)
                    if not chunk:
                        return
                    buffer += chunk

                payload = buffer[:size]
                buffer = buffer[size:]

                decrypted = self.cipher.decrypt(payload)

                if msg_type == 0:    # Video
                    np_arr = np.frombuffer(decrypted, dtype=np.uint8)
                    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    if frame is not None:
                        self.show_image(frame, self.remote_label)
                elif msg_type == 1:  # Text
                    self.log_message(f"Other: {decrypted.decode()}")
                elif msg_type == 2:  # Audio
                    self.stream.write(decrypted)
            except:
                break

    def show_image(self, cv_frame, label):
        rgb = cv2.cvtColor(cv_frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        photo = ImageTk.PhotoImage(image=img)
        label.config(image=photo)
        label.image = photo

    def log_message(self, msg):
        self.chat_box.config(state="normal")
        self.chat_box.insert(tk.END, msg + "\n")
        self.chat_box.config(state="disabled")
        self.chat_box.see(tk.END)

    def on_close(self):
        self.running = False
        try:
            self.stream.stop_stream()
            self.stream.close()
            self.p.terminate()
            self.socket.close()
        except:
            pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoChatApp(root)
    root.mainloop()