import cv2
import time
import numpy as np
import os
import math
import threading
from collections import deque
from src.core.ai_generator import AIGenerator

class MazeGame:
    def __init__(self):
        self.active = False
        self.ai_generator = AIGenerator()
        
        # Stari: GENERATING, WAITING, PLAYING, JUMPSCARE, WIN_SCREEN, LOST
        self.state = "GENERATING" 
        
        self.level_layout = []
        self.walls = []
        self.start_rect = None
        self.end_rect = None
        self.grid_h = 11
        self.grid_w = 20
        self.last_dims = (0, 0)
        
        # Cursor & Trail (Coada pentru efectul de urma)
        self.cursor_norm = (0.5, 0.5)
        self.trail = deque(maxlen=10) # Pastram ultimele 10 pozitii

        # --- JUMPSCARE CONFIG ---
        self.TRANSIT_DURATION = 0.2 
        self.jumpscare_start_time = 0
        
        # --- IMAGINI ---
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
        jumpscare_path = os.path.join(project_root, "assets", "images", "job_application.png")
        
        self.jumpscare_img = cv2.imread(jumpscare_path)
        if self.jumpscare_img is None:
             self.jumpscare_img = np.zeros((500, 500, 3), dtype=np.uint8)
             self.jumpscare_img[:] = (0, 0, 255)

        # --- INTERFATA LOST / WIN ---
        self.buttons_layout = {
            "RETRY": (0.15, 0.7, 0.3, 0.15), 
            "MENU":  (0.55, 0.7, 0.3, 0.15)
        }
        self.hovered_btn = None
        self.selection_start = 0
        self.selection_progress = 0.0
        self.SELECTION_TIME = 1.5
        
        self.win_start_time = 0
        self.WIN_DISPLAY_TIME = 4.0 

        # --- PALETA CULORI NEON ---
        self.COL_BG = (30, 15, 35)       # Dark Purple/Black
        self.COL_GRID = (60, 40, 70)     # Faint Purple
        self.COL_WALL_FILL = (60, 30, 60)
        self.COL_WALL_BORDER = (235, 206, 135) # Cyan ACIEE
        self.COL_TRAIL = (203, 192, 255) # Pink ACIEE

    def _is_solvable(self, layout):
        # (LOGICA RAMANE NESCHIMBATA - O pastram pentru siguranta)
        rows = len(layout)
        if rows == 0: return False
        start_pos, end_pos = None, None
        for r in range(rows):
            cols_in_row = len(layout[r])
            for c in range(cols_in_row):
                if layout[r][c] == 'S': start_pos = (r, c)
                elif layout[r][c] == 'E': end_pos = (r, c)
        if not start_pos or not end_pos: return False 
        queue = deque([start_pos])
        visited = set([start_pos])
        directions = [(-1,0), (1,0), (0,-1), (0,1)] 
        while queue:
            r, c = queue.popleft()
            if (r, c) == end_pos: return True 
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows:
                    if 0 <= nc < len(layout[nr]):
                        if layout[nr][nc] != '#' and (nr, nc) not in visited:
                            visited.add((nr, nc))
                            queue.append((nr, nc))
        return False 

    def _parse_level(self, width, height):
        self.walls = []
        self.start_rect = None
        self.end_rect = None
        if not self.level_layout: return
        self.grid_h = len(self.level_layout)
        self.grid_w = max([len(row) for row in self.level_layout]) if self.grid_h > 0 else 20
        cell_w = width / self.grid_w
        cell_h = height / self.grid_h
        for r, row in enumerate(self.level_layout):
            for c, char in enumerate(row):
                x, y = int(c * cell_w), int(r * cell_h)
                w, h = int(cell_w) + 1, int(cell_h) + 1
                if char == '#': self.walls.append((x, y, w, h))
                elif char == 'S': self.start_rect = (x, y, w, h)
                elif char == 'E': self.end_rect = (x, y, w, h)
        if not self.start_rect: self.start_rect = (0, 0, int(cell_w), int(cell_h))
        if not self.end_rect: self.end_rect = (int(width-cell_w), int(height-cell_h), int(cell_w), int(cell_h))

    def reset(self):
        self.active = True
        self.state = "GENERATING"
        self.message = "AI genereaza labirintul..."
        self.msg_color = (255, 255, 0)
        self.end_time = 0
        self.jumpscare_start_time = 0
        self.win_start_time = 0
        self.cursor_norm = (0.5, 0.5)
        self.walls = []
        self.trail.clear()
        self.hovered_btn = None
        self.selection_progress = 0.0
        
        thread = threading.Thread(target=self._generate_task)
        thread.daemon = True
        thread.start()

    def _generate_task(self):
        try:
            print("Maze: Solicitare layout nou de la Gemini...")
            generated_layout = self.ai_generator.generate_maze()
            if self._is_solvable(generated_layout):
                print("Maze: Layout validat!")
                self.level_layout = generated_layout
            else:
                print("Maze: Layout invalid. Fallback.")
                self.level_layout = self.ai_generator.get_fallback_maze()
            self.state = "READY_TO_START"
        except Exception as e:
            print(f"Maze Error: {e}")
            self.level_layout = self.ai_generator.get_fallback_maze()
            self.state = "READY_TO_START"

    def update(self, cx_norm, cy_norm):
        if not self.active: return
        if cx_norm is None: cx_norm = 0.5
        if cy_norm is None: cy_norm = 0.5
        
        self.cursor_norm = (cx_norm, cy_norm)
        current_time = time.time()
        
        # Actualizare Trail (doar in timpul jocului)
        if self.state in ["WAITING", "PLAYING"]:
            self.trail.append(self.cursor_norm)

        # Logica stari
        if self.state == "READY_TO_START":
            self.state = "WAITING"
            self.message = "Vino in zona VERDE!"
            self.msg_color = (255, 255, 255)
            self.last_dims = (0, 0) 
        elif self.state == "GENERATING": return
        elif self.state == "JUMPSCARE":
            if current_time - self.jumpscare_start_time > self.TRANSIT_DURATION + 2.0:
                self.state = "WIN_SCREEN"
                self.win_start_time = current_time
            return
        elif self.state == "WIN_SCREEN":
            if current_time - self.win_start_time > self.WIN_DISPLAY_TIME:
                self.active = False
            return
        elif self.state == "LOST":
            self._update_buttons_interaction(cx_norm, cy_norm)
            return

        self._check_logic()

    def _update_buttons_interaction(self, cx, cy):
        hovered = None
        for key, (bx, by, bw, bh) in self.buttons_layout.items():
            if bx < cx < bx + bw and by < cy < by + bh:
                hovered = key
                break
        
        if hovered and hovered == self.hovered_btn:
            elapsed = time.time() - self.selection_start
            self.selection_progress = min(elapsed / self.SELECTION_TIME, 1.0)
            if self.selection_progress >= 1.0:
                self.selection_progress = 0.0
                if hovered == "RETRY": self.reset()
                elif hovered == "MENU": self.active = False
        else:
            self.hovered_btn = hovered
            self.selection_start = time.time()
            self.selection_progress = 0.0

    def _check_logic(self):
        w, h = self.last_dims
        if w == 0 or h == 0: return
        cx = int(self.cursor_norm[0] * w)
        cy = int(self.cursor_norm[1] * h)
        
        if self.state == "WAITING":
            if self.start_rect:
                sx, sy, sw, sh = self.start_rect
                if sx < cx < sx + sw and sy < cy < sy + sh:
                    self.state = "PLAYING"
                    self.message = "Rezolva labirintul!"
                    self.msg_color = (0, 255, 255)
        elif self.state == "PLAYING":
            if self.end_rect:
                ex, ey, ew, eh = self.end_rect
                if ex < cx < ex + ew and ey < cy < ey + eh:
                    self.state = "JUMPSCARE"
                    self.jumpscare_start_time = time.time()
                    return
            for (wx, wy, ww, wh) in self.walls:
                if wx < cx < wx + ww and wy < cy < wy + wh:
                    self.state = "LOST"
                    self.message = "AI LOVIT ZIDUL!"
                    self.msg_color = (0, 0, 255)
                    return

    def _draw_tech_grid(self, frame, w, h):
        """Deseneaza un grilaj subtil in fundal - Foarte rapid."""
        # Linii Verticale
        for x in range(0, w, 60):
            cv2.line(frame, (x, 0), (x, h), self.COL_GRID, 1)
        # Linii Orizontale
        for y in range(0, h, 60):
            cv2.line(frame, (0, y), (w, y), self.COL_GRID, 1)

    def draw(self, frame):
        h, w, _ = frame.shape
        self.last_dims = (w, h)
        
        # --- 1. ECRAN GENERARE ---
        if self.state == "GENERATING":
            cv2.rectangle(frame, (0,0), (w,h), self.COL_BG, -1)
            self._draw_tech_grid(frame, w, h)
            msg = "GENERARE LABIRINT..."
            pulse = abs(math.sin(time.time() * 4))
            col = (0, int(255 * pulse), 255)
            font = cv2.FONT_HERSHEY_SIMPLEX
            ts = cv2.getTextSize(msg, font, 1.2, 3)[0]
            cv2.putText(frame, msg, ((w-ts[0])//2, h//2), font, 1.2, col, 3)
            return frame

        # --- 2. ECRAN WIN ---
        if self.state == "WIN_SCREEN":
            frame[:] = 0 # Negru
            msgs = ["FELICITARI!", "Ai castigat!"]
            font = cv2.FONT_HERSHEY_SIMPLEX
            y_off = h // 2 - 50
            for i, line in enumerate(msgs):
                scale = 2.0 if i == 0 else 1.2
                color = (0, 255, 0) if i == 0 else (200, 200, 200)
                thick = 4 if i == 0 else 2
                ts = cv2.getTextSize(line, font, scale, thick)[0]
                cv2.putText(frame, line, ((w - ts[0]) // 2, y_off), font, scale, color, thick)
                y_off += 80
            return frame

        # --- 3. JUMPSCARE ---
        if self.state == "JUMPSCARE" and self.jumpscare_img is not None:
            frame[:] = 0 
            elapsed = time.time() - self.jumpscare_start_time
            progress = min(elapsed / self.TRANSIT_DURATION, 1.0)
            scale = 0.1 + (progress**3) * 0.9 
            tw, th = int(w * scale), int(h * scale)
            if tw > 0 and th > 0:
                resized = cv2.resize(self.jumpscare_img, (tw, th))
                x_off = (w - tw) // 2
                y_off = (h - th) // 2
                frame[y_off:y_off+th, x_off:x_off+tw] = resized
            return frame
        
        # --- 4. GAMEPLAY (NEON STYLE) ---
        if self.level_layout and not self.walls: self._parse_level(w, h)

        # A. Fundal & Grid
        cv2.rectangle(frame, (0,0), (w,h), self.COL_BG, -1)
        self._draw_tech_grid(frame, w, h)
        
        # B. Pereti (Stil Neon: Fill transparent + Border)
        # Optimizare: Desenam toti peretii
        for (wx, wy, ww, wh) in self.walls:
            # Poti comenta linia de fill daca vrei transparenta totala pentru performanta MAXIMA
            cv2.rectangle(frame, (wx+2, wy+2), (wx+ww-2, wy+wh-2), self.COL_WALL_FILL, -1)
            cv2.rectangle(frame, (wx, wy), (wx+ww, wy+wh), self.COL_WALL_BORDER, 2)
            # Detaliu "Tech" (un punct in mijloc)
            cv2.circle(frame, (wx + ww//2, wy + wh//2), 2, self.COL_WALL_BORDER, -1)
            
        # C. Start Zone (Pulse Green)
        if self.start_rect:
            sx, sy, sw, sh = self.start_rect
            pulse = 0.5 + 0.5 * math.sin(time.time() * 5) # 0.0 -> 1.0
            color_s = (0, int(150 + 100*pulse), 0)
            cv2.rectangle(frame, (sx, sy), (sx+sw, sy+sh), color_s, -1)
            cv2.putText(frame, "S", (sx+sw//2-10, sy+sh//2+10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
        
        # D. End Zone (Pulse Red)
        if self.end_rect:
            ex, ey, ew, eh = self.end_rect
            pulse = 0.5 + 0.5 * math.cos(time.time() * 5)
            color_e = (0, 0, int(150 + 100*pulse))
            cv2.rectangle(frame, (ex, ey), (ex+ew, ey+eh), color_e, -1)
            cv2.putText(frame, "E", (ex+ew//2-10, ey+eh//2+10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)

        # E. Player Trail (Coada)
        for i, (tx, ty) in enumerate(self.trail):
            px, py = int(tx * w), int(ty * h)
            # Cerculete care se micsoreaza
            radius = int(5 + i * 1.5) 
            alpha = (i + 1) / len(self.trail)
            col = tuple(int(c * alpha) for c in self.COL_TRAIL)
            cv2.circle(frame, (px, py), radius, col, -1)

        # Mesaj jos (daca nu e LOST)
        if self.state != "LOST":
            # Bara neagra semitransparenta
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, h-60), (w, h), (0,0,0), -1)
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
            cv2.putText(frame, self.message, (50, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 1, self.msg_color, 2)

        # --- 5. ECRAN LOST OVERLAY ---
        if self.state == "LOST":
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 50), -1) 
            cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
            
            cv2.putText(frame, "AI LOVIT ZIDUL!", (w//2 - 200, h//2 - 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)

            for key, (bx, by, bw, bh) in self.buttons_layout.items():
                x1, y1 = int(bx * w), int(by * h)
                x2, y2 = int((bx + bw) * w), int((by + bh) * h)
                is_hovered = (self.hovered_btn == key)
                
                bg_col = (0, 100, 0) if (key == "RETRY" and is_hovered) else \
                         (0, 0, 100) if (key == "MENU" and is_hovered) else (50, 50, 50)
                border_col = (0, 255, 0) if is_hovered else (200, 200, 200)

                cv2.rectangle(frame, (x1, y1), (x2, y2), bg_col, -1)
                cv2.rectangle(frame, (x1, y1), (x2, y2), border_col, 2)
                
                if is_hovered:
                    prog_w = int((x2 - x1) * self.selection_progress)
                    cv2.rectangle(frame, (x1, y2-10), (x1+prog_w, y2), (255, 255, 255), -1)
                
                label = "REINCEARCA" if key == "RETRY" else "IESIRE MENIU"
                ts = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
                tx = x1 + (x2 - x1 - ts[0]) // 2
                ty = y1 + (y2 - y1 + ts[1]) // 2
                cv2.putText(frame, label, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        return frame