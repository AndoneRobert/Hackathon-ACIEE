import cv2
import mediapipe as mp
import time
import numpy as np
import random

class Screensaver:
    def __init__(self):
        # Face Detection Setup
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            min_detection_confidence=0.5
        )
        
        # State
        self.face_detected_time = 0
        self.WAKE_THRESHOLD = 0.8
        
        # Animation State
        self.particles = []
        for _ in range(50): 
            self.particles.append([
                random.randint(0, 640), 
                random.randint(0, 480), 
                random.randint(2, 5),   
                random.choice([(0, 255, 255), (255, 100, 0)]) 
            ])
            
        self.logo_pulse = 0.0
        # Animation frame counter for UI animations
        self.anim_frame = 0

    def is_face_present(self, frame):
        """
        Helper function to check if a face is looking at the camera.
        Returns True if a face is found, False otherwise.
        """
        h, w, c = frame.shape
        # Convert to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(frame_rgb)
        
        if results.detections:
            for detection in results.detections:
                bboxC = detection.location_data.relative_bounding_box
                face_height = int(bboxC.height * h)
                # Check if face is close enough (10% of screen height)
                if face_height > h * 0.10: 
                    return True
        return False

    def update(self, frame):
        # Use our internal helper
        face_found = self.is_face_present(frame)
        
        # Wake Up Logic
        if face_found:
            if self.face_detected_time == 0:
                self.face_detected_time = time.time()
            
            elapsed = time.time() - self.face_detected_time
            if elapsed > self.WAKE_THRESHOLD:
                self.face_detected_time = 0
                return "WAKE_UP"
        else:
            self.face_detected_time = 0
        
        # Update Particle Animation
        h, w, _ = frame.shape
        for p in self.particles:
            p[1] += p[2] 
            if p[1] > h:
                p[1] = 0
                p[0] = random.randint(0, w)

        self.logo_pulse += 0.1
        # advance animation frame counter
        self.anim_frame += 1
        return None

    def get_ui_data(self):
        # compute waking progress, clamped 0..1
        raw_progress = 0 if self.face_detected_time == 0 else (time.time() - self.face_detected_time) / self.WAKE_THRESHOLD
        waking_progress = max(0.0, min(1.0, raw_progress))
        return {
            "waking_progress": waking_progress,
            "particles": self.particles,
            "pulse": abs(np.sin(self.logo_pulse)),
            "anim_frame": self.anim_frame,
        }