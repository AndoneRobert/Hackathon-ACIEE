import cv2
import time
import numpy as np
import os
import math

class MazeGame:
    def __init__(self):
        self.active = False
        
        # --- CONFIGURARE NIVEL ---
        self.level_layout = [
            "####################",
            "#S                 #",
            "#        ###########",
            "#        #         #",
            "#           #####  #",
            "#           #   #  #",
            "#               #  #",
            "#               #  #",
            "#                  #",
            "#                 E#",
            "####################"
        ]
        
        self.walls = []
        self.start_rect = None
        self.end_rect = None
        self.grid_h = len(self.level_layout)
        self.grid_w = len(self.level_layout[0])
        self.last_dims = (0, 0)

        # --- JUMPSCARE CONFIG ---
        self.TRANSIT_DURATION = 0.2 # Animation time in seconds

        # --- ÎNCĂRCARE ASSET JUMPSCARE ---
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
        jumpscare_path = os.path.join(project_root, "assets", "images", "job_application.png")
        
        self.jumpscare_img = cv2.imread(jumpscare_path)
        if self.jumpscare_img is None:
             self.jumpscare_img = np.zeros((500, 500, 3), dtype=np.uint8)
             self.jumpscare_img[:] = (0, 0, 255)

        self.reset()

    def _parse_level(self, width, height):
        self.walls = []
        cell_w = width / self.grid_w
        cell_h = height / self.grid_h
        
        for r, row in enumerate(self.level_layout):
            for c, char in enumerate(row):
                x = int(c * cell_w)
                y = int(r * cell_h)
                w = int(cell_w) + 1
                h = int(cell_h) + 1
                
                if char == '#':
                    self.walls.append((x, y, w, h))
                elif char == 'S':
                    self.start_rect = (x, y, w, h)
                elif char == 'E':
                    self.end_rect = (x, y, w, h)

    def reset(self):
        self.active = True
        self.state = "WAITING" 
        self.message = "Vino in zona VERDE pentru start!"
        self.msg_color = (255, 255, 255)
        self.end_time = 0
        self.jumpscare_start_time = 0
        self.cursor_norm = (0.5, 0.5) 

    def update(self, cx_norm, cy_norm):
        if not self.active: return
        self.cursor_norm = (cx_norm, cy_norm)
        current_time = time.time()
        
        # LOGICĂ TIMER JUMPSCARE
        if self.state == "JUMPSCARE":
            total_jumpscare_time = self.TRANSIT_DURATION + 2.0 
            if current_time - self.jumpscare_start_time > total_jumpscare_time:
                self.state = "LOST"
                self.end_time = current_time 
            return

        # LOGICĂ ECRANE FINALE
        if self.state in ["WON", "LOST"]:
            if current_time - self.end_time > 2.5: 
                self.active = False
            return

    def _check_logic(self, w, h):
        cx = int(self.cursor_norm[0] * w)
        cy = int(self.cursor_norm[1] * h)
        
        if self.state == "WAITING":
            if self.start_rect:
                sx, sy, sw, sh = self.start_rect
                if sx < cx < sx + sw and sy < cy < sy + sh:
                    self.state = "PLAYING"
                    self.message = "Ajungi la final (E)... daca poti."
                    self.msg_color = (0, 255, 255)

        elif self.state == "PLAYING":
            # 1. VERIFICĂM FINALUL -> CAPCANA (JUMPSCARE)
            if self.end_rect:
                ex, ey, ew, eh = self.end_rect
                if ex < cx < ex + ew and ey < cy < ey + eh:
                    self.state = "JUMPSCARE"
                    self.jumpscare_start_time = time.time()
                    self.message = "AI REUSIT (NU!)"
                    self.msg_color = (0, 0, 255)
                    return

            # 2. VERIFICĂM PEREȚII -> PIERZI NORMAL
            for (wx, wy, ww, wh) in self.walls:
                if wx < cx < wx + ww and wy < cy < wy + wh:
                    self.state = "LOST"
                    self.message = "AI ATINS PERETELE! Incearca din nou."
                    self.msg_color = (0, 0, 255)
                    self.end_time = time.time()
                    return

    def draw(self, frame):
        h, w, _ = frame.shape
        
        # --- DESENARE JUMPSCARE CU TRANZITIE ---
        if self.state == "JUMPSCARE" and self.jumpscare_img is not None:
            
            # --- MODIFICARE: FUNDAL COMPLET NEGRU ---
            frame[:] = 0 
            
            current_time = time.time()
            elapsed = current_time - self.jumpscare_start_time
            
            progress = min(elapsed / self.TRANSIT_DURATION, 1.0)
            
            # Cubica (progress^3) pentru un efect de accelerare la final.
            scale_progress = progress**3 
            
            # Scara: de la 10% la 100% din ecran
            current_scale = 0.1 + scale_progress * 0.9 
            
            target_w = int(w * current_scale)
            target_h = int(h * current_scale)
            
            # Redimensionare
            if target_w > 0 and target_h > 0:
                jumpscare_resized = cv2.resize(self.jumpscare_img, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
            else:
                jumpscare_resized = self.jumpscare_img

            # Calcul poziție (centrat)
            x_offset = (w - target_w) // 2
            y_offset = (h - target_h) // 2
            
            # Suprapune imaginea pe cadrul negru
            frame[y_offset:y_offset+target_h, x_offset:x_offset+target_w] = jumpscare_resized
            
            return frame
        
        # LOGICA NORMALĂ
        if (w, h) != self.last_dims:
            self._parse_level(w, h)
            self.last_dims = (w, h)

        if self.active:
            self._check_logic(w, h)
        
        # 1. Fundal
        cv2.rectangle(frame, (0,0), (w,h), (20, 20, 30), -1)
        
        # 2. Pereți
        for (wx, wy, ww, wh) in self.walls:
            cv2.rectangle(frame, (wx, wy), (wx+ww, wy+wh), (100, 100, 120), -1)
            cv2.rectangle(frame, (wx, wy), (wx+ww, wy+wh), (150, 150, 170), 1)
            
        # 3. Start (Verde)
        if self.start_rect:
            sx, sy, sw, sh = self.start_rect
            cv2.rectangle(frame, (sx, sy), (sx+sw, sy+sh), (0, 200, 0), -1)
            cv2.putText(frame, "S", (sx + sw//2 - 10, sy + sh//2 + 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # 4. Final (Roșu - Capcana)
        if self.end_rect:
            ex, ey, ew, eh = self.end_rect
            color_end = (0, 0, 255) if int(time.time()*6)%2==0 else (50, 0, 180)
            cv2.rectangle(frame, (ex, ey), (ex+ew, ey+eh), color_end, -1)
            cv2.putText(frame, "E", (ex + ew//2 - 10, ey + eh//2 + 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # 5. Mesaje
        cv2.rectangle(frame, (0, h-60), (w, h), (0,0,0), -1)
        cv2.putText(frame, self.message, (50, h - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, self.msg_color, 2)

        return frame