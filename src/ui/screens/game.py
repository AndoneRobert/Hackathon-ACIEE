import cv2
import time

# --- IMPORTURILE CORECTATE ---
from src.ui.screens.quiz_game import QuizGame as QuizLogic
from src.ui.screens.arcade import ArcadeComponent

class QuizGame: 
    def __init__(self):
        self.mode = "MENU"     
        self.game_over = False 
        
        self.quiz = QuizLogic()
        self.arcade = ArcadeComponent()
        
        # Meniu Selectie Joc
        self.buttons = {
            "QUIZ": (0.15, 0.4, 0.3, 0.2), 
            "JOC":  (0.55, 0.4, 0.3, 0.2) 
        }
        
        self.hovered = None
        self.hover_start = 0
        self.progress = 0.0
        self.SELECTION_TIME = 1.5

    def update(self, cx, cy):
        """
        Returneaza True daca utilizatorul vrea sa iasa in Meniul Principal (Kiosk).
        """
        
        # 1. MODUL QUIZ
        if self.mode == "QUIZ":
            result = self.quiz.update(cx, cy)
            
            # Daca utilizatorul a apasat "Inapoi la Meniul Principal"
            if result == "EXIT_TO_APP":
                return True # Semnal catre main_app sa schimbe starea
                
            return False

        # 2. MODUL ARCADE
        elif self.mode == "ARCADE":
            self.arcade.update(cx, cy)
            if not self.arcade.active:
                self.mode = "MENU"
            return False

        # 3. MODUL MENIU (Selectie Joc)
        self._update_menu(cx, cy)
        return False

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
                    if current_hover == "QUIZ":
                        self.quiz.reset()
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
        if self.mode == "QUIZ":
            return self.quiz.draw(frame)
        elif self.mode == "ARCADE":
            return self.arcade.draw(frame)
        
        # --- DESENARE MENIU SELECTIE ---
        h, w, _ = frame.shape
        cv2.putText(frame, "ALEGE ACTIVITATEA", (w//2 - 220, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)

        for name, (bx, by, bw, bh) in self.buttons.items():
            x1, y1 = int(bx * w), int(by * h)
            x2, y2 = int((bx + bw) * w), int((by + bh) * h)
            
            is_hovered = (self.hovered == name)
            bg_color = (0, 100, 0) if (is_hovered and name == "QUIZ") else (0, 0, 100) if is_hovered else (50, 50, 50)
            border_color = (0, 255, 255) if is_hovered else (200, 200, 200)

            cv2.rectangle(frame, (x1, y1), (x2, y2), bg_color, -1)
            cv2.rectangle(frame, (x1, y1), (x2, y2), border_color, 3 if is_hovered else 2)
            
            if is_hovered:
                bar_w = int((x2 - x1) * self.progress)
                cv2.rectangle(frame, (x1, y2-15), (x1+bar_w, y2), (0, 255, 0), -1)
            
            ts = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 2)[0]
            tx = x1 + (x2 - x1 - ts[0]) // 2
            ty = y1 + (y2 - y1 + ts[1]) // 2
            cv2.putText(frame, name, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)

        return frame