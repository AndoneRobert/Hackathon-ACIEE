import cv2
import mediapipe as mp
import math
import time
import numpy as np

class GestureEngine:
    def __init__(self):
        # MediaPipe initializations
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            model_complexity=0,       # <--- CRITICAL OPTIMIZATION (0=Lite, 1=Full)
            min_detection_confidence=0.5, # Lowered slightly for speed
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # State variables
        self.prev_x, self.prev_y = 0, 0
        self.smoothing_factor = 0.5
        
        # Swipe detection variables
        self.hand_positions = []
        self.swipe_cooldown = 0
        
    def process_frame(self, frame):
        # ... (Rest of the code remains exactly the same) ...
        # Just copy the process_frame, _detect_swipe, and draw_debug_ui methods 
        # from your original file here.
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(frame_rgb)
        
        data = {
            "cursor_detected": False,
            "x": 0, "y": 0,
            "gesture": None,
            "landmarks": None
        }

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                data["cursor_detected"] = True
                data["landmarks"] = hand_landmarks
                
                h, w, c = frame.shape
                index_tip = hand_landmarks.landmark[8]
                
                curr_x = index_tip.x
                curr_y = index_tip.y
                
                smooth_x = self.prev_x + (curr_x - self.prev_x) * self.smoothing_factor
                smooth_y = self.prev_y + (curr_y - self.prev_y) * self.smoothing_factor
                
                self.prev_x, self.prev_y = smooth_x, smooth_y
                
                data["x"] = smooth_x
                data["y"] = smooth_y

                thumb_tip = hand_landmarks.landmark[4]
                
                distance = math.hypot(
                    (index_tip.x - thumb_tip.x) * w, 
                    (index_tip.y - thumb_tip.y) * h
                )
                
                if distance < 40:
                    data["gesture"] = "CLICK"
                
                self._detect_swipe(smooth_x, data)
                
        return data

    def _detect_swipe(self, current_x, data):
        if self.swipe_cooldown > 0:
            self.swipe_cooldown -= 1
            return

        self.hand_positions.append(current_x)
        if len(self.hand_positions) > 10:
            self.hand_positions.pop(0)
            
        if len(self.hand_positions) == 10:
            displacement = self.hand_positions[-1] - self.hand_positions[0]
            if displacement > 0.20: 
                data["gesture"] = "SWIPE_LEFT"
                self.swipe_cooldown = 15
                self.hand_positions = []
            elif displacement < -0.20:
                data["gesture"] = "SWIPE_RIGHT"
                self.swipe_cooldown = 15
                self.hand_positions = []

    def draw_debug_ui(self, frame, data):
        h, w, _ = frame.shape
        if data["cursor_detected"]:
            cx, cy = int(data["x"] * w), int(data["y"] * h)
            cv2.circle(frame, (cx, cy), 15, (0, 255, 0), cv2.FILLED)
            if data["gesture"]:
                cv2.putText(frame, f"GESTURE: {data['gesture']}", (50, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            self.mp_draw.draw_landmarks(frame, data["landmarks"], self.mp_hands.HAND_CONNECTIONS)
        return frame