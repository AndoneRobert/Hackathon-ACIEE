import time
import cv2

class MenuController:
    def __init__(self):
        self.DWELL_THRESHOLD = 1.0
        self.selection_start_time = 0
        self.hovered_option = None
        self.progress = 0.0
        
        # State intern: False = Meniu Principal, True = Selectie Joc
        self.in_game_selection_mode = False

        # Layout Meniu Principal
        self.main_buttons = {
            "INFO": (0.05, 0.3, 0.25, 0.4),  # Stanga
            "PLAY_MENU": (0.375, 0.3, 0.25, 0.4), # Centru (Il numim intern PLAY_MENU)
            "MAP":  (0.70, 0.3, 0.25, 0.4)   # Dreapta
        }
        
        # Layout Sub-meniu Selectie Joc
        self.game_buttons = {
            "IT QUIZ": (0.1,  0.3, 0.35, 0.4), # Stanga
            "COMING SOON": (0.55, 0.3, 0.35, 0.4)  # Dreapta
        }

    def update(self, cursor_x, cursor_y):
        """
        Returnează:
        - None: Nu s-a selectat nimic final.
        - "INFO", "MAP": Selecții directe.
        - "PLAY": Doar după ce s-a ales "IT QUIZ".
        """
        # Alegem setul de butoane in functie de modul curent
        if not self.in_game_selection_mode:
            active_buttons = self.main_buttons
        else:
            active_buttons = self.game_buttons

        current_hover = None
        
        # 1. Check collision
        for name, (bx, by, bw, bh) in active_buttons.items():
            if bx < cursor_x < bx + bw and by < cursor_y < by + bh:
                current_hover = name
                break
        
        # 2. Handle Hover Logic
        if current_hover == self.hovered_option and current_hover is not None:
            elapsed = time.time() - self.selection_start_time
            self.progress = min(elapsed / self.DWELL_THRESHOLD, 1.0)
            
            if self.progress >= 1.0:
                self.progress = 0.0
                self.hovered_option = None
                return self._confirm_selection(current_hover)
                
        elif current_hover != self.hovered_option:
            self.hovered_option = current_hover
            self.selection_start_time = time.time()
            self.progress = 0.0
            
        return None

    def _confirm_selection(self, selection):
        """Gestioneaza logica interna a meniului"""
        if not self.in_game_selection_mode:
            # Suntem in Meniul Principal
            if selection == "PLAY_MENU":
                self.in_game_selection_mode = True # Intram in sub-meniu
                return None # Nu trimitem inca nimic la main_app
            else:
                return selection # INFO sau MAP
        else:
            # Suntem in Sub-meniu Jocuri
            if selection == "IT QUIZ":
                return "PLAY" # Acum pornim jocul in main_app
            elif selection == "COMING SOON":
                return None # Nu face nimic
        return None

    def draw(self, frame):
        """Deseneaza meniul sau sub-meniul"""
        h, w, _ = frame.shape
        
        # Titlu
        cv2.putText(frame, "UNIVERSITY TOUCHLESS KIOSK", (50, 80), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)

        if not self.in_game_selection_mode:
            # --- DESENARE MENIU PRINCIPAL ---
            cv2.putText(frame, "Main Menu - Hover to Select", (50, 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 200, 200), 2)
            self._draw_buttons(frame, self.main_buttons)
        else:
            # --- DESENARE SELECTIE JOC ---
            cv2.putText(frame, "Select Game Mode", (50, 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 200, 200), 2)
            self._draw_buttons(frame, self.game_buttons)
            
            # Instructiune Back (Optional, vizual doar)
            cv2.putText(frame, "Reset to Main Menu automatically on timeout", (50, h-50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150,150,150), 1)

        return frame

    def _draw_buttons(self, frame, buttons):
        h, w, _ = frame.shape
        for name, (bx, by, bw, bh) in buttons.items():
            # Coordonate pixeli
            x1, y1 = int(bx * w), int(by * h)
            w_px, h_px = int(bw * w), int(bh * h)
            x2, y2 = x1 + w_px, y1 + h_px

            # Culori
            is_hovered = (self.hovered_option == name)
            if name == "COMING SOON":
                color = (30, 30, 30) # Gri inchis
                border_color = (50, 50, 50)
            elif is_hovered:
                color = (100, 100, 100)
                border_color = (0, 255, 255) # Galben
            else:
                color = (50, 50, 50)
                border_color = (200, 200, 200)

            # Desenare cutie transparenta (Manual, fara helper extern)
            overlay = frame.copy()
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
            
            # Border
            thick = 3 if is_hovered else 2
            cv2.rectangle(frame, (x1, y1), (x2, y2), border_color, thick)

            # Bara Progres
            if is_hovered and self.progress > 0:
                bar_w = int(w_px * self.progress)
                cv2.rectangle(frame, (x1, y2-10), (x1+bar_w, y2), (0, 255, 0), -1)

            # Text
            display_text = "PLAY" if name == "PLAY_MENU" else name
            font_scale = 1.0
            tsz = cv2.getTextSize(display_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)[0]
            tx = x1 + (w_px - tsz[0]) // 2
            ty = y1 + (h_px + tsz[1]) // 2
            cv2.putText(frame, display_text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 2)