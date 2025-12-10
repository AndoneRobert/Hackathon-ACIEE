import cv2
import mediapipe as mp
import time
import numpy as np
import random
import os

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
        
        # Load Particle Image (ACIEE Logo)
        self.particle_img = None
        # Check standard extensions
        possible_names = ["aciee_logo.jpeg", "aciee_logo.png", "aciee_logo.jpg"]
        base_path = "assets/images"
        
        for name in possible_names:
            full_path = os.path.join(base_path, name)
            if os.path.exists(full_path):
                try:
                    loaded_img = cv2.imread(full_path, cv2.IMREAD_UNCHANGED)
                    if loaded_img is not None:
                        # Resize to a small particle size (e.g., 30x30 pixels)
                        self.particle_img = cv2.resize(loaded_img, (30, 30))
                        print(f"Screensaver: Loaded particle image from {full_path}")
                        break
                except Exception as e:
                    print(f"Screensaver: Error loading {name}: {e}")
        
        if self.particle_img is None:
            print("Screensaver: No 'aciee_logo' found in assets. Using default circles.")

        # Animation State
        # Format: [x, y, speed, color]
        self.particles = []
        for _ in range(65): 
            self.particles.append([
                random.random(),             # x: 0.0 - 1.0
                random.random(),             # y: 0.0 - 1.0
                random.uniform(0.003, 0.01), # speed: ~0.3% to 1% of screen height
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
        
        # Update Particle Animation (Normalized Math)
        for p in self.particles:
            p[1] += p[2]  # y += speed
            # If particle goes off the bottom (>1.0), reset to top
            if p[1] > 1.05:
                p[1] = -0.05
                p[0] = random.random()

        self.logo_pulse += 0.1
        return None

    def _overlay_image(self, bg, overlay, x, y):
        """Helper to draw an overlay with transparency checks."""
        bg_h, bg_w = bg.shape[:2]
        ov_h, ov_w = overlay.shape[:2]

        # Calculate limits to prevent out-of-bounds errors
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(bg_w, x + ov_w), min(bg_h, y + ov_h)

        if x1 >= x2 or y1 >= y2: return

        ov_x1 = x1 - x
        ov_y1 = y1 - y
        ov_x2 = ov_x1 + (x2 - x1)
        ov_y2 = ov_y1 + (y2 - y1)

        bg_crop = bg[y1:y2, x1:x2]
        ov_crop = overlay[ov_y1:ov_y2, ov_x1:ov_x2]

        if overlay.shape[2] == 4:
            alpha = ov_crop[:, :, 3] / 255.0
            alpha_inv = 1.0 - alpha
            
            for c in range(3):
                bg_crop[:, :, c] = (alpha * ov_crop[:, :, c] + 
                                    alpha_inv * bg_crop[:, :, c])
        else:
            bg[y1:y2, x1:x2] = ov_crop

    def _draw_rounded_rect(self, img, pt1, pt2, color, thickness, r):
        """Helper to draw a rectangle with rounded corners."""
        x1, y1 = pt1
        x2, y2 = pt2
        
        # Ensure radius isn't too large for the box
        w_rect = x2 - x1
        h_rect = y2 - y1
        r = min(r, w_rect // 2, h_rect // 2)

        if thickness == -1:
            # FILLED ROUNDED RECT
            # Draw two inner rectangles
            cv2.rectangle(img, (x1 + r, y1), (x2 - r, y2), color, -1)
            cv2.rectangle(img, (x1, y1 + r), (x2, y2 - r), color, -1)
            # Draw four corner circles
            cv2.circle(img, (x1 + r, y1 + r), r, color, -1)
            cv2.circle(img, (x2 - r, y1 + r), r, color, -1)
            cv2.circle(img, (x1 + r, y2 - r), r, color, -1)
            cv2.circle(img, (x2 - r, y2 - r), r, color, -1)
        else:
            # OUTLINE ROUNDED RECT
            # Draw straight lines
            cv2.line(img, (x1 + r, y1), (x2 - r, y1), color, thickness)
            cv2.line(img, (x1 + r, y2), (x2 - r, y2), color, thickness)
            cv2.line(img, (x1, y1 + r), (x1, y2 - r), color, thickness)
            cv2.line(img, (x2, y1 + r), (x2, y2 - r), color, thickness)
            # Draw arcs
            cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, thickness)
            cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, thickness)
            cv2.ellipse(img, (x1 + r, y2 - r), (r, r), 90, 0, 90, color, thickness)
            cv2.ellipse(img, (x2 - r, y2 - r), (r, r), 0, 0, 90, color, thickness)

    def draw(self, frame, logo_img=None):
        h, w, _ = frame.shape
        
        # 1. Background Dimming
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (20, 10, 40), -1) 
        cv2.addWeighted(overlay, 0.95, frame, 0.05, 0, frame)
        
        # 2. Draw Matrix Particles
        for p in self.particles:
            nx, ny, speed, color = p
            draw_x = int(nx * w)
            draw_y = int(ny * h)
            
            if self.particle_img is not None:
                self._overlay_image(frame, self.particle_img, draw_x, draw_y)
            else:
                cv2.circle(frame, (draw_x, draw_y), 2, color, -1)
                cv2.line(frame, (draw_x, draw_y), (draw_x, draw_y-10), color, 1)

        # 3. Draw Glass Card & Text
        pulse = abs(np.sin(self.logo_pulse))
        center_y = h // 2
        
        # --- NEW SIZE LOGIC: Centered box instead of full width ---
        box_width = 800
        box_height = 180
        half_w = box_width // 2
        half_h = box_height // 2

        box_x1, box_y1 = (w // 2) - half_w, center_y - half_h
        box_x2, box_y2 = (w // 2) + half_w, center_y + half_h
        
        # Corner radius for rounded edges
        radius = 20

        # Glass Effect (Rounded)
        glass_overlay = frame.copy()
        # Use new helper for filled rect (-1 thickness)
        self._draw_rounded_rect(glass_overlay, (box_x1, box_y1), (box_x2, box_y2), (10, 10, 10), -1, radius)
        cv2.addWeighted(glass_overlay, 0.6, frame, 0.4, 0, frame)

        # Glowing Border (Rounded)
        glow_color = (255, 150 + int(50 * pulse), 0)
        # Use new helper for outline (2 thickness)
        self._draw_rounded_rect(frame, (box_x1, box_y1), (box_x2, box_y2), glow_color, 2, radius)
        
        # Offset/Shadow Border (Rounded)
        offset = 6
        self._draw_rounded_rect(frame, 
                                (box_x1 - offset, box_y1 - offset), 
                                (box_x2 + offset, box_y2 + offset), 
                                (200, 200, 200), 1, radius + 2)

        # Text with Shadow
        font = cv2.FONT_HERSHEY_SIMPLEX
        # Adjusted x-coordinates slightly to center within the 800px box
        cv2.putText(frame, "Facultatea de Automatica, Calculatoare,", (w//2 - 300, center_y - 20), font, 1, (255, 255, 255), 2)
        cv2.putText(frame, "Inginerie Electrica si Electronica", (w//2 - 260, center_y + 30), font, 1, (255, 255, 255), 2)

        # Blink Text
        if int(time.time() * 2) % 2 == 0: 
            cv2.putText(frame, "[ VINO IN FATA CAMEREI PENTRU A INCEPE ]", (w//2 - 400, h - 180), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 204, 0), 2)

        # 4. Draw Logo (Main University Logo)
        if logo_img is not None:
            try:
                ly, lx = logo_img.shape[:2]
                x_pos = (w // 2) - (lx // 2)
                y_pos = 50 
                if y_pos + ly <= h and x_pos + lx <= w:
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

        # 5. Waking Progress
        waking_progress = 0 if self.face_detected_time == 0 else (time.time() - self.face_detected_time) / self.WAKE_THRESHOLD
        if waking_progress > 0:
            bw = int(w * waking_progress)
            cv2.rectangle(frame, (0, h-10), (w, h), (50, 50, 50), -1)
            cv2.rectangle(frame, (0, h-10), (bw, h), (255, 200, 0), -1)
            cv2.putText(frame, "INITIALIZARE SISTEM", (20, h - 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2)
                       
        return frame