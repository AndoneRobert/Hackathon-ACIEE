import cv2
import time
import numpy as np
import os
import math
import random

# --- IMPORTURILE JOCURILOR ---
from src.ui.screens.quiz_game import QuizGame as QuizLogic
from src.ui.screens.arcade import ArcadeComponent
from src.ui.screens.maze import MazeGame

class QuizGame: # Clasa Hub pentru Jocuri
    def __init__(self):
        self.mode = "MENU"     
        
        # Initializam instantele jocurilor
        self.quiz = QuizLogic()
        self.arcade = ArcadeComponent()
        self.maze = MazeGame()
        
        # --- CONFIGURARE CULORI (PALETA PIXEL BUBBLE) ---
        # Format BGR (Blue, Green, Red)
        self.PALETTE = {
            "CYAN":   (235, 206, 135),  # Cyan-ul deschis
            "PINK":   (203, 192, 255),  # Rozul
            "BG_DARK": (40, 20, 45),    # Fundal inchis (dark purple)
            "TEXT":   (255, 255, 255)   # Alb
        }

        # --- INCARCARE ASSET (Pixel Bubble) ---
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
        sprite_path = os.path.join(project_root, "assets", "images", "pixel_bubble.png")
        
        self.bubble_sprite = cv2.imread(sprite_path, cv2.IMREAD_UNCHANGED)
        if self.bubble_sprite is None:
            print(f"WARN: Nu s-a gasit imaginea la {sprite_path}")
            self.bubble_sprite = np.zeros((100, 100, 4), dtype=np.uint8)
            cv2.circle(self.bubble_sprite, (50,50), 45, (50, 50, 50, 255), -1)

        # --- CONFIGURARE BUTOANE JOCURI (BULE) ---
        self.buttons = {
            "QUIZ":   (0.25, 0.5, 0.12),
            "ARCADE": (0.50, 0.5, 0.12),
            "MAZE":   (0.75, 0.5, 0.12)
        }
        
        self.anim_offsets = {k: random.uniform(0, 6.28) for k in self.buttons.keys()}

        # --- CONFIGURARE BUTON INAPOI (FIX) ---
        self.back_btn_rect = {
            "BACK": (0.03, 0.05, 0.12, 0.07) # x, y, w, h (proportii ecran)
        }
        
        self.hovered = None
        self.hover_start = 0
        self.progress = 0.0
        self.SELECTION_TIME = 1.5

    def update(self, cx, cy):
        # 1. LOGICA SUB-JOCURILOR
        if self.mode == "QUIZ":
            result = self.quiz.update(cx, cy)
            if result == "EXIT_TO_APP":
                self.mode = "MENU" # Ne intoarcem la bule
                self.quiz.reset()
                return False # <--- MODIFICAT: Ramanem in Hub-ul de jocuri
            return False

        elif self.mode == "ARCADE":
            self.arcade.update(cx, cy)
            if not self.arcade.active:
                self.mode = "MENU" # Ne intoarcem la bule
                self.arcade.reset()
                return False # <--- MODIFICAT: Ramanem in Hub-ul de jocuri
            return False

        elif self.mode == "MAZE":
            self.maze.update(cx, cy)
            if not self.maze.active:
                self.mode = "MENU"
                self.maze.reset()
                return False # <--- MODIFICAT: Consistenta si pentru Maze
            return False

        # 2. LOGICA MENIU SELECTIE
        return self._update_menu(cx, cy)

    def _update_menu(self, cx, cy):
        current_hover = None
        aspect_ratio = 1.77
        
        # A. Verificam Butonul BACK
        bx, by, bw, bh = self.back_btn_rect["BACK"]
        if bx < cx < bx + bw and by < cy < by + bh:
            current_hover = "BACK"
        else:
            # B. Verificam Bulele de Joc
            for name, (bcx, bcy, br) in self.buttons.items():
                dx = cx - bcx
                dy = (cy - bcy) / aspect_ratio
                dist = math.sqrt(dx*dx + dy*dy)
                
                if dist < br:
                    current_hover = name
                    break
        
        # Logica Timer Selectie
        if current_hover:
            if self.hovered != current_hover:
                self.hovered = current_hover
                self.hover_start = time.time()
                self.progress = 0.0
            else:
                elapsed = time.time() - self.hover_start
                self.progress = min(elapsed / self.SELECTION_TIME, 1.0)
                
                if self.progress >= 1.0:
                    self.hovered = None
                    self.progress = 0.0
                    
                    if current_hover == "BACK":
                        return True
                    elif current_hover == "QUIZ":
                        self.quiz.reset()
                        self.mode = "QUIZ"
                    elif current_hover == "ARCADE":
                        self.arcade.reset()
                        self.mode = "ARCADE"
                    elif current_hover == "MAZE":
                        self.maze.reset()
                        self.mode = "MAZE"
        else:
            self.hovered = None
            self.progress = 0.0
            
        return False

    def overlay_transparent(self, background, overlay, x, y):
        bg_h, bg_w, _ = background.shape
        ov_h, ov_w, _ = overlay.shape

        if x >= bg_w or y >= bg_h or x + ov_w < 0 or y + ov_h < 0: 
            return background

        bg_x_start = max(0, x)
        bg_y_start = max(0, y)
        bg_x_end = min(x + ov_w, bg_w)
        bg_y_end = min(y + ov_h, bg_h)
        
        roi_w = bg_x_end - bg_x_start
        roi_h = bg_y_end - bg_y_start
        
        if roi_w <= 0 or roi_h <= 0: return background

        roi = background[bg_y_start:bg_y_end, bg_x_start:bg_x_end]
        
        ov_crop_x = bg_x_start - x
        ov_crop_y = bg_y_start - y
        overlay_crop = overlay[ov_crop_y:ov_crop_y+roi_h, ov_crop_x:ov_crop_x+roi_w]

        if overlay_crop.shape[2] == 4:
            alpha = overlay_crop[:, :, 3] / 255.0
            ov_bgr = overlay_crop[:, :, :3]
            for c in range(3):
                roi[:, :, c] = (alpha * ov_bgr[:, :, c] + (1.0 - alpha) * roi[:, :, c])
        else:
            roi[:] = overlay_crop

        background[bg_y_start:bg_y_end, bg_x_start:bg_x_end] = roi
        return background

    def draw(self, frame):
        if self.mode == "QUIZ":
            return self.quiz.draw(frame)
        elif self.mode == "ARCADE":
            return self.arcade.draw(frame)
        elif self.mode == "MAZE":
            return self.maze.draw(frame)
        
        # --- DESENARE MENIU ---
        h, w, _ = frame.shape
        current_time = time.time()
        
        # Titlu
        cv2.putText(frame, "ALEGE JOCUL", (w//2 - 150, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, self.PALETTE["TEXT"], 3)
        
        # ---------------------------------------------------------
        # 1. DESENARE BUTON INAPOI (Transparent Tech Style)
        # ---------------------------------------------------------
        bx, by, bw, bh = self.back_btn_rect["BACK"]
        x1, y1 = int(bx * w), int(by * h)
        x2, y2 = int((bx + bw) * w), int((by + bh) * h)
        
        is_back_hovered = (self.hovered == "BACK")
        
        # --- CULORI (SWAPPED) ---
        # IDLE = CYAN
        # HOVER = PINK
        corner_color = self.PALETTE["PINK"] if is_back_hovered else self.PALETTE["CYAN"]
        bg_color = self.PALETTE["BG_DARK"]
        
        # A. FUNDAL TRANSPARENT (STICLA FUMURIE)
        roi = frame[y1:y2, x1:x2]
        color_block = np.zeros_like(roi, dtype=np.uint8)
        color_block[:] = bg_color
        
        # Blend: 0.4 culoare (mai putin opac) + 0.6 imagine originala (mai vizibil prin el)
        cv2.addWeighted(color_block, 0.4, roi, 0.6, 0, roi)
        frame[y1:y2, x1:x2] = roi

        # B. BORDER "TECH" (Colturi Opuse)
        corner_len_w = int((x2 - x1) * 0.3)
        corner_len_h = int((y2 - y1) * 0.4)
        thickness = 3 if is_back_hovered else 2

        # Coltul STANGA-SUS
        cv2.line(frame, (x1, y1), (x1 + corner_len_w, y1), corner_color, thickness)
        cv2.line(frame, (x1, y1), (x1, y1 + corner_len_h), corner_color, thickness)
        
        # Coltul DREAPTA-JOS
        cv2.line(frame, (x2, y2), (x2 - corner_len_w, y2), corner_color, thickness)
        cv2.line(frame, (x2, y2), (x2, y2 - corner_len_h), corner_color, thickness)

        # C. BARA PROGRES (PINK la Hover)
        if is_back_hovered and self.progress > 0:
            prog_w = int((x2 - x1) * self.progress)
            cv2.rectangle(frame, (x1, y2 - 4), (x1 + prog_w, y2), self.PALETTE["PINK"], -1)

        # TEXT BUTON ("<< BACK")
        font_scale = 0.7
        text = "<< INAPOI"
        ts = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)[0]
        tx = x1 + (x2 - x1 - ts[0]) // 2
        ty = y1 + (y2 - y1 + ts[1]) // 2
        
        cv2.putText(frame, text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, self.PALETTE["TEXT"], 2)

        # ---------------------------------------------------------
        # 2. DESENARE BULE JOCURI
        # ---------------------------------------------------------
        for name, (cx_norm, cy_norm, r_norm) in self.buttons.items():
            is_hovered = (self.hovered == name)
            
            # Animatie Plutire
            float_y = 0
            scale = 1.0
            
            if is_hovered:
                scale = 1.1 + 0.05 * math.sin(current_time * 10)
            else:
                float_y = math.sin(current_time * 2.5 + self.anim_offsets[name]) * 10

            center_x = int(cx_norm * w)
            center_y = int(cy_norm * h + float_y)
            target_size = int(r_norm * w * 2 * scale)
            
            resized = cv2.resize(self.bubble_sprite, (target_size, target_size), interpolation=cv2.INTER_NEAREST)
            
            tl_x = center_x - target_size // 2
            tl_y = center_y - target_size // 2
            
            frame = self.overlay_transparent(frame, resized, tl_x, tl_y)
            
            if is_hovered and self.progress > 0:
                angle = 360 * self.progress
                radius = target_size // 2
                cv2.ellipse(frame, (center_x, center_y), (radius, radius), -90, 0, angle, self.PALETTE["CYAN"], 6)

            text_col = self.PALETTE["CYAN"] if is_hovered else self.PALETTE["TEXT"]
            font_s = 1.0 * scale
            ts = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, font_s, 2)[0]
            
            cv2.putText(frame, name, (center_x - ts[0]//2, center_y + ts[1]//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, font_s, (0,0,0), 4)
            cv2.putText(frame, name, (center_x - ts[0]//2, center_y + ts[1]//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, font_s, text_col, 2)

        return frame