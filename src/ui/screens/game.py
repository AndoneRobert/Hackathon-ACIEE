import cv2
import time
import math
import os
import random
import numpy as np

# --- IMPORTURI ---
from src.ui.screens.quiz_game import QuizGame as QuizLogic
from src.ui.screens.arcade import ArcadeComponent
from src.ui.screens.maze import MazeGame  # <-- Importăm noua clasă

class QuizGame: # Clasa HUB (Meniul Principal pentru Jocuri)
    def __init__(self):
        self.mode = "MENU"     # Poate fi: MENU, QUIZ, ARCADE, MAZE
        
        # Inițializăm instanțele jocurilor
        self.quiz = QuizLogic()
        self.arcade = ArcadeComponent()
        self.maze = MazeGame() # <-- Instanțiem jocul real
        
        # Flag global (dacă e nevoie să închidem tot)
        self.game_over = False 
        
        # --- CONFIGURARE LAYOUT BULE (3 BUTOANE) ---
        self.layout = {
            "QUIZ": (0.2, 0.5, 0.12),  # Stânga
            "MAZE": (0.5, 0.5, 0.12),  # Centru
            "JOC":  (0.8, 0.5, 0.12)   # Dreapta
        }
        
        # Stare interacțiune
        self.hovered = None
        self.hover_start = 0
        self.progress = 0.0
        self.selection_threshold = 1.5 
        
        self.end_game_timer = 0

        # --- ANIMATION SETUP ---
        self.anim_offsets = {k: random.uniform(0, 6.28) for k in self.layout.keys()}

        # --- ASSET LOADING ---
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
        sprite_path = os.path.join(project_root, "assets", "images", "pixel_bubble.png")
        
        self.bubble_sprite = cv2.imread(sprite_path, cv2.IMREAD_UNCHANGED)
        
        if self.bubble_sprite is None:
            self.bubble_sprite = np.zeros((100, 100, 4), dtype=np.uint8)
            cv2.circle(self.bubble_sprite, (50,50), 45, (50, 50, 50, 255), -1)

    def overlay_transparent(self, background, overlay, x, y):
        """Metodă helper pentru suprapunere"""
        bg_h, bg_w, _ = background.shape
        ov_h, ov_w, ov_c = overlay.shape

        if x >= bg_w or y >= bg_h or x + ov_w < 0 or y + ov_h < 0: 
            return background

        ov_x_start = max(0, x)
        ov_y_start = max(0, y)
        bg_x_start = max(0, x)
        bg_y_start = max(0, y)
        
        ov_x_end = min(x + ov_w, bg_w)
        ov_y_end = min(y + ov_h, bg_h)
        bg_x_end = min(x + ov_w, bg_w)
        bg_y_end = min(y + ov_h, bg_h)
        
        roi_w = bg_x_end - bg_x_start
        roi_h = bg_y_end - bg_y_start
        
        if roi_w <= 0 or roi_h <=0: return background

        roi = background[bg_y_start:bg_y_end, bg_x_start:bg_x_end]
        
        ov_crop_x_start = bg_x_start - x
        ov_crop_y_start = bg_y_start - y
        overlay_crop = overlay[ov_crop_y_start:ov_crop_y_start+roi_h, ov_crop_x_start:ov_crop_x_start+roi_w]

        if overlay_crop.shape[2] == 4:
            alpha = overlay_crop[:, :, 3] / 255.0
            ov_bgr = overlay_crop[:, :, :3]
            for c in range(3):
                roi[:, :, c] = (alpha * ov_bgr[:, :, c] + (1.0 - alpha) * roi[:, :, c])
        else:
            roi[:] = overlay_crop

        background[bg_y_start:bg_y_end, bg_x_start:bg_x_end] = roi
        return background

    def update(self, cx, cy):
        """Dispecer principal"""
        
        # 1. MODUL QUIZ
        if self.mode == "QUIZ":
            self.quiz.update(cx, cy)
            if self.quiz.game_over:
                if self.end_game_timer == 0:
                    self.end_game_timer = time.time()
                elif time.time() - self.end_game_timer > 4.0:
                    self.mode = "MENU"
                    self.end_game_timer = 0
            return

        # 2. MODUL ARCADE
        elif self.mode == "ARCADE":
            self.arcade.update(cx, cy)
            if not self.arcade.active:
                self.mode = "MENU"
            return
            
        # 3. MODUL MAZE
        elif self.mode == "MAZE":
            self.maze.update(cx, cy)
            if not self.maze.active:
                self.mode = "MENU"
            return

        # 4. MENIUL DE SELECȚIE
        self._update_menu(cx, cy)

    def _update_menu(self, cursor_x, cursor_y):
        currently_hovered = None
        aspect_ratio = 1.77 
        
        for name, (btn_cx, btn_cy, r) in self.layout.items():
            dx = cursor_x - btn_cx
            dy = (cursor_y - btn_cy) / aspect_ratio 
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist < r:
                currently_hovered = name
                break
        
        # Hover State Machine
        if currently_hovered != self.hovered:
            self.hovered = currently_hovered
            self.hover_start = time.time()
            self.progress = 0.0
        
        if currently_hovered:
            elapsed = time.time() - self.hover_start
            self.progress = min(elapsed / self.selection_threshold, 1.0)
            
            if elapsed >= self.selection_threshold:
                # --- LANSARE JOC ---
                if currently_hovered == "QUIZ":
                    self.quiz = QuizLogic()
                    self.mode = "QUIZ"
                elif currently_hovered == "JOC":
                    self.arcade.reset()
                    self.mode = "ARCADE"
                elif currently_hovered == "MAZE":
                    self.maze.reset() # Resetare Maze
                    self.mode = "MAZE"
                
                self.hovered = None
                self.progress = 0.0

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
        
        cv2.putText(frame, "ALEGE ACTIVITATEA", (w//2 - 220, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)

        for name, (cx_norm, cy_norm, r_norm) in self.layout.items():
            
            is_hovered = (self.hovered == name)
            
            # Animație
            float_offset_y = 0
            scale_factor = 1.0

            if not is_hovered:
                float_offset_y = math.sin(current_time * 2.5 + self.anim_offsets[name]) * 15
            else:
                scale_factor = 1.1 + 0.05 * math.sin(current_time * 8) 

            # Coordonate
            center_x = int(cx_norm * w)
            center_y = int(cy_norm * h + float_offset_y)
            
            target_diameter = int(r_norm * w * 2 * scale_factor)
            radius_px = target_diameter // 2
            
            # Sprite Bubble
            if self.bubble_sprite is not None:
                resized = cv2.resize(self.bubble_sprite, (target_diameter, target_diameter), interpolation=cv2.INTER_NEAREST)
                frame = self.overlay_transparent(frame, resized, center_x - radius_px, center_y - radius_px)

            # Inel Progres
            if is_hovered and self.progress > 0:
                thickness = 8 
                angle = 360 * self.progress
                cv2.ellipse(frame, (center_x, center_y), (radius_px + thickness//2, radius_px + thickness//2),
                            -90, 0, angle, (0, 255, 255), thickness, lineType=cv2.LINE_4)

            # Text
            font_scale = 1.0 * scale_factor
            thickness = 2
            ts = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
            tx = center_x - ts[0] // 2
            ty = center_y + ts[1] // 2
            
            cv2.putText(frame, name, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0,0,0), thickness+3, lineType=cv2.LINE_4)
            text_color = (200, 255, 255) if is_hovered else (255, 255, 255)
            cv2.putText(frame, name, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, thickness, lineType=cv2.LINE_4)

        return frame