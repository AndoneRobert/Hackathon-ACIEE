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

    def draw(self, frame, logo_img=None):
        """
        Draw the full screensaver UI onto `frame` and return it.
        This mirrors the previous `draw_screensaver_ui` behavior used by the app.
        """
        h, w, _ = frame.shape

        # Background overlay (darken)
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (20, 10, 40), -1)
        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

        # Draw particles (matrix style)
        for p in self.particles:
            x, y, speed, color = p
            draw_x = int(x * (w / 640)) if w > 640 else int(x)
            draw_y = int(y * (h / 480)) if h > 480 else int(y)
            cv2.circle(frame, (draw_x, draw_y), 2, color, -1)
            cv2.line(frame, (draw_x, draw_y), (draw_x, draw_y - 10), color, 1)

        # Draw logo if provided
        if logo_img is not None:
            try:
                ly, lx = logo_img.shape[:2]
                x_pos = (w // 2) - (lx // 2)
                y_pos = 50
                roi = frame[y_pos:y_pos+ly, x_pos:x_pos+lx]
                if logo_img.shape[2] == 4:
                    b, g, r, a = cv2.split(logo_img)
                    overlay_color = cv2.merge((b, g, r))
                    mask = cv2.merge((a, a, a))
                    img1_bg = cv2.bitwise_and(roi.copy(), cv2.bitwise_not(mask))
                    img2_fg = cv2.bitwise_and(overlay_color, mask)
                    frame[y_pos:y_pos+ly, x_pos:x_pos+lx] = cv2.add(img1_bg, img2_fg)
                else:
                    frame[y_pos:y_pos+ly, x_pos:x_pos+lx] = logo_img
            except Exception:
                pass

        # Pulse and text
        pulse = abs(np.sin(self.logo_pulse))
        glow_intensity = int(20 * pulse)
        center_y = h // 2

        cv2.rectangle(frame, (100 - glow_intensity, center_y - 80 - glow_intensity),
                             (w - 100 + glow_intensity, center_y + 80 + glow_intensity),
                             (255, 100, 0), 1)
        cv2.rectangle(frame, (100, center_y - 80), (w - 100, center_y + 80), (0, 0, 0), -1)

        cv2.putText(frame, "FACULTY OF AUTOMATION,", (w//2 - 250, center_y - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, "COMPUTERS & ELECTRONICS", (w//2 - 260, center_y + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)

        if int(time.time() * 2) % 2 == 0:
            cv2.putText(frame, "[ STEP FORWARD TO START ]", (w//2 - 180, h - 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # Waking progress bar
        ui = self.get_ui_data()
        if ui.get("waking_progress", 0) > 0:
            bw = int(w * ui.get("waking_progress", 0))
            cv2.rectangle(frame, (0, h-10), (w, h), (50, 50, 50), -1)
            cv2.rectangle(frame, (0, h-10), (bw, h), (255, 200, 0), -1)
            cv2.putText(frame, "INITIALIZING SYSTEM...", (20, h - 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2)

        return frame