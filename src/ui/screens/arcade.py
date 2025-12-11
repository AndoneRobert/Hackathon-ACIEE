import cv2
import time
import random
import numpy as np
import os
import math

class FallingItem:
    def __init__(self, screen_w, item_type, text):
        self.type = item_type 
        self.text = text
        
        # Pozitie initiala
        self.x = random.randint(70, screen_w - 70)
        self.y = -70 
        
        # Viteza
        base_speed = 20 
        self.speed = random.uniform(base_speed, base_speed + 3)
        
        # Dimensiune
        self.radius = 50 
        self.collected = False
        
        # Culori & Text
        if self.type == "GOOD":
            self.color = (0, 200, 0)     # Verde
            self.border = (0, 255, 0)    # Neon Verde
            self.text_color = (0, 0, 0)  # --- TEXT NEGRU (Contrast mai bun) ---
        elif self.type == "TROLL":
            self.color = (255, 100, 0)   # Albastru/Cyan
            self.border = (255, 255, 255)# Alb
            self.text_color = (255, 255, 255) # Text Alb
            self.speed += 8              # TROLL e mult mai rapid
            self.radius = 55             

    def update(self):
        self.y += self.speed

    def draw(self, frame, shake_x=0, shake_y=0):
        # Aplicam shake-ul la coordonatele de desenare
        draw_x = int(self.x + shake_x)
        draw_y = int(self.y + shake_y)
        
        cv2.circle(frame, (draw_x, draw_y), self.radius, self.color, -1)
        cv2.circle(frame, (draw_x, draw_y), self.radius, self.border, 3)
        
        font_scale = 0.8
        if self.type == "TROLL": font_scale = 1.1
        
        ts = cv2.getTextSize(self.text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)[0]
        tx = int(draw_x - ts[0] // 2)
        ty = int(draw_y + ts[1] // 2)
        
        # Folosim culoarea textului definita in __init__
        cv2.putText(frame, self.text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, self.text_color, 2)

class ArcadeComponent:
    def __init__(self):
        self.active = False
        self.game_over = False
        
        # Dimensiuni Basket
        self.basket_w = 150 
        self.basket_h = 100
        
        self.good_labels = ["DATA", "INFO", "WIFI", "JAVA", "PY", "C++", "HTML", "CSS", "JS", "SQL"]
        self.troll_labels = ["JOB", "CV", "HR", "BOSS"] 
        
        # Incarcare imagine Troll
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
        img_path = os.path.join(project_root, "assets", "images", "job_application.png")
        
        self.troll_img = cv2.imread(img_path)
        if self.troll_img is None:
            self.troll_img = np.zeros((720, 1280, 3), dtype=np.uint8)
            self.troll_img[:] = (0, 0, 255)

        # High Score Session-Based
        self.high_score = 0

        # Game Over Buttons
        self.game_over_buttons = {
            "RETRY": (0.15, 0.75, 0.3, 0.15), 
            "MENU":  (0.55, 0.75, 0.3, 0.15)  
        }
        
        # Buton Back
        self.back_btn_layout = (0.03, 0.05, 0.12, 0.07) 
        self.back_hovered = False
        self.back_start_time = 0
        self.back_progress = 0.0
        
        self.PALETTE = {
            "CYAN":   (235, 206, 135),
            "PINK":   (203, 192, 255),
            "BG_DARK": (40, 20, 45),
            "TEXT":   (255, 255, 255)
        }

        self.hovered_btn = None
        self.hover_start_time = 0
        self.selection_progress = 0.0
        self.SELECTION_THRESHOLD = 1.5

        # Damage Effects
        self.damage_timer = 0
        self.shake_intensity = 0

        self.reset()

    def reset(self):
        self.active = True
        self.game_over = False
        
        self.score = 0
        self.lives = 3
        
        self.items = []
        self.last_spawn_time = time.time()
        
        self.troll_active = False
        self.troll_start_time = 0
        self.TROLL_DURATION = 0.5 
        
        self.basket_x = 0 
        self.last_cx = 0.5 
        
        self.hovered_btn = None
        self.selection_progress = 0.0
        self.back_hovered = False
        self.back_progress = 0.0
        
        # Reset Damage Effect
        self.damage_timer = 0
        self.shake_intensity = 0

    def _trigger_damage(self):
        """Activeaza efectul de damage (Flash rosu + Shake)"""
        self.lives -= 1
        self.damage_timer = time.time()
        self.shake_intensity = 25 

    def update(self, cx, cy):
        if not self.active: return
        
        # --- VERIFICARE BUTON BACK ---
        if not self.game_over and not self.troll_active:
            bx, by, bw, bh = self.back_btn_layout
            if bx < cx < bx + bw and by < cy < by + bh:
                if not self.back_hovered:
                    self.back_hovered = True
                    self.back_start_time = time.time()
                    self.back_progress = 0.0
                else:
                    elapsed = time.time() - self.back_start_time
                    self.back_progress = min(elapsed / self.SELECTION_THRESHOLD, 1.0)
                    if self.back_progress >= 1.0:
                        self.active = False 
            else:
                self.back_hovered = False
                self.back_progress = 0.0

        # TROLL LOGIC
        if self.troll_active:
            if time.time() - self.troll_start_time > self.TROLL_DURATION:
                self.troll_active = False

        # GAME OVER LOGIC
        if self.lives <= 0:
            if not self.game_over:
                self.game_over = True
                if self.score > self.high_score:
                    self.high_score = self.score
            
            # Selectie butoane Game Over
            hovered = None
            for key, (bx, by, bw, bh) in self.game_over_buttons.items():
                if bx < cx < bx + bw and by < cy < by + bh:
                    hovered = key
                    break
            
            if hovered and hovered == self.hovered_btn:
                elapsed = time.time() - self.hover_start_time
                self.selection_progress = min(elapsed / self.SELECTION_THRESHOLD, 1.0)
                
                if self.selection_progress >= 1.0:
                    if hovered == "RETRY":
                        self.reset()
                    elif hovered == "MENU":
                        self.active = False 
            else:
                self.hovered_btn = hovered
                self.hover_start_time = time.time()
                self.selection_progress = 0.0
                
            return 

        self.last_cx = cx 

        # --- SPAWNARE ---
        spawn_delay = max(0.4, 0.9 - (self.score * 0.02))
        
        if time.time() - self.last_spawn_time > spawn_delay:
            self._spawn_item()
            self.last_spawn_time = time.time()

        # Update Elemente
        sim_w, sim_h = 1920, 1080 
        basket_px = int(cx * sim_w)
        basket_py = sim_h - 100 
        
        for item in self.items:
            item.update()
            
            # Hitbox
            in_y_range = (item.y + item.radius >= basket_py - 20) and (item.y - item.radius <= basket_py + 40)
            in_x_range = abs(item.x - basket_px) < (self.basket_w // 2 + item.radius)
            
            # 1. PRINS
            if in_y_range and in_x_range and not item.collected:
                item.collected = True
                if item.type == "GOOD":
                    self.score += 1
                elif item.type == "TROLL":
                    self.troll_active = True
                    self.troll_start_time = time.time()
                    self.score += 5
            
            # 2. RATAT (Doar pentru GOOD items)
            if item.y > sim_h + 50 and not item.collected:
                if item.type == "GOOD":
                    item.collected = True 
                    self._trigger_damage()

        # Curatare lista
        self.items = [i for i in self.items if not i.collected and i.y < sim_h + 100]

    def _spawn_item(self):
        sim_w = 1920
        rand_val = random.random()
        
        if rand_val < 0.15: 
            text = random.choice(self.troll_labels)
            item = FallingItem(sim_w, "TROLL", text)
        else:
            text = random.choice(self.good_labels)
            item = FallingItem(sim_w, "GOOD", text)
            
        speed_boost = min(15, self.score * 0.5)
        item.speed += speed_boost
        
        self.items.append(item)

    def _draw_laptop(self, frame, x, y, shake_x, shake_y):
        x += int(shake_x)
        y += int(shake_y)
        
        base_w = self.basket_w
        base_h = 20
        screen_h = 80
        screen_w = base_w
        
        cv2.rectangle(frame, (x - screen_w//2, y - screen_h), (x + screen_w//2, y), (50, 50, 50), -1)
        cv2.rectangle(frame, (x - screen_w//2 + 5, y - screen_h + 5), (x + screen_w//2 - 5, y - 5), (255, 200, 100), -1)
        
        for i in range(3):
            ly = y - screen_h + 20 + (i * 15)
            cv2.line(frame, (x - screen_w//2 + 15, ly), (x + screen_w//2 - 15, ly), (255, 255, 255), 2)

        cv2.rectangle(frame, (x - base_w//2, y), (x + base_w//2, y + base_h), (80, 80, 80), -1)
        cv2.rectangle(frame, (x - 20, y + 5), (x + 20, y + 15), (40, 40, 40), -1)

    def _draw_heart(self, frame, x, y, size, active):
        color = (0, 0, 255) if active else (50, 50, 50) 
        
        radius = size // 2
        cv2.circle(frame, (x - radius, y - radius), radius, color, -1)
        cv2.circle(frame, (x + radius, y - radius), radius, color, -1)
        
        pt1 = (x - size, y - radius + 3)
        pt2 = (x + size, y - radius + 3)
        pt3 = (x, y + size)
        
        triangle_cnt = np.array( [pt1, pt2, pt3] )
        cv2.fillPoly(frame, [triangle_cnt], color)

    def _draw_back_button(self, frame):
        h, w, _ = frame.shape
        bx, by, bw, bh = self.back_btn_layout
        x1, y1 = int(bx * w), int(by * h)
        x2, y2 = int((bx + bw) * w), int((by + bh) * h)
        
        corner_color = self.PALETTE["PINK"] if self.back_hovered else self.PALETTE["CYAN"]
        bg_color = self.PALETTE["BG_DARK"]
        
        roi = frame[y1:y2, x1:x2]
        block = np.zeros_like(roi, dtype=np.uint8)
        block[:] = bg_color
        cv2.addWeighted(block, 0.4, roi, 0.6, 0, roi)
        frame[y1:y2, x1:x2] = roi
        
        corner_w = int((x2-x1) * 0.3)
        corner_h = int((y2-y1) * 0.4)
        thick = 3 if self.back_hovered else 2
        
        cv2.line(frame, (x1, y1), (x1+corner_w, y1), corner_color, thick)
        cv2.line(frame, (x1, y1), (x1, y1+corner_h), corner_color, thick)
        cv2.line(frame, (x2, y2), (x2-corner_w, y2), corner_color, thick)
        cv2.line(frame, (x2, y2), (x2, y2-corner_h), corner_color, thick)
        
        if self.back_hovered and self.back_progress > 0:
            pw = int((x2-x1) * self.back_progress)
            cv2.rectangle(frame, (x1, y2-4), (x1+pw, y2), self.PALETTE["PINK"], -1)
            
        label = "<< INAPOI"
        ts = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        tx = x1 + (x2-x1-ts[0]) // 2
        ty = y1 + (y2-y1+ts[1]) // 2
        cv2.putText(frame, label, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.PALETTE["TEXT"], 2)

    def draw(self, frame):
        h, w, _ = frame.shape
        
        shake_x, shake_y = 0, 0
        damage_elapsed = time.time() - self.damage_timer
        is_damaged = (damage_elapsed < 0.4) 
        
        if is_damaged:
            shake_x = random.randint(-self.shake_intensity, self.shake_intensity)
            shake_y = random.randint(-self.shake_intensity, self.shake_intensity)
            self.shake_intensity = max(0, int(self.shake_intensity * 0.9))

        if self.troll_active and self.troll_img is not None:
            troll_overlay = cv2.resize(self.troll_img, (w, h))
            frame[:] = troll_overlay
            cv2.putText(frame, "GET A JOB", (w//2 - 250, h//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 3.0, (0, 0, 255), 8)
            cv2.putText(frame, "GET A JOB", (w//2 - 250, h//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 3.0, (255, 255, 255), 3)
            return frame

        if self.game_over:
            overlay = frame.copy()
            bg_overlay = (10, 10, 30)
            cv2.rectangle(overlay, (0, 0), (w, h), bg_overlay, -1)
            cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)
            
            title = "GAME OVER"
            title_col = (0, 0, 255)

            cv2.putText(frame, title, (w//2 - 200, h//3), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2.0, title_col, 5)
            cv2.putText(frame, title, (w//2 - 200, h//3), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2.0, (255, 255, 255), 2)
            
            cv2.putText(frame, f"Scor Final: {self.score}", (w//2 - 150, h//3 + 80), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
            
            hs_text = f"CEL MAI BUN (SESIUNE): {self.high_score}"
            cv2.putText(frame, hs_text, (w//2 - 200, h//3 + 140), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 215, 255), 2)

            for key, (bx, by, bw, bh) in self.game_over_buttons.items():
                x1 = int(bx * w)
                y1 = int(by * h)
                x2 = int((bx + bw) * w)
                y2 = int((by + bh) * h)
                
                is_hovered = (self.hovered_btn == key)
                
                color_bg = (50, 50, 50)
                color_border = (200, 200, 200)
                if is_hovered:
                    color_bg = (0, 100, 0) if key == "RETRY" else (0, 0, 100)
                    color_border = (0, 255, 0) if key == "RETRY" else (0, 100, 255)
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), color_bg, -1)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color_border, 3)
                
                if is_hovered:
                    prog_w = int((x2 - x1) * self.selection_progress)
                    cv2.rectangle(frame, (x1, y2-10), (x1+prog_w, y2), (255, 255, 255), -1)
                
                label = "REINCEARCA" if key == "RETRY" else "INAPOI LA JOCURI"
                ts = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
                tx = x1 + (x2 - x1 - ts[0]) // 2
                ty = y1 + (y2 - y1 + ts[1]) // 2
                cv2.putText(frame, label, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            return frame

        if is_damaged:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 255), -1) 
            cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)

        basket_x = int(self.last_cx * w)
        basket_y = h - 100
        self._draw_laptop(frame, basket_x, basket_y, shake_x, shake_y)
        
        scale_x = w / 1920
        scale_y = h / 1080
        
        for item in self.items:
            orig_x, orig_y = item.x, item.y
            orig_r = item.radius
            
            item.x = int(orig_x * scale_x)
            item.y = int(orig_y * scale_y)
            item.radius = int(orig_r * min(scale_x, scale_y))
            
            item.draw(frame, shake_x, shake_y)
            
            item.x, item.y = orig_x, orig_y
            item.radius = orig_r

        self._draw_back_button(frame)
        
        heart_size = 18 
        spacing = 50
        
        for i in range(3):
            lx_normal = (w - 180) + (i * spacing)
            is_active = (i < self.lives)
            self._draw_heart(frame, lx_normal, 60, heart_size, is_active)

        score_text = f"SCOR: {self.score}"
        ts_score = cv2.getTextSize(score_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
        score_x = (w - 200) - ts_score[0] - 20 
        score_y = 70 
        
        cv2.putText(frame, score_text, (score_x + 2, score_y + 2), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3)
        cv2.putText(frame, score_text, (score_x, score_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                   
        hs_small = f"BEST: {self.high_score}"
        cv2.putText(frame, hs_small, (w - 250, 110), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 0), 2)

        return frame