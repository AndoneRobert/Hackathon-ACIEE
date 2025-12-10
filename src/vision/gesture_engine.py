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
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # State variables
        self.prev_x, self.prev_y = 0, 0
        self.smoothing_factor = 0.5  # Lower = smoother but more lag (0.1 to 1.0)
        
        # Swipe detection variables
        self.hand_positions = []  # Stores recent x positions
        self.swipe_cooldown = 0
        
    def process_frame(self, frame):
        """
        Input: A standard OpenCV frame.
        Output: A dictionary containing cursor coordinates and gesture events.
        """
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(frame_rgb)
        
        data = {
            "cursor_detected": False,
            "x": 0, "y": 0,         # Normalized 0.0 to 1.0
            "gesture": None,        # "CLICK", "SWIPE_LEFT", "SWIPE_RIGHT" or None
            "landmarks": None
        }

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                data["cursor_detected"] = True
                data["landmarks"] = hand_landmarks
                
                # 1. GET INDEX FINGER TIP (Landmark 8)
                h, w, c = frame.shape
                index_tip = hand_landmarks.landmark[8]
                
                # 2. SMOOTHING LOGIC
                # We use a weighted average of the current and previous position
                curr_x = index_tip.x
                curr_y = index_tip.y
                
                # Interpolate to reduce jitter
                smooth_x = self.prev_x + (curr_x - self.prev_x) * self.smoothing_factor
                smooth_y = self.prev_y + (curr_y - self.prev_y) * self.smoothing_factor
                
                # Update history
                self.prev_x, self.prev_y = smooth_x, smooth_y
                
                data["x"] = smooth_x
                data["y"] = smooth_y

                # 3. DETECT PINCH (CLICK)
                # Calculate distance between Index Tip (8) and Thumb Tip (4)
                thumb_tip = hand_landmarks.landmark[4]
                
                # Euclidean distance calculation
                distance = math.hypot(
                    (index_tip.x - thumb_tip.x) * w, 
                    (index_tip.y - thumb_tip.y) * h
                )
                
                # If fingers are close (less than 40 pixels), trigger click
                if distance < 40:
                    data["gesture"] = "CLICK"
                
                # 4. DETECT SWIPE
                self._detect_swipe(smooth_x, data)
                
        return data

    def _detect_swipe(self, current_x, data):
        """
        Analyzes movement history to detect swipes.
        """
        # Cooldown prevents multiple swipes registering instantly
        if self.swipe_cooldown > 0:
            self.swipe_cooldown -= 1
            return

        self.hand_positions.append(current_x)
        if len(self.hand_positions) > 10: # Keep last 10 frames
            self.hand_positions.pop(0)
            
        if len(self.hand_positions) == 10:
            # Calculate displacement: End - Start
            displacement = self.hand_positions[-1] - self.hand_positions[0]
            
            # Threshold: If moved 20% of screen width in 10 frames
            if displacement > 0.20: 
                data["gesture"] = "SWIPE_LEFT" # Camera is mirrored usually
                self.swipe_cooldown = 15 # Wait 15 frames before next swipe
                self.hand_positions = []
            elif displacement < -0.20:
                data["gesture"] = "SWIPE_RIGHT"
                self.swipe_cooldown = 15
                self.hand_positions = []

    def draw_debug_ui(self, frame, data):
        """
        Helper to visualize what the engine sees.
        """
        h, w, _ = frame.shape
        
        if data["cursor_detected"]:
            # Draw Index Finger (Cursor)
            cx, cy = int(data["x"] * w), int(data["y"] * h)
            cv2.circle(frame, (cx, cy), 15, (0, 255, 0), cv2.FILLED)
            
            # Draw Swipe Status
            if data["gesture"]:
                cv2.putText(frame, f"GESTURE: {data['gesture']}", (50, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                
            # Draw Skeleton
            self.mp_draw.draw_landmarks(frame, data["landmarks"], self.mp_hands.HAND_CONNECTIONS)
            
        return frame