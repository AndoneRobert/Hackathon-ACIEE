import cv2
import time
import random
import numpy as np
import os
import math

class FallingItem:
    def __init__(self, screen_w, item_type, text):
        self.type = item_type # "GOOD", "BAD", sau "TROLL"
        self.text = text
        
        # Pozitie initiala (sus, x random)
        self.x = random.randint(60, screen_w - 60)
        self.y = -60 # Porneste putin deasupra ecranului
        
        # --- MODIFICARE 2: Fast Paced (Viteza mai mare) ---
        base_speed = 9 # Era 5
        self.speed = random.uniform(base_speed, base_speed + 4)
        
        # --- MODIFICARE 1: Elemente putin mai mari ---
        self.radius = 42 # Era 35
        self.collected = False
        
        # --- CONFIGURARE TIPURI ---
        if self.type == "GOOD":
            self.color = (0, 200, 0)     # Verde
            self.border = (0, 255, 0)    # Neon Verde
        elif self.type == "BAD":
            self.color = (0, 0, 200)     # Rosu Inchis
            self.border = (0, 0, 255)    # Rosu Aprins
        elif self.type == "TROLL":
            self.color = (255, 100, 0)   # Albastru/Cyan
            self.border = (255, 255, 255)# Alb
            self.speed += 10             # Foarte rapid
            self.radius = 48             # Si mai mare

    def update(self):
        self.y += self.speed

    def draw(self, frame):
        cv2.circle(frame, (int(self.x), int(self.y)), self.radius, self.color, -1)
        cv2.circle(frame, (int(self.x), int(self.y)), self.radius, self.border, 3)
        
        font_scale = 0.7
        if self.type == "TROLL": font_scale = 1.0
        
        ts = cv2.getTextSize(self.text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)[0]
        tx = int(self.x - ts[0] // 2)
        ty = int(self.y + ts[1] // 2)
        cv2.putText(frame, self.text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 2)

class ArcadeComponent:
    def __init__(self):
        self.active = False
        self.game_over = False
        
        # Setari
        self.COLOR_ACIEE_DARK = (46, 27, 8)
        self.basket_w = 140 # Mai lat pentru laptop
        self.basket_h = 90
        
        self.good_labels = ["DATA", "INFO", "WIFI", "JAVA", "PY", "C++", "A+"]
        self.bad_labels = ["BUG", "ERR", "VIRUS", "404", "LAG"]
        self.troll_labels = ["JOB", "CV", "HR", "BOSS"] 
        
        # Incarcare imagine Troll
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
        img_path = os.path.join(project_root, "assets", "images", "job_application.png")
        
        self.troll_img = cv2.imread(img_path)
        if self.troll_img is None:
            self.troll_img = np.zeros((720, 1280, 3), dtype=np.uint8)
            self.troll_img[:] = (0, 0, 255)

        # --- MODIFICARE 5: Layout Game Over ---
        self.game_over_buttons = {
            "RETRY": (0.15, 0.75, 0.3, 0.15), # Stanga
            "MENU":  (0.55, 0.75, 0.3, 0.15)  # Dreapta
        }
        self.hovered_btn = None
        self.hover_start_time = 0
        self.selection_progress = 0.0
        self.SELECTION_THRESHOLD = 1.5

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
        self.TROLL_DURATION = 2.5 
        
        self.basket_x = 0 
        self.last_cx = 0.5 
        
        # Reset Menu State
        self.hovered_btn = None
        self.selection_progress = 0.0

    def update(self, cx, cy):
        if not self.active: return
        
        # 1. TROLL LOGIC
        if self.troll_active:
            if time.time() - self.troll_start_time > self.TROLL_DURATION:
                self.troll_active = False
            # In timpul troll-ului jocul continua in fundal, dar nu procesam input (pauza vizuala)
            # Sau il lasam sa curga? Sa il lasam sa curga e mai amuzant.
            pass

        # --- MODIFICARE 5: GAME OVER INTERACTIV ---
        if self.lives <= 0:
            self.game_over = True
            
            # Logica de selectie butoane (RETRY / MENU)
            hovered = None
            for key, (bx, by, bw, bh) in self.game_over_buttons.items():
                if bx < cx < bx + bw and by < cy < by + bh:
                    hovered = key
                    break
            
            if hovered and hovered == self.hovered_btn:
                elapsed = time.time() - self.hover_start_time
                self.selection_progress = min(elapsed / self.SELECTION_THRESHOLD, 1.0)
                
                if self.selection_progress >= 1.0:
                    # ACTIUNE
                    if hovered == "RETRY":
                        self.reset()
                    elif hovered == "MENU":
                        self.active = False # Iesim din joc
            else:
                self.hovered_btn = hovered
                self.hover_start_time = time.time()
                self.selection_progress = 0.0
                
            return # Nu mai updatam jocul (iteme etc)

        self.last_cx = cx 

        # Spawnare
        spawn_rate = max(0.4, 1.2 - (self.score * 0.05)) # Si mai rapid spawn rate
        if time.time() - self.last_spawn_time > spawn_rate:
            self._spawn_item()
            self.last_spawn_time = time.time()

        # Update Elemente
        sim_w, sim_h = 1920, 1080 
        basket_px = int(cx * sim_w)
        basket_py = sim_h - 100 
        
        for item in self.items:
            item.update()
            
            # Hitbox putin mai generos pentru laptop
            in_y_range = (item.y + item.radius >= basket_py - 20) and (item.y - item.radius <= basket_py + 40)
            in_x_range = abs(item.x - basket_px) < (self.basket_w // 2 + item.radius)
            
            if in_y_range and in_x_range and not item.collected:
                item.collected = True
                
                if item.type == "GOOD":
                    self.score += 1
                elif item.type == "BAD":
                    self.lives -= 1 
                elif item.type == "TROLL":
                    self.troll_active = True
                    self.troll_start_time = time.time()
                    self.score += 5 
            
        self.items = [i for i in self.items if not i.collected and i.y < sim_h + 50]

    def _spawn_item(self):
        sim_w = 1920
        rand_val = random.random()
        
        if rand_val < 0.08: # 8% sansa Troll
            text = random.choice(self.troll_labels)
            item = FallingItem(sim_w, "TROLL", text)
        elif rand_val < 0.45:
            text = random.choice(self.bad_labels)
            item = FallingItem(sim_w, "BAD", text)
        else:
            text = random.choice(self.good_labels)
            item = FallingItem(sim_w, "GOOD", text)
            
        if item.type != "TROLL":
            speed_boost = min(12, self.score * 0.3)
            item.speed += speed_boost
        
        self.items.append(item)

    # --- MODIFICARE 4: DESENARE LAPTOP (BASKET) ---
    def _draw_laptop(self, frame, x, y):
        # x, y = centrul bazei laptopului
        
        base_w = self.basket_w
        base_h = 20
        screen_h = 80
        screen_w = base_w
        
        # 1. Ecranul (Partea de sus)
        # Contur Gri Inchis
        cv2.rectangle(frame, (x - screen_w//2, y - screen_h), (x + screen_w//2, y), (50, 50, 50), -1)
        # Display (Albastru deschis - stil Windows/Code)
        cv2.rectangle(frame, (x - screen_w//2 + 5, y - screen_h + 5), (x + screen_w//2 - 5, y - 5), (255, 200, 100), -1)
        
        # Linii de cod pe ecran (decor)
        for i in range(3):
            ly = y - screen_h + 20 + (i * 15)
            cv2.line(frame, (x - screen_w//2 + 15, ly), (x + screen_w//2 - 15, ly), (255, 255, 255), 2)

        # 2. Baza (Tastatura)
        # Trapezoid sau dreptunghi simplu pentru viteza
        cv2.rectangle(frame, (x - base_w//2, y), (x + base_w//2, y + base_h), (80, 80, 80), -1)
        # Trackpad
        cv2.rectangle(frame, (x - 20, y + 5), (x + 20, y + 15), (40, 40, 40), -1)

    def draw(self, frame):
        h, w, _ = frame.shape
        
        # --- MODIFICARE 3: TROLL "GET A JOB" ---
        if self.troll_active and self.troll_img is not None:
            troll_overlay = cv2.resize(self.troll_img, (w, h))
            frame[:] = troll_overlay
            
            # Text Mare si Rosu
            cv2.putText(frame, "GET A JOB", (w//2 - 250, h//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 3.0, (0, 0, 255), 8)
            cv2.putText(frame, "GET A JOB", (w//2 - 250, h//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 3.0, (255, 255, 255), 3)
            return frame

        # Game Over Screen Interactiv
        if self.game_over:
            # Fundal intunecat
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), (10, 10, 30), -1)
            cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)
            
            # Mesaj
            cv2.putText(frame, "GAME OVER", (w//2 - 200, h//3), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2.0, (255, 255, 255), 4)
            cv2.putText(frame, f"Scor Final: {self.score}", (w//2 - 150, h//3 + 80), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 2)

            # Desenare Butoane
            for key, (bx, by, bw, bh) in self.game_over_buttons.items():
                x1 = int(bx * w)
                y1 = int(by * h)
                x2 = int((bx + bw) * w)
                y2 = int((by + bh) * h)
                
                is_hovered = (self.hovered_btn == key)
                
                # Culori Modern Tech
                color_bg = (50, 50, 50)
                color_border = (200, 200, 200)
                if is_hovered:
                    color_bg = (0, 100, 0) if key == "RETRY" else (0, 0, 100)
                    color_border = (0, 255, 0) if key == "RETRY" else (0, 100, 255)
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), color_bg, -1)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color_border, 3)
                
                # Progres Bar
                if is_hovered:
                    prog_w = int((x2 - x1) * self.selection_progress)
                    cv2.rectangle(frame, (x1, y2-10), (x1+prog_w, y2), (255, 255, 255), -1)
                
                # Text Buton
                label = "REINCEARCA" if key == "RETRY" else "INAPOI LA MENIU"
                ts = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
                tx = x1 + (x2 - x1 - ts[0]) // 2
                ty = y1 + (y2 - y1 + ts[1]) // 2
                cv2.putText(frame, label, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            return frame

        # --- JOC ACTIV ---
        
        # Desenare Basket (Laptop)
        basket_x = int(self.last_cx * w)
        basket_y = h - 100
        self._draw_laptop(frame, basket_x, basket_y)
        
        # Eticheta sub laptop
        cv2.putText(frame, "DEVELOPER", (basket_x - 50, basket_y + 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Elemente
        scale_x = w / 1920
        scale_y = h / 1080
        
        for item in self.items:
            orig_x, orig_y = item.x, item.y
            orig_r = item.radius
            
            item.x = int(orig_x * scale_x)
            item.y = int(orig_y * scale_y)
            item.radius = int(orig_r * min(scale_x, scale_y))
            
            item.draw(frame)
            
            item.x, item.y = orig_x, orig_y
            item.radius = orig_r

        # HUD
        cv2.rectangle(frame, (0, 0), (w, 80), self.COLOR_ACIEE_DARK, -1)
        cv2.putText(frame, f"SCOR: {self.score}", (30, 55), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
        
        cv2.putText(frame, "VIETI:", (w - 250, 55), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
        for i in range(3):
            color = (0, 0, 255) if i < self.lives else (100, 100, 100)
            cx = w - 100 + (i * 40)
            cy = 45
            cv2.circle(frame, (cx, cy), 15, color, -1)
            cv2.circle(frame, (cx, cy), 15, (255, 255, 255), 2)

        return frame