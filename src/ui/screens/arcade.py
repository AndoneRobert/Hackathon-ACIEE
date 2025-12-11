import cv2
import time
import random
import numpy as np
import math

class FallingItem:
    def __init__(self, screen_w, item_type, text):
        self.type = item_type # "GOOD" sau "BAD"
        self.text = text
        
        # Pozitie initiala (sus, x random)
        self.x = random.randint(50, screen_w - 50)
        self.y = -50 # Porneste putin deasupra ecranului
        
        # Viteza de cadere (variaza putin pentru realism)
        base_speed = 5
        self.speed = random.uniform(base_speed, base_speed + 3)
        
        self.radius = 35
        self.collected = False
        
        # Culori
        if self.type == "GOOD":
            self.color = (0, 200, 0)     # Verde
            self.border = (0, 255, 0)    # Neon
        else:
            self.color = (0, 0, 200)     # Rosu Inchis
            self.border = (0, 0, 255)    # Rosu Aprins

    def update(self):
        self.y += self.speed

    def draw(self, frame):
        # Desenam ca un cerc cu text
        cv2.circle(frame, (int(self.x), int(self.y)), self.radius, self.color, -1)
        cv2.circle(frame, (int(self.x), int(self.y)), self.radius, self.border, 2)
        
        # Text
        font_scale = 0.6
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
        self.basket_w = 120
        self.basket_h = 60
        
        self.good_labels = ["DATA", "INFO", "WIFI", "JAVA", "PY", "C++", "A+"]
        self.bad_labels = ["BUG", "ERR", "VIRUS", "404", "LAG"]
        
        self.reset()

    def reset(self):
        self.active = True
        self.game_over = False
        self.score = 0
        self.lives = 3
        self.items = []
        self.last_spawn_time = time.time()
        self.game_over_time = 0
        
        # Pozitie cos (controlata de mana)
        self.basket_x = 0 
        
        # --- FIX: Initializam last_cx default la mijloc (0.5) ---
        self.last_cx = 0.5 

    def update(self, cx, cy):
        """
        cx: 0.0 - 1.0 (pozitia mainii pe orizontala)
        """
        if not self.active: return
        
        # Daca e Game Over, asteptam 4 secunde si iesim
        if self.lives <= 0:
            if not self.game_over:
                self.game_over = True
                self.game_over_time = time.time()
            
            if time.time() - self.game_over_time > 4.0:
                self.active = False # Semnal pentru wrapper sa iasa
            return

        # 1. Update Pozitie Cos
        self.last_cx = cx 

        # 2. Spawnare Elemente (Curgere continua)
        spawn_rate = max(0.5, 1.5 - (self.score * 0.05))
        
        if time.time() - self.last_spawn_time > spawn_rate:
            self._spawn_item()
            self.last_spawn_time = time.time()

        # 3. Update Elemente & Coliziuni
        sim_w, sim_h = 1920, 1080 
        basket_px = int(cx * sim_w)
        basket_py = sim_h - 100 
        
        for item in self.items:
            item.update()
            
            # Zona Y
            in_y_range = (item.y + item.radius >= basket_py) and (item.y - item.radius <= basket_py + self.basket_h)
            
            # Zona X
            in_x_range = abs(item.x - basket_px) < (self.basket_w // 2 + item.radius)
            
            if in_y_range and in_x_range and not item.collected:
                item.collected = True
                
                if item.type == "GOOD":
                    self.score += 1
                else:
                    self.lives -= 1 
            
        # Stergem elementele colectate sau iesite din ecran
        self.items = [i for i in self.items if not i.collected and i.y < sim_h + 50]

    def _spawn_item(self):
        sim_w = 1920
        is_bad = (random.random() < 0.4)
        
        if is_bad:
            text = random.choice(self.bad_labels)
            item = FallingItem(sim_w, "BAD", text)
        else:
            text = random.choice(self.good_labels)
            item = FallingItem(sim_w, "GOOD", text)
            
        # Creste viteza itemului in functie de scor
        speed_boost = min(10, self.score * 0.2)
        item.speed += speed_boost
        
        self.items.append(item)

    def draw(self, frame):
        h, w, _ = frame.shape
        
        # --- GAME OVER ---
        if self.game_over:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 50), -1)
            cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
            
            cv2.putText(frame, "GAME OVER", (w//2 - 200, h//2 - 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2.0, (255, 255, 255), 4)
            cv2.putText(frame, f"SCOR FINAL: {self.score}", (w//2 - 180, h//2 + 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)
            return frame

        # --- DESENARE COS (BASKET) ---
        # Folosim self.last_cx care acum e sigur initializat
        basket_x = int(self.last_cx * w)
        basket_y = h - 100
        
        # Corpul cosului
        pt1 = (basket_x - self.basket_w//2, basket_y)
        pt2 = (basket_x + self.basket_w//2, basket_y + self.basket_h)
        
        cv2.rectangle(frame, pt1, pt2, (50, 50, 50), -1) 
        cv2.rectangle(frame, pt1, pt2, (255, 200, 0), 3) 
        
        # Eticheta
        cv2.putText(frame, "CATCHER", (basket_x - 40, basket_y + 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # --- DESENARE ELEMENTE ---
        # Scalam itemele pentru rezolutia curenta daca nu e 1920x1080
        # Simplu: le desenam relativ la width-ul curent
        scale_x = w / 1920
        scale_y = h / 1080
        
        for item in self.items:
            # Salvam pozitiile originale
            orig_x, orig_y = item.x, item.y
            orig_r = item.radius
            
            # Scalam temporar pentru desenare
            item.x = int(orig_x * scale_x)
            item.y = int(orig_y * scale_y)
            item.radius = int(orig_r * min(scale_x, scale_y))
            
            item.draw(frame)
            
            # Restauram (pentru logica update care ruleaza pe coordonate fixe 1920)
            item.x, item.y = orig_x, orig_y
            item.radius = orig_r

        # --- HUD (SCOR & VIETI) ---
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