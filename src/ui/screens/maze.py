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
        
        # Buffer pentru fundal static (optimizare Pi 4)
        self.static_bg = None 

        # --- CONFIG JUMPSCARE ---
        self.TRANSIT_DURATION = 0.2 
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
        jumpscare_path = os.path.join(project_root, "assets", "images", "job_application.png")
        
        self.jumpscare_img = cv2.imread(jumpscare_path)
        if self.jumpscare_img is None:
             self.jumpscare_img = np.zeros((500, 500, 3), dtype=np.uint8)
             self.jumpscare_img[:] = (0, 0, 255)

        # --- VARIABILE UI & INTERACȚIUNE ---
        self.pulse_phase = 0.0
        
        # Butoane pentru Popup
        self.btn_retry_rect = None
        self.btn_menu_rect = None
        
        # Hover logic (pentru a selecta butoanele cu mana)
        self.hover_start_time = 0
        self.hovered_button = None # "RETRY" sau "MENU"
        self.HOVER_THRESHOLD = 1.5 # Secunde de tinut mana pe buton pentru activare

        self.reset()

    def _parse_level(self, width, height):
        # ... (Aceeasi logica de parcurgere grid) ...
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
        
        # --- PRE-RANDARE FUNDAL ---
        self.static_bg = np.zeros((height, width, 3), dtype=np.uint8)
        self.static_bg[:] = (15, 15, 20)
        
        # Grid
        step = 50
        grid_color = (30, 30, 40)
        for x_line in range(0, width, step):
            cv2.line(self.static_bg, (x_line, 0), (x_line, height), grid_color, 1)
        for y_line in range(0, height, step):
            cv2.line(self.static_bg, (0, y_line), (width, y_line), grid_color, 1)

        # Pereti
        wall_color = (255, 200, 0)
        bright_color = (255, 255, 150)
        for (wx, wy, ww, wh) in self.walls:
            cv2.rectangle(self.static_bg, (wx, wy), (wx + ww, wy + wh), (50, 40, 0), -1) 
            cv2.rectangle(self.static_bg, (wx, wy), (wx + ww, wy + wh), wall_color, 2)
            # Colturi
            c = 8
            cv2.line(self.static_bg, (wx, wy), (wx + c, wy), bright_color, 2)
            cv2.line(self.static_bg, (wx, wy), (wx, wy + c), bright_color, 2)

        # --- DEFINIRE BUTOANE POPUP (Centrate) ---
        bw, bh = 200, 60
        cx, cy = width // 2, height // 2
        self.btn_retry_rect = (cx - bw - 20, cy + 50, bw, bh)
        self.btn_menu_rect = (cx + 20, cy + 50, bw, bh)

    def reset(self):
        self.active = True
        self.state = "WAITING" 
        self.message = "Mergi la START!"
        self.msg_color = (0, 255, 0)
        
        self.jumpscare_start_time = 0
        self.win_screen_start_time = 0
        
        self.hovered_button = None
        self.hover_start_time = 0
        self.cursor_norm = (0.5, 0.5) 

    def update(self, cx_norm, cy_norm):
        if not self.active: return
        self.cursor_norm = (cx_norm, cy_norm)
        current_time = time.time()
        self.pulse_phase += 0.2
        
        # Calcul coordonate absolute cursor pentru verificari
        if self.last_dims == (0,0): return
        w, h = self.last_dims
        cx_abs = int(cx_norm * w)
        cy_abs = int(cy_norm * h)

        # --- LOGICA STĂRI ---

        # 1. JUMPSCARE -> WIN SCREEN
        if self.state == "JUMPSCARE":
            if current_time - self.jumpscare_start_time > (self.TRANSIT_DURATION + 2.0):
                self.state = "WIN_SCREEN"
                self.win_screen_start_time = current_time
            return

        # 2. WIN SCREEN -> EXIT
        if self.state == "WIN_SCREEN":
            if current_time - self.win_screen_start_time > 4.0: # Sta 4 secunde
                self.active = False # Iese in meniul principal
            return

        # 3. GAME OVER POPUP (Interactiune cu butoane)
        if self.state == "GAME_OVER_POPUP":
            # Verificam coliziunea cu butoanele
            hit_retry = self._is_point_in_rect((cx_abs, cy_abs), self.btn_retry_rect)
            hit_menu = self._is_point_in_rect((cx_abs, cy_abs), self.btn_menu_rect)
            
            target_btn = "RETRY" if hit_retry else ("MENU" if hit_menu else None)
            
            if target_btn:
                if self.hovered_button != target_btn:
                    # Tocmai am intrat pe buton
                    self.hovered_button = target_btn
                    self.hover_start_time = current_time
                else:
                    # Suntem deja pe buton, verificam cat timp a trecut
                    elapsed = current_time - self.hover_start_time
                    if elapsed >= self.HOVER_THRESHOLD:
                        # CLICK CONFIRMAT!
                        if target_btn == "RETRY":
                            self.reset()
                        else:
                            self.active = False # Back to menu
            else:
                self.hovered_button = None
                self.hover_start_time = 0
            
            return

    def _is_point_in_rect(self, point, rect):
        px, py = point
        rx, ry, rw, rh = rect
        return rx < px < rx + rw and ry < py < ry + rh

    def _check_logic(self, w, h):
        cx = int(self.cursor_norm[0] * w)
        cy = int(self.cursor_norm[1] * h)
        
        if self.state == "WAITING":
            if self.start_rect:
                sx, sy, sw, sh = self.start_rect
                if sx < cx < sx + sw and sy < cy < sy + sh:
                    self.state = "PLAYING"
                    self.message = "FUGI LA EXIT!"
                    self.msg_color = (0, 255, 255)

        elif self.state == "PLAYING":
            # Verificam EXIT (WIN)
            if self.end_rect:
                ex, ey, ew, eh = self.end_rect
                if ex < cx < ex + ew and ey < cy < ey + eh:
                    self.state = "JUMPSCARE"
                    self.jumpscare_start_time = time.time()
                    self.message = "PRINS...?"
                    self.msg_color = (0, 0, 255)
                    return

            # Verificam PERETI (FAIL)
            for (wx, wy, ww, wh) in self.walls:
                if wx < cx < wx + ww and wy < cy < wy + wh:
                    self.state = "GAME_OVER_POPUP"
                    self.message = "AI LOVIT ZIDUL!"
                    self.msg_color = (0, 0, 255)
                    return

    def draw(self, frame):
        h, w, _ = frame.shape
        
        # Init Resize
        if (w, h) != self.last_dims:
            self.last_dims = (w, h)
            self._parse_level(w, h)

        # --- 1. JUMPSCARE (Overlay total) ---
        if self.state == "JUMPSCARE":
            elapsed = time.time() - self.jumpscare_start_time
            if elapsed < self.TRANSIT_DURATION:
                # Zoom effect
                scale = 0.1 + (elapsed / self.TRANSIT_DURATION) * 0.9
                target_w, target_h = int(w * scale), int(h * scale)
                if target_w > 0:
                    small_jmp = cv2.resize(self.jumpscare_img, (target_w, target_h), interpolation=cv2.INTER_NEAREST)
                    y_off = (h - target_h) // 2
                    x_off = (w - target_w) // 2
                    y1, y2 = max(0, y_off), min(h, y_off + target_h)
                    x1, x2 = max(0, x_off), min(w, x_off + target_w)
                    sy1 = max(0, -y_off)
                    sy2 = sy1 + (y2 - y1)
                    sx1 = max(0, -x_off)
                    sx2 = sx1 + (x2 - x1)
                    if (y2>y1) and (x2>x1):
                        frame[y1:y2, x1:x2] = small_jmp[sy1:sy2, sx1:sx2]
            else:
                resized_full = cv2.resize(self.jumpscare_img, (w, h), interpolation=cv2.INTER_NEAREST)
                frame[:] = resized_full
            return frame

        # --- 2. WIN SCREEN (Dupa Jumpscare) ---
        if self.state == "WIN_SCREEN":
            # Fundal Verde
            frame[:] = (0, 50, 0) 
            cv2.putText(frame, "AI CASTIGAT!", (w//2 - 150, h//2), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
            cv2.putText(frame, "Revenire meniu...", (w//2 - 100, h//2 + 50), cv2.FONT_HERSHEY_PLAIN, 1.2, (200, 200, 200), 1)
            return frame

        # --- 3. JOC NORMAL (Background + Wall Check) ---
        if self.static_bg is not None:
            np.copyto(frame, self.static_bg)
        else:
            frame[:] = (15, 15, 20)

        # Logic check daca jucam
        if self.active and self.state not in ["GAME_OVER_POPUP"]:
            self._check_logic(w, h)

        # Desenare Start/Exit
        if self.start_rect:
            sx, sy, sw, sh = self.start_rect
            pulse = (math.sin(self.pulse_phase) + 1) / 2
            col_val = int(100 + 155 * pulse)
            cv2.rectangle(frame, (sx, sy), (sx+sw, sy+sh), (0, col_val, 0), 2)
            cv2.putText(frame, "START", (sx+5, sy+30), cv2.FONT_HERSHEY_PLAIN, 1.2, (255,255,255), 1)
        
        if self.end_rect:
            ex, ey, ew, eh = self.end_rect
            cv2.rectangle(frame, (ex, ey), (ex+ew, ey+eh), (0, 0, 255), 2)
            cv2.putText(frame, "EXIT", (ex+5, ey+30), cv2.FONT_HERSHEY_PLAIN, 1.2, (255,255,255), 1)

        # --- 4. POPUP FAIL (Overlay) ---
        if self.state == "GAME_OVER_POPUP":
            # Overlay intunecat (Simulat simplu prin dreptunghi solid semi-opac doar in zona centrala pentru viteza)
            # Sau pur si simplu un panou opac
            
            panel_w, panel_h = 500, 300
            px, py = (w - panel_w)//2, (h - panel_h)//2
            
            # Panou Fundal
            cv2.rectangle(frame, (px, py), (px+panel_w, py+panel_h), (20, 20, 20), -1)
            cv2.rectangle(frame, (px, py), (px+panel_w, py+panel_h), (0, 0, 255), 2) # Contur Rosu
            
            # Text FAIL
            cv2.putText(frame, "SYSTEM FAILURE", (px + 100, py + 60), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 2)
            
            # Functie desenare buton
            def draw_btn(rect, text, btn_id):
                bx, by, bw, bh = rect
                is_hovered = (self.hovered_button == btn_id)
                
                # Culoare buton
                bg_col = (50, 50, 50) if not is_hovered else (100, 100, 100)
                border_col = (200, 200, 200) if not is_hovered else (0, 255, 0)
                
                cv2.rectangle(frame, (bx, by), (bx+bw, by+bh), bg_col, -1)
                cv2.rectangle(frame, (bx, by), (bx+bw, by+bh), border_col, 2)
                
                # Bara de progres hover
                if is_hovered:
                    elapsed = time.time() - self.hover_start_time
                    prog = min(elapsed / self.HOVER_THRESHOLD, 1.0)
                    fill_w = int(bw * prog)
                    cv2.rectangle(frame, (bx, by+bh-5), (bx+fill_w, by+bh), (0, 255, 0), -1)

                # Text
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                tx = bx + (bw - text_size[0]) // 2
                ty = by + (bh + text_size[1]) // 2
                cv2.putText(frame, text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            draw_btn(self.btn_retry_rect, "MAI INCEARCA", "RETRY")
            draw_btn(self.btn_menu_rect, "MENIU", "MENU")

        # Mesaj HUD (doar daca nu e popup)
        else:
            cv2.rectangle(frame, (0, h-40), (w, h), (0,0,0), -1)
            cv2.putText(frame, f">> {self.message}", (20, h - 12), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.msg_color, 1, cv2.LINE_AA)

        return frame