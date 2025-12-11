import cv2
import time
import numpy as np
import math
import random

class QuizGame:
    def __init__(self):
        # --- CONFIGURARE JOC ---
        self.DWELL_THRESHOLD = 1.0  
        self.FEEDBACK_DURATION = 2.0 
        
        self.STATE_PLAYING = "PLAYING"
        self.STATE_FEEDBACK = "FEEDBACK"
        self.STATE_GAMEOVER = "GAMEOVER"
        
        self.game_over = False 
        self.state = self.STATE_PLAYING
        
        # Datele Quiz-ului
        self.questions = self._load_questions()
        self.current_q_index = 0
        self.score = 0
        
        # --- INTERACȚIUNE ---
        self.current_selection = None
        self.selection_start_time = 0
        self.progress = 0.0
        
        self.feedback_start_time = 0
        self.last_choice = None
        self.is_correct = False
        
        # --- DESIGN & CULORI (ACIEE STYLE) ---
        self.COLOR_ACIEE_DARK = (46, 27, 8)
        self.COLOR_ACIEE_LIGHT = (131, 77, 23)
        
        # Layout Răspunsuri (Joc)
        self.options_layout = {
            "LEFT":  (0.1,  0.55, 0.35, 0.3), 
            "RIGHT": (0.55, 0.55, 0.35, 0.3)
        }

        # Layout Butoane Game Over (Sub scor)
        self.game_over_buttons = {
            "RETRY": (0.15, 0.7, 0.3, 0.15),  # Stanga: Reincearca
            "EXIT":  (0.55, 0.7, 0.3, 0.15)   # Dreapta: Meniu
        }
        
        # --- ANIMATIE ---
        self.anim_offsets = {k: random.uniform(0, 6.28) for k in list(self.options_layout.keys()) + list(self.game_over_buttons.keys())}

    def reset(self):
        """Resetează jocul pentru a începe din nou."""
        self.current_q_index = 0
        self.score = 0
        self.state = self.STATE_PLAYING
        self.game_over = False
        self.current_selection = None
        self.progress = 0.0
        # Optional: Amestecă întrebările
        # random.shuffle(self.questions)

    def _load_questions(self):
        return [
            {"text": "Ce reprezinta CPU?", "options": {"LEFT": "Central Processing Unit", "RIGHT": "Central Power Unit"}, "correct": "LEFT"},
            {"text": "Care memorie este volatila?", "options": {"LEFT": "HDD (Hard Disk)", "RIGHT": "RAM (Random Access)"}, "correct": "RIGHT"},
            {"text": "Limbajul binar foloseste doar:", "options": {"LEFT": "0 si 1", "RIGHT": "1 si 2"}, "correct": "LEFT"},
            {"text": "HTML este limbaj de programare?", "options": {"LEFT": "DA", "RIGHT": "NU (Markup)"}, "correct": "RIGHT"},
            {"text": "Ce este un algoritm?", "options": {"LEFT": "Componenta Hardware", "RIGHT": "Pasi Logici"}, "correct": "RIGHT"},
            {"text": "Cum afisezi in Python?", "options": {"LEFT": "print()", "RIGHT": "echo()"}, "correct": "LEFT"}
        ]

    def update(self, cursor_x, cursor_y):
        """ 
        Returnează 'EXIT' dacă utilizatorul alege să iasă la meniu.
        Altfel returnează None.
        """
        
        # --- LOGICA GAME OVER (Butoane Finale) ---
        if self.state == self.STATE_GAMEOVER:
            hovered = None
            for key, (bx, by, bw, bh) in self.game_over_buttons.items():
                if bx < cursor_x < bx + bw and by < cursor_y < by + bh:
                    hovered = key
                    break
            
            if hovered and hovered == self.current_selection:
                elapsed = time.time() - self.selection_start_time
                self.progress = min(elapsed / self.DWELL_THRESHOLD, 1.0)
                
                if self.progress >= 1.0:
                    self.progress = 0.0
                    self.current_selection = None
                    
                    if hovered == "RETRY":
                        self.reset()
                    elif hovered == "EXIT":
                        return "EXIT"
            else:
                self.current_selection = hovered
                self.selection_start_time = time.time()
                self.progress = 0.0
            
            return None

        # --- LOGICA JOC ACTIV ---
        
        # 1. Pauză Feedback
        if self.state == self.STATE_FEEDBACK:
            if time.time() - self.feedback_start_time > self.FEEDBACK_DURATION:
                self._next_question()
            return None

        # 2. Logica Hover Răspunsuri
        hovered = None
        for key, (bx, by, bw, bh) in self.options_layout.items():
            if bx < cursor_x < bx + bw and by < cursor_y < by + bh:
                hovered = key
                break
        
        # 3. Calcul Progres
        if hovered and hovered == self.current_selection:
            elapsed = time.time() - self.selection_start_time
            self.progress = min(elapsed / self.DWELL_THRESHOLD, 1.0)
            if self.progress >= 1.0:
                self._submit_answer(hovered)
                self.progress = 0.0
                self.current_selection = None
        else:
            self.current_selection = hovered
            self.selection_start_time = time.time()
            self.progress = 0.0
            
        return None

    def _submit_answer(self, choice):
        q = self.questions[self.current_q_index]
        self.last_choice = choice
        self.is_correct = (choice == q["correct"])
        if self.is_correct:
            self.score += 1
        self.state = self.STATE_FEEDBACK
        self.feedback_start_time = time.time()

    def _next_question(self):
        self.current_q_index += 1
        if self.current_q_index >= len(self.questions):
            self.state = self.STATE_GAMEOVER
            self.game_over = True
        else:
            self.state = self.STATE_PLAYING

    def _draw_gradient_rect(self, frame, x, y, w, h, color_start, color_end):
        gradient = np.zeros((h, w, 3), dtype=np.uint8)
        for i in range(h):
            alpha = i / h
            color = (
                int(color_start[0] * (1 - alpha) + color_end[0] * alpha),
                int(color_start[1] * (1 - alpha) + color_end[1] * alpha),
                int(color_start[2] * (1 - alpha) + color_end[2] * alpha)
            )
            gradient[i, :] = color
        
        if y+h > frame.shape[0] or x+w > frame.shape[1]: return frame
        frame[y:y+h, x:x+w] = gradient
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 255), 1)
        return frame

    def _draw_button(self, frame, key, text, layout_dict, current_time):
        """Helper pentru desenarea unui buton standard"""
        bx, by, bw, bh = layout_dict[key]
        h, w, _ = frame.shape
        
        # Animatie Plutire
        float_offset = math.sin(current_time * 2.5 + self.anim_offsets.get(key, 0)) * 5
        
        x1 = int(bx * w)
        y1 = int(by * h + float_offset)
        w_px = int(bw * w)
        h_px = int(bh * h)
        x2 = x1 + w_px
        y2 = y1 + h_px
        
        is_hovered = (key == self.current_selection)
        
        # Culori
        bg_color = (30, 30, 30)
        border_color = (150, 150, 150)
        text_color = (200, 200, 200)
        
        if is_hovered:
            bg_color = (60, 60, 60)
            border_color = (0, 255, 255) # Cyan
            text_color = (255, 255, 255)
            
        # Desenare
        overlay = frame.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), bg_color, -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
        cv2.rectangle(frame, (x1, y1), (x2, y2), border_color, 2 if not is_hovered else 3)
        
        # Progres
        if is_hovered and self.progress > 0:
            bar_w = int(w_px * self.progress)
            cv2.rectangle(frame, (x1, y2-8), (x1+bar_w, y2), (0, 255, 0), -1)
            
        # Text
        font_s = 0.9
        t_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_s, 2)[0]
        t_x = x1 + (w_px - t_size[0]) // 2
        t_y = y1 + (h_px + t_size[1]) // 2
        cv2.putText(frame, text, (t_x, t_y), cv2.FONT_HERSHEY_SIMPLEX, font_s, text_color, 2)

    def draw(self, frame):
        h, w, _ = frame.shape
        current_time = time.time()

        # --- FIX: VERIFICARE TIMEOUT FEEDBACK ---
        if self.state == self.STATE_FEEDBACK:
            if time.time() - self.feedback_start_time > self.FEEDBACK_DURATION:
                self._next_question()

        # --- ECRAN GAME OVER ---
        if self.state == self.STATE_GAMEOVER:
            # Fundal Gradient
            self._draw_gradient_rect(frame, w//2 - 300, h//2 - 250, 600, 500, self.COLOR_ACIEE_DARK, self.COLOR_ACIEE_LIGHT)
            
            # Titlu si Scor
            cv2.putText(frame, "QUIZ COMPLETE", (w//2 - 180, h//2 - 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
            cv2.putText(frame, f"SCOR FINAL: {self.score}/{len(self.questions)}", (w//2 - 200, h//2 - 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)
            
            # Butoane Actiune
            self._draw_button(frame, "RETRY", "REINCEARCA", self.game_over_buttons, current_time)
            self._draw_button(frame, "EXIT", "MENIU PRINCIPAL", self.game_over_buttons, current_time)
            
            return frame

        # --- JOC ACTIV ---
        q = self.questions[self.current_q_index]

        # 1. HEADER
        header_w = int(w * 0.9)
        header_h = 140
        header_x = (w - header_w) // 2
        header_y = 60
        self._draw_gradient_rect(frame, header_x, header_y, header_w, header_h, self.COLOR_ACIEE_DARK, self.COLOR_ACIEE_LIGHT)
        
        font_scale = 1.3
        thick = 2
        text_size = cv2.getTextSize(q['text'], cv2.FONT_HERSHEY_SIMPLEX, font_scale, thick)[0]
        text_x = header_x + (header_w - text_size[0]) // 2
        text_y = header_y + (header_h + text_size[1]) // 2
        
        cv2.putText(frame, q['text'], (text_x+2, text_y+2), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thick)
        cv2.putText(frame, q['text'], (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thick)
        
        cv2.putText(frame, f"Score: {self.score}", (header_x + header_w - 180, header_y + header_h - 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 1)

        # 2. BUTOANE RĂSPUNS
        for key, text in q["options"].items():
            bx, by, bw, bh = self.options_layout[key]
            
            float_offset = math.sin(current_time * 2.5 + self.anim_offsets[key]) * 8
            x1, y1 = int(bx * w), int(by * h + float_offset)
            w_px, h_px = int(bw * w), int(bh * h)
            x2, y2 = x1 + w_px, y1 + h_px
            
            is_hovered = (key == self.current_selection)
            bg_color = (20, 20, 20) 
            border_color = (100, 100, 100)
            text_color = (200, 200, 200)
            
            if self.state == self.STATE_FEEDBACK:
                if key == q["correct"]:
                    bg_color = (0, 100, 0)
                    border_color = (0, 255, 0)
                    text_color = (255, 255, 255)
                elif key == self.last_choice and not self.is_correct:
                    bg_color = (0, 0, 100)
                    border_color = (0, 0, 255)
            elif is_hovered:
                bg_color = (60, 60, 60)
                border_color = (255, 255, 0)
                text_color = (255, 255, 255)

            overlay = frame.copy()
            cv2.rectangle(overlay, (x1, y1), (x2, y2), bg_color, -1)
            cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
            cv2.rectangle(frame, (x1, y1), (x2, y2), border_color, 3 if is_hovered else 2)
            
            if is_hovered and self.state == self.STATE_PLAYING and self.progress > 0:
                bar_w = int(w_px * self.progress)
                cv2.rectangle(frame, (x1, y2-8), (x1+bar_w, y2), (0, 255, 0), -1)

            font_s = 1.1
            t_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_s, 2)[0]
            t_x = x1 + (w_px - t_size[0]) // 2
            t_y = y1 + (h_px + t_size[1]) // 2
            
            cv2.putText(frame, text, (t_x, t_y), cv2.FONT_HERSHEY_SIMPLEX, font_s, text_color, 2)

        return frame