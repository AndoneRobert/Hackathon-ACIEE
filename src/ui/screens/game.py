import cv2
import time

# --- IMPORTURILE CORECTATE ---
# Importăm clasa ta din 'quiz_game.py' și o redenumim temporar 'QuizLogic'
# pentru a nu intra în conflict cu clasa 'QuizGame' de mai jos (care e meniul).
from src.ui.screens.quiz_game import QuizGame as QuizLogic
from src.ui.screens.arcade import ArcadeComponent

class QuizGame: # Aceasta este clasa HUB (Meniul Principal) cerută de main_app.py
    def __init__(self):
        self.mode = "MENU"     # Poate fi: MENU, QUIZ, ARCADE
        self.game_over = False # Flag pentru main_app (dacă vrei să închizi tot)
        
        # Inițializăm instanțele jocurilor
        self.quiz = QuizLogic()
        self.arcade = ArcadeComponent()
        
        # --- CONFIGURARE MENIU ---
        self.buttons = {
            "QUIZ": (0.15, 0.4, 0.3, 0.2), # Stânga
            "JOC":  (0.55, 0.4, 0.3, 0.2)  # Dreapta
        }
        
        # Variabile hover meniu
        self.hovered = None
        self.hover_start = 0
        self.progress = 0.0
        self.SELECTION_TIME = 1.5
        
        # Timer pentru pauza de la finalul quiz-ului
        self.end_game_timer = 0

    def update(self, cx, cy):
        """Dispecer principal: trimite datele la jocul activ sau la meniu."""
        
        # 1. DACĂ SUNTEM ÎN MODUL QUIZ
        if self.mode == "QUIZ":
            self.quiz.update(cx, cy)
            
            # Verificăm dacă quiz-ul a setat flag-ul de final
            if self.quiz.game_over:
                # Așteptăm 4 secunde să vadă scorul, apoi revenim la meniu
                if self.end_game_timer == 0:
                    self.end_game_timer = time.time()
                elif time.time() - self.end_game_timer > 4.0:
                    self.mode = "MENU"
                    self.end_game_timer = 0
            return

        # 2. DACĂ SUNTEM ÎN MODUL ARCADE
        elif self.mode == "ARCADE":
            self.arcade.update(cx, cy)
            
            # Arcade folosește 'active' = False când termină
            if not self.arcade.active:
                self.mode = "MENU"
            return

        # 3. DACĂ SUNTEM ÎN MENIU
        self._update_menu(cx, cy)

    def _update_menu(self, cx, cy):
        current_hover = None
        for name, (bx, by, bw, bh) in self.buttons.items():
            if bx < cx < bx + bw and by < cy < by + bh:
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
                
                if elapsed >= self.SELECTION_TIME:
                    # --- LANSARE JOC ---
                    if current_hover == "QUIZ":
                        # Re-instanțiem QuizLogic pentru a reseta scorul și întrebările
                        self.quiz = QuizLogic()
                        self.mode = "QUIZ"
                    elif current_hover == "JOC":
                        self.arcade.reset()
                        self.mode = "ARCADE"
                    
                    self.hovered = None
                    self.progress = 0.0
        else:
            self.hovered = None
            self.progress = 0.0

    def draw(self, frame):
        # Desenăm jocul activ
        if self.mode == "QUIZ":
            return self.quiz.draw(frame)
        elif self.mode == "ARCADE":
            return self.arcade.draw(frame)
        
        # --- DESENARE MENIU ---
        h, w, _ = frame.shape
        
        # Titlu
        cv2.putText(frame, "ALEGE ACTIVITATEA", (w//2 - 220, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)

        # Butoane
        for name, (bx, by, bw, bh) in self.buttons.items():
            x1, y1 = int(bx * w), int(by * h)
            x2, y2 = int((bx + bw) * w), int((by + bh) * h)
            
            is_hovered = (self.hovered == name)
            
            # Culori
            bg_color = (50, 50, 50)
            border_color = (200, 200, 200)
            
            if is_hovered:
                bg_color = (0, 100, 0) if name == "QUIZ" else (0, 0, 100)
                border_color = (0, 255, 255)

            # Desenare buton
            cv2.rectangle(frame, (x1, y1), (x2, y2), bg_color, -1)
            cv2.rectangle(frame, (x1, y1), (x2, y2), border_color, 3 if is_hovered else 2)
            
            # Bară progres
            if is_hovered:
                bar_w = int((x2 - x1) * self.progress)
                cv2.rectangle(frame, (x1, y2-15), (x1+bar_w, y2), (0, 255, 0), -1)
            
            # Text centrat
            ts = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 2)[0]
            tx = x1 + (x2 - x1 - ts[0]) // 2
            ty = y1 + (y2 - y1 + ts[1]) // 2
            cv2.putText(frame, name, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)

        return frame