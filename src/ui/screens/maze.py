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
        self.TRANSIT_DURATION = 0.2 
        
        # Incarcare asset Jumpscare
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
        jumpscare_path = os.path.join(project_root, "assets", "images", "job_application.png")
        
        self.jumpscare_img = cv2.imread(jumpscare_path)
        if self.jumpscare_img is None:
             self.jumpscare_img = np.zeros((500, 500, 3), dtype=np.uint8)
             self.jumpscare_img[:] = (0, 0, 255)

        # --- VARIABILE ANIMATIE ---
        self.pulse_phase = 0.0

        self.reset()

    def _parse_level(self, width, height):
        self.walls = []
        # Calculam dimensiunile celulelor
        cell_w = width / self.grid_w
        cell_h = height / self.grid_h
        
        for r, row in enumerate(self.level_layout):
            for c, char in enumerate(row):
                x = int(c * cell_w)
                y = int(r * cell_h)
                w = int(cell_w) + 1 # +1 pentru a evita spatiile goale intre blocuri
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
        self.message = "Mergi la START pentru a incepe!"
        self.msg_color = (0, 255, 0) # Verde
        self.end_time = 0
        self.jumpscare_start_time = 0
        self.cursor_norm = (0.5, 0.5) 

    def update(self, cx_norm, cy_norm):
        if not self.active: return
        self.cursor_norm = (cx_norm, cy_norm)
        current_time = time.time()
        
        # Animatie pulsatie
        self.pulse_phase += 0.15
        
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
                # Verificam daca cursorul e in zona de start
                if sx < cx < sx + sw and sy < cy < sy + sh:
                    self.state = "PLAYING"
                    self.message = "Evita peretii! Ajungi la FINAL."
                    self.msg_color = (0, 255, 255)

        elif self.state == "PLAYING":
            # 1. VERIFICĂM FINALUL -> CAPCANA (JUMPSCARE)
            if self.end_rect:
                ex, ey, ew, eh = self.end_rect
                if ex < cx < ex + ew and ey < cy < ey + eh:
                    self.state = "JUMPSCARE"
                    self.jumpscare_start_time = time.time()
                    self.message = "AI REUSIT...?"
                    self.msg_color = (0, 0, 255)
                    return

            # 2. VERIFICĂM PEREȚII -> PIERZI NORMAL
            # Optimizare: Verificam doar peretii din apropierea cursorului ar fi ideal,
            # dar la numarul mic de pereti, iteratia completa e ok.
            for (wx, wy, ww, wh) in self.walls:
                if wx < cx < wx + ww and wy < cy < wy + wh:
                    self.state = "LOST"
                    self.message = "SYSTEM FAILURE: Ai atins peretele!"
                    self.msg_color = (0, 0, 255)
                    self.end_time = time.time()
                    return

    def _draw_tech_grid(self, frame, w, h):
        """Deseneaza un grid subtil pe fundal."""
        step = 50
        color = (30, 30, 40) # Gri foarte inchis
        
        # Linii verticale
        for x in range(0, w, step):
            cv2.line(frame, (x, 0), (x, h), color, 1)
        
        # Linii orizontale
        for y in range(0, h, step):
            cv2.line(frame, (0, y), (w, y), color, 1)

    def _draw_neon_rect(self, frame, x, y, w, h, color_bgr, fill_alpha=0.3):
        """Deseneaza un dreptunghi cu efect de neon (margine stralucitoare + interior transparent)."""
        
        # 1. Interior Transparent
        overlay = frame.copy()
        cv2.rectangle(overlay, (x, y), (x + w, y + h), color_bgr, -1)
        cv2.addWeighted(overlay, fill_alpha, frame, 1 - fill_alpha, 0, frame)
        
        # 2. Margine Stralucitoare (Grosime 2)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color_bgr, 2)
        
        # 3. Colturi Accentuate (Tech Look)
        corner_len = min(10, w//3, h//3)
        bright_color = tuple(min(255, c + 100) for c in color_bgr) # Culoare mai deschisa
        
        # Colt Stanga-Sus
        cv2.line(frame, (x, y), (x + corner_len, y), bright_color, 2)
        cv2.line(frame, (x, y), (x, y + corner_len), bright_color, 2)
        
        # Colt Dreapta-Jos
        cv2.line(frame, (x + w, y + h), (x + w - corner_len, y + h), bright_color, 2)
        cv2.line(frame, (x + w, y + h), (x + w, y + h - corner_len), bright_color, 2)

    def draw(self, frame):
        h, w, _ = frame.shape
        
        # --- DESENARE JUMPSCARE (Prioritar) ---
        if self.state == "JUMPSCARE" and self.jumpscare_img is not None:
            frame[:] = 0 # Blackout
            
            current_time = time.time()
            elapsed = current_time - self.jumpscare_start_time
            progress = min(elapsed / self.TRANSIT_DURATION, 1.0)
            
            # Zoom In Effect
            scale_progress = progress**3 
            current_scale = 0.1 + scale_progress * 0.9 
            
            target_w = int(w * current_scale)
            target_h = int(h * current_scale)
            
            if target_w > 0 and target_h > 0:
                jumpscare_resized = cv2.resize(self.jumpscare_img, (target_w, target_h))
                x_offset = (w - target_w) // 2
                y_offset = (h - target_h) // 2
                
                # Bounds check
                y1, y2 = max(0, y_offset), min(h, y_offset + target_h)
                x1, x2 = max(0, x_offset), min(w, x_offset + target_w)
                
                # Ajustam crop-ul daca iese din ecran (safe resize logic)
                if x2 > x1 and y2 > y1:
                    # Trebuie sa decupam si din imaginea sursa daca iese din ecran
                    src_y1 = 0
                    src_y2 = target_h
                    if y_offset < 0: src_y1 = -y_offset
                    if y_offset + target_h > h: src_y2 = target_h - (y_offset + target_h - h)
                    
                    src_x1 = 0
                    src_x2 = target_w
                    if x_offset < 0: src_x1 = -x_offset
                    if x_offset + target_w > w: src_x2 = target_w - (x_offset + target_w - w)

                    try:
                        frame[y1:y2, x1:x2] = jumpscare_resized[src_y1:src_y2, src_x1:src_x2]
                    except:
                        pass # Safety fallback
            return frame
        
        # --- LOGICA STANDARD ---
        if (w, h) != self.last_dims:
            self._parse_level(w, h)
            self.last_dims = (w, h)

        if self.active:
            self._check_logic(w, h)
        
        # 1. Fundal Dark Tech
        cv2.rectangle(frame, (0,0), (w,h), (15, 15, 20), -1) # Dark Navy/Black
        self._draw_tech_grid(frame, w, h)
        
        # 2. Pereți (Cyan Neon Style)
        wall_color = (255, 200, 0) # Cyan in BGR
        for (wx, wy, ww, wh) in self.walls:
            self._draw_neon_rect(frame, wx, wy, ww, wh, wall_color, fill_alpha=0.2)
            
        # 3. Start (Verde Pulsant)
        if self.start_rect:
            sx, sy, sw, sh = self.start_rect
            # Pulsatie pe canalul verde
            pulse = (math.sin(self.pulse_phase) + 1) / 2 # 0.0 -> 1.0
            green_val = int(150 + 105 * pulse)
            
            self._draw_neon_rect(frame, sx, sy, sw, sh, (0, green_val, 0), fill_alpha=0.4)
            
            # Text centrat
            text = "START"
            font = cv2.FONT_HERSHEY_SIMPLEX
            ts = cv2.getTextSize(text, font, 0.6, 2)[0]
            cv2.putText(frame, text, (sx + (sw-ts[0])//2, sy + (sh+ts[1])//2), 
                       font, 0.6, (255, 255, 255), 2)
        
        # 4. Final (Roșu/Mov Alertă)
        if self.end_rect:
            ex, ey, ew, eh = self.end_rect
            # Clipire alerta
            is_alert = int(time.time() * 5) % 2 == 0
            end_color = (0, 0, 255) if is_alert else (50, 0, 150) # Rosu <-> Mov Inchis
            
            self._draw_neon_rect(frame, ex, ey, ew, eh, end_color, fill_alpha=0.5)
            
            text = "EXIT"
            ts = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.putText(frame, text, (ex + (ew-ts[0])//2, ey + (eh+ts[1])//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # 5. Mesaje HUD (Stil Terminal)
        # Bara neagra jos
        cv2.rectangle(frame, (0, h-50), (w, h), (0,0,0), -1)
        cv2.line(frame, (0, h-50), (w, h-50), (0, 255, 255), 1) # Linie galbena sus
        
        # Text mesaj
        cv2.putText(frame, f">> {self.message}", (30, h - 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.msg_color, 2, cv2.LINE_AA)

        return frame