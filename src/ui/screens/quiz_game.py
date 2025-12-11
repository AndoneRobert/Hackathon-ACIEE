import cv2
import time
import numpy as np
import math
import random

class QuizGame:
    def __init__(self):
        # --- CONFIGURARE JOC ---
        self.DWELL_THRESHOLD = 1.0  # Timp necesar pentru selectare
        self.FEEDBACK_DURATION = 2.0 # Cât timp afișăm rezultatul
        
        # --- STĂRI INTERNE ---
        self.STATE_PLAYING = "PLAYING"
        self.STATE_FEEDBACK = "FEEDBACK"
        self.STATE_GAMEOVER = "GAMEOVER"
        
        # Variabile cerute de main_app.py / game.py
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
        # Gradient Start (SUS): #081B2E -> BGR: (46, 27, 8)
        # Gradient End (JOS):   #174D83 -> BGR: (131, 77, 23)
        self.COLOR_ACIEE_DARK = (46, 27, 8)
        self.COLOR_ACIEE_LIGHT = (131, 77, 23)
        
        # Layout Răspunsuri
        self.options_layout = {
            "LEFT":  (0.1,  0.55, 0.35, 0.3), # x, y, w, h
            "RIGHT": (0.55, 0.55, 0.35, 0.3)
        }
        
        # --- ANIMATIE ---
        self.anim_offsets = {k: random.uniform(0, 6.28) for k in self.options_layout.keys()}

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
        """ Logica jocului (apelată DOAR cand e detectata mana) """
        if self.state == self.STATE_GAMEOVER:
            return

        # Daca suntem in feedback, nu mai procesam hover, dar verificam timpul
        # (Dublam verificarea si aici pentru cand mana e prezenta)
        if self.state == self.STATE_FEEDBACK:
            if time.time() - self.feedback_start_time > self.FEEDBACK_DURATION:
                self._next_question()
            return

        # Logica Hover
        hovered = None
        for key, (bx, by, bw, bh) in self.options_layout.items():
            if bx < cursor_x < bx + bw and by < cursor_y < by + bh:
                hovered = key
                break
        
        # Calcul Progres
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
        """Desenează un dreptunghi cu gradient VERTICAL"""
        gradient = np.zeros((h, w, 3), dtype=np.uint8)
        for i in range(h):
            alpha = i / h
            color = (
                int(color_start[0] * (1 - alpha) + color_end[0] * alpha),
                int(color_start[1] * (1 - alpha) + color_end[1] * alpha),
                int(color_start[2] * (1 - alpha) + color_end[2] * alpha)
            )
            gradient[i, :] = color
        
        # Verificare limite frame
        if y+h > frame.shape[0] or x+w > frame.shape[1]: return frame

        frame[y:y+h, x:x+w] = gradient
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 255), 1)
        return frame

    def draw(self, frame):
        h, w, _ = frame.shape
        current_time = time.time()

        # --- FIX: VERIFICARE TIMEOUT FEEDBACK AICI ---
        # Deoarece main_app nu apeleaza update() cand mana nu e prezenta,
        # verificam timpul si aici (draw se apeleaza mereu).
        if self.state == self.STATE_FEEDBACK:
            if time.time() - self.feedback_start_time > self.FEEDBACK_DURATION:
                self._next_question()

        # --- ECRAN GAME OVER ---
        if self.state == self.STATE_GAMEOVER:
            self._draw_gradient_rect(frame, w//2 - 300, h//2 - 200, 600, 400, self.COLOR_ACIEE_DARK, self.COLOR_ACIEE_LIGHT)
            cv2.putText(frame, "QUIZ COMPLETE", (w//2 - 180, h//2 - 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
            cv2.putText(frame, f"SCORE: {self.score}/{len(self.questions)}", (w//2 - 120, h//2 + 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 2)
            msg = "Bravo!" if (self.score / len(self.questions)) > 0.5 else "Mai incearca!"
            cv2.putText(frame, msg, (w//2 - 100, h//2 + 130), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 200, 200), 2)
            return frame

        # --- JOC ACTIV ---
        q = self.questions[self.current_q_index]

        # 1. HEADER
        header_w = int(w * 0.9)
        header_h = 140
        header_x = (w - header_w) // 2
        header_y = 60
        
        self._draw_gradient_rect(frame, header_x, header_y, header_w, header_h, self.COLOR_ACIEE_DARK, self.COLOR_ACIEE_LIGHT)
        
        # Text Întrebare
        font_scale = 1.3
        thick = 2
        text_size = cv2.getTextSize(q['text'], cv2.FONT_HERSHEY_SIMPLEX, font_scale, thick)[0]
        text_x = header_x + (header_w - text_size[0]) // 2
        text_y = header_y + (header_h + text_size[1]) // 2
        
        cv2.putText(frame, q['text'], (text_x+2, text_y+2), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thick)
        cv2.putText(frame, q['text'], (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thick)
        
        cv2.putText(frame, f"Score: {self.score}", (header_x + header_w - 180, header_y + header_h - 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 1)

        # 2. BUTOANE
        for key, text in q["options"].items():
            bx, by, bw, bh = self.options_layout[key]
            
            # Animatie Plutire
            float_offset = math.sin(current_time * 2.5 + self.anim_offsets[key]) * 8
            
            x1 = int(bx * w)
            y1 = int(by * h + float_offset)
            w_px = int(bw * w)
            h_px = int(bh * h)
            x2 = x1 + w_px
            y2 = y1 + h_px
            
            # Stilizare
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

            # Desenare
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