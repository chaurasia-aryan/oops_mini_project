# cv.py
# Camera-based Snake Game, Live Filters, and Mood Detector for TakeBook

import cv2
import mediapipe as mp
import numpy as np
import random
import math
from collections import deque
from tkinter import Toplevel, Label, Button, ttk, messagebox
from PIL import Image, ImageTk

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

# ------------------- Snake Game -------------------
def play_hand_snake():
    snake = deque()
    snake_len = 10
    food = None
    score = 0

    def new_food(w, h):
        return [random.randint(50, w - 50), random.randint(50, h - 50)]

    def dist(a, b):
        return math.hypot(a[0] - b[0], a[1] - b[1])

    cap = cv2.VideoCapture(0)
    width, height = 640, 480
    cap.set(3, width)
    cap.set(4, height)

    hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
    food = new_food(width, height)

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                x = int(hand_landmarks.landmark[8].x * width)
                y = int(hand_landmarks.landmark[8].y * height)
                head = [x, y]

                snake.append(head)
                if len(snake) > snake_len:
                    snake.popleft()

                # Eat food
                if dist(head, food) < 25:
                    score += 1
                    snake_len += 5
                    food = new_food(width, height)

                # Draw snake and food
                for i in range(1, len(snake)):
                    cv2.line(frame, tuple(snake[i - 1]), tuple(snake[i]), (0, 255, 0), 15)
                cv2.circle(frame, tuple(head), 10, (0, 0, 255), -1)
                cv2.circle(frame, tuple(food), 10, (255, 0, 0), -1)
                cv2.putText(frame, f"Score: {score}", (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                # Self collision
                if len(snake) > 10:
                    for i in range(len(snake) - 10):
                        if dist(head, snake[i]) < 10:
                            cv2.putText(frame, "GAME OVER", (180, 250),
                                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
                            cv2.imshow("Snake Game", frame)
                            cv2.waitKey(1500)
                            cap.release()
                            cv2.destroyAllWindows()
                            return

                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        cv2.imshow("Snake Game", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


# ------------------- Live Filters -------------------
class VideoFilterWindow(Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Live Video Filters 🎥")
        self.geometry("720x520")
        self.resizable(False, False)

        Label(self, text="Choose Filter:", font=("Helvetica Bold", 12)).pack(pady=10)
        self.filter_var = ttk.Combobox(self, values=["Normal", "Grayscale", "Sepia", "Invert", "Blur", "Cartoon"], state="readonly")
        self.filter_var.current(0)
        self.filter_var.pack(pady=5)

        self.video_label = Label(self, bg="black")
        self.video_label.pack(padx=10, pady=10, fill="both", expand=True)

        Button(self, text="Close", bg="#e74c3c", fg="white", command=self.close_camera).pack(pady=10)

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Could not open camera!")
            self.destroy()
            return

        self.running = True
        self.update_frame()

    def apply_filter(self, frame):
        f = self.filter_var.get()
        if f == "Grayscale":
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        elif f == "Sepia":
            kernel = np.array([[0.272, 0.534, 0.131],
                               [0.349, 0.686, 0.168],
                               [0.393, 0.769, 0.189]])
            frame = cv2.transform(frame, kernel)
            frame = np.clip(frame, 0, 255).astype("uint8")
        elif f == "Invert":
            frame = cv2.bitwise_not(frame)
        elif f == "Blur":
            frame = cv2.GaussianBlur(frame, (15, 15), 0)
        elif f == "Cartoon":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.medianBlur(gray, 5)
            edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                          cv2.THRESH_BINARY, 9, 9)
            color = cv2.bilateralFilter(frame, 9, 250, 250)
            frame = cv2.bitwise_and(color, color, mask=edges)
        return frame

    def update_frame(self):
        if not self.running:
            return
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            frame = self.apply_filter(frame)
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            imgtk = ImageTk.PhotoImage(Image.fromarray(img))
            self.video_label.imgtk = imgtk
            self.video_label.config(image=imgtk)
        self.after(10, self.update_frame)

    def close_camera(self):
        self.running = False
        if self.cap.isOpened():
            self.cap.release()
        self.destroy()


# Mood detetctor using Haar cascades
class MoodDetectorWindow(Toplevel):
  

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Mood Detector")
        self.geometry("720x520")
        self.resizable(False, False)

        Label(self, text="Mood Detector (local)", font=("Helvetica Bold", 12)).pack(pady=8)
        self.status_label = Label(self, text="Initializing...", font=("Arial", 14))
        self.status_label.pack(pady=6)

        self.video_label = Label(self, bg="black")
        self.video_label.pack(padx=10, pady=10, fill="both", expand=True)

        Button(self, text="Close", bg="#e74c3c", fg="white", command=self.close_camera).pack(pady=8)

        # load cascades
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_smile.xml")

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Camera Error", "Could not open camera!")
            self.destroy()
            return

        self.running = True
        self.update_frame()

    def update_frame(self):
        if not self.running:
            return
        ret, frame = self.cap.read()
        if not ret:
            self.after(100, self.update_frame)
            return

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))

        mood = "BT"
        for (x, y, w, h) in faces:
            # draw a rectangle around face
            cv2.rectangle(frame, (x, y), (x + w, y + h), (90, 200, 255), 2)

            # detect smiles inside face ROI
            roi_gray = gray[y:y + h, x:x + w]
            smiles = self.smile_cascade.detectMultiScale(roi_gray, scaleFactor=1.7, minNeighbors=20)

            if len(smiles) > 0:
                mood ="kush"
                # draws dabbe around smiles
                for (sx, sy, sw, sh) in smiles:
                    cv2.rectangle(frame, (x + sx, y + sy), (x + sx + sw, y + sy + sh), (0, 255, 0), 1)
                break

        
        cv2.putText(frame, f"Mood: {mood}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)
        
        self.status_label.config(text=f"Detected mood: {mood}")

        # Convert to PhotoImage and show in label
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        imgtk = ImageTk.PhotoImage(Image.fromarray(img))
        self.video_label.imgtk = imgtk
        self.video_label.config(image=imgtk)

        self.after(60, self.update_frame) 

    def close_camera(self):
        self.running = False
        if hasattr(self, "cap") and self.cap.isOpened():
            self.cap.release()
        self.destroy()
