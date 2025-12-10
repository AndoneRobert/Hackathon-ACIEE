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

    def is_face_present(self, frame):
        h, w, c = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(frame_rgb)
        
        if results.detections:
            for detection in results.detections:
                bboxC = detection.location_data.relative_bounding_box
                face_height = int(bboxC.height * h)
                if face_height > h * 0.10: 
                    return True
        return False

    def update(self, frame):
        face_found = self.is_face_present(frame)
        
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
        return None

    # --- MOVED DRAWING LOGIC HERE ---
    def draw(self, frame, logo_img=None):
        h, w, _ = frame.shape
        
        # 1. Background Dimming
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (20, 10, 40), -1) 
        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)
        
        # 2. Draw Matrix Particles (Using self.particles)
        for p in self.particles:
            x, y, speed, color = p
            draw_x = int(x * (w / 640)) if w > 640 else x
            draw_y = int(y * (h / 480)) if h > 480 else y
            cv2.circle(frame, (draw_x, draw_y), 2, color, -1)
            cv2.line(frame, (draw_x, draw_y), (draw_x, draw_y-10), color, 1)

        # 3. Draw Logo
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
            except Exception as e:
                print(f"Error drawing logo: {e}")

        # 4. Draw Glass Card & Text
        pulse = abs(np.sin(self.logo_pulse)) # Calculated internally now
        center_y = h // 2
        
        box_x1, box_y1 = 100, center_y - 90
        box_x2, box_y2 = w - 100, center_y + 90
        
        # Glass Effect
        glass_overlay = frame.copy()
        cv2.rectangle(glass_overlay, (box_x1, box_y1), (box_x2, box_y2), (10, 10, 10), -1)
        cv2.addWeighted(glass_overlay, 0.6, frame, 0.4, 0, frame)

        # Glowing Border
        glow_color = (255, 150 + int(50 * pulse), 0)
        cv2.rectangle(frame, (box_x1, box_y1), (box_x2, box_y2), glow_color, 2)
        offset = 6
        cv2.rectangle(frame, (box_x1 - offset, box_y1 - offset), 
                             (box_x2 + offset, box_y2 + offset), 
                             (200, 200, 200), 1)

        # Text with Shadow
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, "Facultatea de Automatica, Calculatoare,", (w//2 - 300 + 2, center_y - 20 + 2), font, 1, (0,0,0), 4)
        cv2.putText(frame, "Facultatea de Automatica, Calculatoare,", (w//2 - 300, center_y - 20), font, 1, (255, 255, 255), 2)
        
        cv2.putText(frame, "Inginerie Electrica si Electronica", (w//2 - 260 + 2, center_y + 30 + 2), font, 1, (0,0,0), 4)
        cv2.putText(frame, "Inginerie Electrica si Electronica", (w//2 - 260, center_y + 30), font, 1, (138, 80, 22), 3)

        # Blink Text
        if int(time.time() * 2) % 2 == 0: 
            cv2.putText(frame, "[ VINO IN FATA CAMEREI PENTRU A INCEPE ]", (w//2 - 400, h - 180), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.1, (138, 80, 22), 2)

        # 5. Waking Progress
        waking_progress = 0 if self.face_detected_time == 0 else (time.time() - self.face_detected_time) / self.WAKE_THRESHOLD
        
        if waking_progress > 0:
            bw = int(w * waking_progress)
            cv2.rectangle(frame, (0, h-10), (w, h), (50, 50, 50), -1)
            cv2.rectangle(frame, (0, h-10), (bw, h), (255, 200, 0), -1)
            cv2.putText(frame, "INITIALIZARE SISTEM", (20, h - 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2)
                       
        return frame