import cv2
import time
import random
import numpy as np

class ArcadeComponent:
    def __init__(self):
        self.active = False
        self.reset()
        
    def reset(self):
        self.active = True
        self.score = 0
        self.target_pos = [0.5, 0.5] # x, y normalizat
        self.target_radius = 0.08
        self.hover_start = 0
        self.spawn_time = time.time()
        self.game_over = False

    def update(self, cx, cy):
        if not self.active: return
        
        if self.score >= 5: # Jocul se termină la 5 puncte
            self.game_over = True
            if time.time() - self.spawn_time > 3.0: # 3 secunde pauză la final
                self.active = False
            return

        # Calcul distanță
        tx, ty = self.target_pos
        # Aproximare distanță (fără aspect ratio corectat perfect pentru simplitate)
        dist = np.sqrt((cx - tx)**2 + (cy - ty)**2)
        
        if dist < self.target_radius:
            if self.hover_start == 0:
                self.hover_start = time.time()
            
            # Trebuie să ții cursorul 0.3 secunde pe țintă
            if time.time() - self.hover_start > 0.3:
                self.score += 1
                self.target_pos = [random.uniform(0.1, 0.9), random.uniform(0.2, 0.8)]
                self.hover_start = 0
                self.spawn_time = time.time() # Reset timer pt efecte
        else:
            self.hover_start = 0

    def draw(self, frame):
        h, w, _ = frame.shape
        
        if self.game_over:
            cv2.putText(frame, "BRAVO! AI CASTIGAT!", (w//2 - 250, h//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)
            return frame

        # UI
        cv2.putText(frame, f"Tinte prinse: {self.score}/5", (50, 80), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Desenează Ținta
        tx, ty = int(self.target_pos[0] * w), int(self.target_pos[1] * h)
        rad = int(self.target_radius * w)
        
        color = (0, 0, 255) # Roșu
        if self.hover_start > 0:
            color = (0, 255, 0) # Verde când ești deasupra
            
        cv2.circle(frame, (tx, ty), rad, color, -1)
        cv2.circle(frame, (tx, ty), rad+5, (255, 255, 255), 2)
        
        return frame