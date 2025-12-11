import cv2
import time
import numpy as np

# --- IMPORTURILE CORECTATE ---
from src.ui.screens.quiz_game import QuizGame as QuizLogic
from src.ui.screens.arcade import ArcadeComponent

class QuizGame: # Aceasta este clasa HUB (Meniul Principal de Jocuri)
    def __init__(self):
        self.mode = "MENU"     
        self.game_over = False 
        
        # Inițializăm instanțele jocurilor
        self.quiz = QuizLogic()
        self.arcade = ArcadeComponent()
        
        # --- CONFIGURARE BUTOANE ---
        
        # 1. Butoanele pentru Jocuri (Centru)
        self.game_buttons = {
            "QUIZ": (0.15, 0.4, 0.3, 0.2), # Stânga
            "JOC":  (0.55, 0.4, 0.3, 0.2)  # Dreapta
        }
        
        # 2. Butonul de INAPOI (Stanga Sus - Vizibil)
        # Coordonate: x, y, width, height
        self.back_btn_layout = {
            "BACK": (0.03, 0.03, 0.15, 0.08)
        }
        
        self.hovered = None
        self.hover_start = 0
        self.progress = 0.0
        self.SELECTION_TIME = 1.5

    def update(self, cx, cy):
        """
        Returneaza True daca utilizatorul vrea sa iasa in Meniul Principal al aplicatiei.
        """
        
        # 1. MODUL QUIZ
        if self.mode == "QUIZ":
            result = self.quiz.update(cx, cy)
            if result == "EXIT_TO_APP":
                return True 
            return False

        # 2. MODUL ARCADE
        elif self.mode == "ARCADE":
            self.arcade.update(cx, cy)
            if not self.arcade.active:
                self.mode = "MENU"
            return False

        # 3. MODUL MENIU (Selectie Joc)
        return self._update_menu(cx, cy)

    def _update_menu(self, cx, cy):
        """Verifica hover pe butoanele de joc sau pe butonul Back."""
        current_hover = None
        
        # A. Verificam Butonul BACK
        bx, by, bw, bh = self.back_btn_layout["BACK"]
        if bx < cx < bx + bw and by < cy < by + bh:
            current_hover = "BACK"
        else:
            # B. Verificam Butoanele de Joc
            for name, (bx, by, bw, bh) in self.game_buttons.items():
                if bx < cx < bx + bw and by < cy < by + bh:
                    current_hover = name
                    break
        
        # Logica de selectie (Timer)
        if current_hover:
            if self.hovered != current_hover:
                self.hovered = current_hover
                self.hover_start = time.time()
                self.progress = 0.0
            else:
                elapsed = time.time() - self.hover_start
                self.progress = min(elapsed / self.SELECTION_TIME, 1.0)
                
                if elapsed >= self.SELECTION_TIME:
                    # Actiune confirmata!
                    self.hovered = None
                    self.progress = 0.0
                    
                    if current_hover == "BACK":
                        return True # Iesire catre main_app
                    elif current_hover == "QUIZ":
                        self.quiz.reset()
                        self.mode = "QUIZ"
                    elif current_hover == "JOC":
                        self.arcade.reset()
                        self.mode = "ARCADE"
        else:
            self.hovered = None
            self.progress = 0.0
            
        return False

    def draw(self, frame):
        # Daca e activ un joc, il desenam pe ala
        if self.mode == "QUIZ":
            return self.quiz.draw(frame)
        elif self.mode == "ARCADE":
            return self.arcade.draw(frame)
        
        # --- DESENARE MENIU SELECTIE ---
        h, w, _ = frame.shape
        
        # Titlu
        cv2.putText(frame, "ALEGE ACTIVITATEA", (w//2 - 220, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)

        # 1. Desenam Butoanele de Joc
        for name, coords in self.game_buttons.items():
            self._draw_button_style(frame, name, name, coords, is_back=False)

        # 2. Desenam Butonul de INAPOI
        coords = self.back_btn_layout["BACK"]
        self._draw_button_style(frame, "BACK", "<< INAPOI", coords, is_back=True)

        return frame

    def _draw_button_style(self, frame, key, text, coords, is_back=False):
        """Helper pentru desenarea unitara a butoanelor."""
        bx, by, bw, bh = coords
        h, w, _ = frame.shape
        
        x1, y1 = int(bx * w), int(by * h)
        x2, y2 = int((bx + bw) * w), int((by + bh) * h)
        
        is_hovered = (self.hovered == key)
        
        # Culori
        if is_back:
            # Stil Rosu/Visiniu pentru Back
            bg_color = (0, 0, 100) if is_hovered else (20, 20, 60)
            border_color = (0, 0, 255) if is_hovered else (100, 100, 150)
        else:
            # Stil Normal (Verde/Albastru)
            bg_color = (0, 100, 0) if (is_hovered and key == "QUIZ") else (0, 0, 100) if is_hovered else (50, 50, 50)
            border_color = (0, 255, 255) if is_hovered else (200, 200, 200)

        # Desenare Cutie
        cv2.rectangle(frame, (x1, y1), (x2, y2), bg_color, -1)
        cv2.rectangle(frame, (x1, y1), (x2, y2), border_color, 3 if is_hovered else 2)
        
        # Bara Progres
        if is_hovered:
            bar_w = int((x2 - x1) * self.progress)
            cv2.rectangle(frame, (x1, y2-10), (x1+bar_w, y2), (0, 255, 0), -1)
        
        # Text
        font_scale = 0.7 if is_back else 1.2
        thick = 2
        ts = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thick)[0]
        tx = x1 + (x2 - x1 - ts[0]) // 2
        ty = y1 + (y2 - y1 + ts[1]) // 2
        cv2.putText(frame, text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thick)