# -*- coding: utf-8 -*-
import cv2
import time
from deepface import DeepFace

class VisionController:
    def __init__(self):
        self.prev_gray = None
        self.frame_count = 0  # 紀錄目前跑到第幾格
        self.cached_emotion = {'happy': 0, 'sad': 0, 'surprise': 0} # 暫存 AI 運算結果

    def process_frame(self, frame, current_task, last_trigger_time):
        self.frame_count += 1
        height, width = frame.shape[:2]
        center_x, center_y = width // 2, height // 2
        oval_color = (255, 255, 255)
        should_advance = False

        if current_task.startswith("emotion"):
            # 每 4 格才讓 DeepFace 算一次，攝影機瞬間變順暢！
            if self.frame_count % 4 == 0:
                try:
                    results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                    self.cached_emotion = results[0]['emotion']
                except: pass

            # 靈敏度提升：過關門檻降至 40，並使用 cached_emotion 判斷
            if current_task == "emotion_happy" and self.cached_emotion.get('happy', 0) > 55:
                oval_color = (0, 200, 100)
                if time.time() - last_trigger_time > 4: should_advance = True
            elif current_task == "emotion_sad" and self.cached_emotion.get('sad', 0) > 50:
                oval_color = (255, 100, 100)
                if time.time() - last_trigger_time > 4: should_advance = True
            elif current_task == "emotion_surprise" and self.cached_emotion.get('surprise', 0) > 55:
                oval_color = (200, 100, 255)
                if time.time() - last_trigger_time > 4: should_advance = True

        elif current_task == "motion_wave":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            if self.prev_gray is not None:
                diff = cv2.absdiff(self.prev_gray, gray)
                _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
                motion_level = cv2.countNonZero(thresh)
                # 揮手靈敏度提升：門檻從 15000 降到 10000
                if motion_level > 10000: 
                    oval_color = (0, 255, 255)
                    if time.time() - last_trigger_time > 4: should_advance = True
            self.prev_gray = gray

        cv2.ellipse(frame, (center_x, center_y), (120, 160), 0, 0, 360, oval_color, 2)
        return frame, should_advance