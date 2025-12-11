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
        
        self.quiz = QuizLogic()
        self.arcade = ArcadeComponent()
        self.maze = MazeGame()
        
        self.PALETTE = {
            "CYAN":   (235, 206, 135),
            "PINK":   (203, 192, 255),
            "BG_DARK": (40, 20, 45),
            "TEXT":   (255, 255, 255)
        }

        # Asset Bubble
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
        sprite_path = os.path.join(project_root, "assets", "images", "pixel_bubble.png")
        self.bubble_sprite = cv2.imread(sprite_path, cv2.IMREAD_UNCHANGED)
        if self.bubble_sprite is None:
            self.bubble_sprite = np.zeros((100, 100, 4), dtype=np.uint8)
            cv2.circle(self.bubble_sprite, (50,50), 45, (50, 50, 50, 255), -1)

        self.buttons = {
            "QUIZ":   (0.25, 0.5, 0.12),
            "ARCADE": (0.50, 0.5, 0.12),
            "MAZE":   (0.75, 0.5, 0.12)
        }
        self.anim_offsets = {k: random.uniform(0, 6.28) for k in self.buttons.keys()}
        self.back_btn_rect = {"BACK": (0.03, 0.05, 0.12, 0.07)}
        
        self.hovered = None
        self.hover_start = 0
        self.progress = 0.0
        self.SELECTION_TIME = 1.5

    def update(self, cx, cy):
        # 1. TRANSMITEM UPDATE LA SUB-JOCURI (CHIAR DACA CX e NONE)
        if self.mode == "QUIZ":
            # Quiz-ul probabil are nevoie de mana, dar transmitem oricum
            if cx is not None:
                result = self.quiz.update(cx, cy)
                if result == "EXIT_TO_APP":
                    self.mode = "MENU"
                    self.quiz.reset()
            return False

        elif self.mode == "ARCADE":
            if cx is not None:
                self.arcade.update(cx, cy)
            if not self.arcade.active:
                self.mode = "MENU"
                self.arcade.reset()
            return False

        elif self.mode == "MAZE":
            # Aici e important: Maze primeste update si cu None, None
            # ca sa ruleze timerele de jumpscare
            self.maze.update(cx, cy)
            if not self.maze.active:
                self.mode = "MENU"
                self.maze.reset()
            return False

        # 2. LOGICA MENIU SELECTIE (Necesita Mana)
        if cx is None or cy is None:
            self.hovered = None
            self.progress = 0.0
            return False

        return self._update_menu(cx, cy)

    def _update_menu(self, cx, cy):
        current_hover = None
        aspect_ratio = 1.77
        
        bx, by, bw, bh = self.back_btn_rect["BACK"]
        if bx < cx < bx + bw and by < cy < by + bh:
            current_hover = "BACK"
        else:
            for name, (bcx, bcy, br) in self.buttons.items():
                dx = cx - bcx
                dy = (cy - bcy) / aspect_ratio
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < br:
                    current_hover = name
                    break
        
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
                    if current_hover == "BACK": return True
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
        if x >= bg_w or y >= bg_h or x + ov_w < 0 or y + ov_h < 0: return background
        bg_x_start, bg_y_start = max(0, x), max(0, y)
        bg_x_end, bg_y_end = min(x + ov_w, bg_w), min(y + ov_h, bg_h)
        roi_w, roi_h = bg_x_end - bg_x_start, bg_y_end - bg_y_start
        if roi_w <= 0 or roi_h <= 0: return background
        roi = background[bg_y_start:bg_y_end, bg_x_start:bg_x_end]
        ov_crop_x, ov_crop_y = bg_x_start - x, bg_y_start - y
        overlay_crop = overlay[ov_crop_y:ov_crop_y+roi_h, ov_crop_x:ov_crop_x+roi_w]
        if overlay_crop.shape[2] == 4:
            alpha = overlay_crop[:, :, 3] / 255.0
            for c in range(3):
                roi[:, :, c] = (alpha * overlay_crop[:, :, c] + (1.0 - alpha) * roi[:, :, c])
        else:
            roi[:] = overlay_crop
        background[bg_y_start:bg_y_end, bg_x_start:bg_x_end] = roi
        return background

    def draw(self, frame):
        if self.mode == "QUIZ": return self.quiz.draw(frame)
        elif self.mode == "ARCADE": return self.arcade.draw(frame)
        elif self.mode == "MAZE": return self.maze.draw(frame)
        
        h, w, _ = frame.shape
        current_time = time.time()
        
        cv2.putText(frame, "ALEGE JOCUL", (w//2 - 150, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.5, self.PALETTE["TEXT"], 3)
        
        # Back Button
        bx, by, bw, bh = self.back_btn_rect["BACK"]
        x1, y1, x2, y2 = int(bx*w), int(by*h), int((bx+bw)*w), int((by+bh)*h)
        is_back = (self.hovered == "BACK")
        col = self.PALETTE["PINK"] if is_back else self.PALETTE["CYAN"]
        
        roi = frame[y1:y2, x1:x2]
        blk = np.zeros_like(roi, dtype=np.uint8); blk[:] = self.PALETTE["BG_DARK"]
        cv2.addWeighted(blk, 0.4, roi, 0.6, 0, roi)
        frame[y1:y2, x1:x2] = roi
        
        cv2.rectangle(frame, (x1,y1), (x2,y2), col, 2)
        if is_back and self.progress > 0:
            cv2.rectangle(frame, (x1, y2-4), (x1+int((x2-x1)*self.progress), y2), self.PALETTE["PINK"], -1)
        cv2.putText(frame, "<< INAPOI", (x1+20, y1+40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.PALETTE["TEXT"], 2)

        # Bubbles
        for name, (cxn, cyn, rn) in self.buttons.items():
            ish = (self.hovered == name)
            sc = 1.1 if ish else 1.0
            off = 0 if ish else math.sin(current_time*2.5 + self.anim_offsets[name])*10
            cx, cy = int(cxn*w), int(cyn*h+off)
            sz = int(rn*w*2*sc)
            res = cv2.resize(self.bubble_sprite, (sz, sz), interpolation=cv2.INTER_NEAREST)
            self.overlay_transparent(frame, res, cx-sz//2, cy-sz//2)
            
            if ish and self.progress > 0:
                cv2.ellipse(frame, (cx, cy), (sz//2, sz//2), -90, 0, 360*self.progress, self.PALETTE["CYAN"], 6)
            
            tcol = self.PALETTE["CYAN"] if ish else self.PALETTE["TEXT"]
            cv2.putText(frame, name, (cx-40, cy+10), cv2.FONT_HERSHEY_SIMPLEX, 1.0*sc, (0,0,0), 4)
            cv2.putText(frame, name, (cx-40, cy+10), cv2.FONT_HERSHEY_SIMPLEX, 1.0*sc, tcol, 2)
            
        return frame