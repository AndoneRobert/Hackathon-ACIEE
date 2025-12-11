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
        
        # --- CULORI ACIEE (BGR) ---
        # Dark Blue (#081B2E) -> (46, 27, 8)
        # Light Blue (#174D83) -> (131, 77, 23)
        self.COLOR_ACIEE_DARK = (46, 27, 8)
        self.COLOR_ACIEE_LIGHT = (131, 77, 23)
        
        # Layout Răspunsuri (Joc) - Butoanele la 60% inaltime
        self.options_layout = {
            "LEFT":  (0.1,  0.6, 0.35, 0.3), 
            "RIGHT": (0.55, 0.6, 0.35, 0.3)
        }

        # --- LAYOUT GAME OVER ---
        self.game_over_layout = {
            "RETRY": (0.1, 0.75, 0.35, 0.15),
            "EXIT":  (0.55, 0.75, 0.35, 0.15)
        }
        
        self.anim_offsets = {k: random.uniform(0, 6.28) for k in list(self.options_layout.keys()) + list(self.game_over_layout.keys())}

    def reset(self):
        self.current_q_index = 0
        self.score = 0
        self.state = self.STATE_PLAYING
        self.game_over = False
        self.current_selection = None
        self.progress = 0.0

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
        # --- GAME OVER ---
        if self.state == self.STATE_GAMEOVER:
            hovered = None
            for key, (bx, by, bw, bh) in self.game_over_layout.items():
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
                        return "RETRY"
                    elif hovered == "EXIT":
                        return "EXIT_TO_APP"
            else:
                self.current_selection = hovered
                self.selection_start_time = time.time()
                self.progress = 0.0
            
            return None

        # --- JOC ACTIV ---
        if self.state == self.STATE_FEEDBACK:
            if time.time() - self.feedback_start_time > self.FEEDBACK_DURATION:
                self._next_question()
            return None

        hovered = None
        for key, (bx, by, bw, bh) in self.options_layout.items():
            if bx < cursor_x < bx + bw and by < cursor_y < by + bh:
                hovered = key
                break
        
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
        """Desenează un dreptunghi cu gradient VERTICAL"""
        # Creăm un canvas mic doar pentru dreptunghi
        gradient = np.zeros((h, w, 3), dtype=np.uint8)
        
        # Generăm gradientul (interpolare liniară) pe înălțime
        for i in range(h):
            alpha = i / h
            # Interpolăm între culori
            color = (
                int(color_start[0] * (1 - alpha) + color_end[0] * alpha),
                int(color_start[1] * (1 - alpha) + color_end[1] * alpha),
                int(color_start[2] * (1 - alpha) + color_end[2] * alpha)
            )
            gradient[i, :] = color
            
        # Verificăm limitele pentru a nu crăpa la resize
        if y+h > frame.shape[0] or x+w > frame.shape[1]: 
            return frame

        # Copiem gradientul
        frame[y:y+h, x:x+w] = gradient
        
        # Adăugăm un contur fin alb
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 255), 1)
        return frame

    def _draw_modern_button(self, frame, key, text, layout_dict, current_time, is_answer_button=False):
        """
        Desenează un buton modern cu Gradient, Glow și Feedback vizual.
        """
        bx, by, bw, bh = layout_dict[key]
        h, w, _ = frame.shape
        
        # --- 1. ANIMATIE (Plutire) ---
        float_offset = math.sin(current_time * 2.5 + self.anim_offsets.get(key, 0)) * 5
        
        x1 = int(bx * w)
        y1 = int(by * h + float_offset)
        w_px = int(bw * w)
        h_px = int(bh * h)
        x2 = x1 + w_px
        y2 = y1 + h_px
        
        is_hovered = (key == self.current_selection)
        
        # --- 2. LOGICA CULORI & GRADIENT ---
        
        # Culori implicite (Gradient ACIEE)
        color_top = self.COLOR_ACIEE_DARK
        color_bottom = self.COLOR_ACIEE_LIGHT
        border_color = (200, 200, 200) # Gri deschis
        text_color = (255, 255, 255)
        
        # Override pentru Feedback (Verde/Roșu)
        is_feedback_state = False
        
        if is_answer_button and self.state == self.STATE_FEEDBACK:
            q = self.questions[self.current_q_index]
            is_feedback_state = True
            
            if key == q["correct"]:
                # Gradient Verde
                color_top = (0, 100, 0)
                color_bottom = (0, 200, 0)
                border_color = (0, 255, 0) # Neon Green
            elif key == self.last_choice and not self.is_correct:
                # Gradient Roșu
                color_top = (0, 0, 100)
                color_bottom = (0, 0, 200)
                border_color = (0, 0, 255) # Neon Red
            else:
                # Butoanele neimplicate devin gri șters
                color_top = (30, 30, 30)
                color_bottom = (50, 50, 50)
                border_color = (100, 100, 100)
                text_color = (150, 150, 150)
        
        # Override pentru Hover (Luminăm butonul)
        elif is_hovered:
            # Facem culorile mai deschise la hover
            color_top = (min(255, self.COLOR_ACIEE_DARK[0] + 40), 
                         min(255, self.COLOR_ACIEE_DARK[1] + 40), 
                         min(255, self.COLOR_ACIEE_DARK[2] + 40))
            color_bottom = (min(255, self.COLOR_ACIEE_LIGHT[0] + 40), 
                            min(255, self.COLOR_ACIEE_LIGHT[1] + 40), 
                            min(255, self.COLOR_ACIEE_LIGHT[2] + 40))
            border_color = (0, 255, 255) # Cyan Glow

        # --- 3. DESENARE EFECTIVA ---

        # A. Glow Exterior (doar la hover sau răspuns corect)
        if (is_hovered and not is_feedback_state) or (is_feedback_state and border_color == (0, 255, 0)):
            cv2.rectangle(frame, (x1-3, y1-3), (x2+3, y2+3), border_color, -1) # Glow solid in spate

        # B. Fundal Gradient (Desenăm manual gradientul pe un ROI)
        # Atenție la limitele ecranului
        roi_h = y2 - y1
        roi_w = x2 - x1
        
        if roi_h > 0 and roi_w > 0:
            # Creăm gradientul local
            btn_gradient = np.zeros((roi_h, roi_w, 3), dtype=np.uint8)
            for i in range(roi_h):
                alpha = i / roi_h
                c = (
                    int(color_top[0] * (1 - alpha) + color_bottom[0] * alpha),
                    int(color_top[1] * (1 - alpha) + color_bottom[1] * alpha),
                    int(color_top[2] * (1 - alpha) + color_bottom[2] * alpha)
                )
                btn_gradient[i, :] = c
            
            # Aplicăm gradientul pe frame (cu alpha blending opțional dacă vrei transparență)
            # Aici îl punem solid pentru claritate
            frame[y1:y2, x1:x2] = btn_gradient

        # C. Border
        thick = 3 if (is_hovered or is_feedback_state) else 1
        cv2.rectangle(frame, (x1, y1), (x2, y2), border_color, thick)
        
        # D. Bara de Progres (Hover)
        if is_hovered and self.progress > 0 and not is_feedback_state:
            bar_w = int(w_px * self.progress)
            cv2.rectangle(frame, (x1, y2-8), (x1+bar_w, y2), (0, 255, 0), -1)
            
        # E. Text (Centrat)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_s = 0.8
        
        # Ajustăm mărimea fontului pentru texte lungi
        if len(text) > 25: font_s = 0.6
        elif len(text) > 15: font_s = 0.7
        
        t_size = cv2.getTextSize(text, font, font_s, 2)[0]
        t_x = x1 + (w_px - t_size[0]) // 2
        t_y = y1 + (h_px + t_size[1]) // 2
        
        # Umbră text pentru contrast
        cv2.putText(frame, text, (t_x+1, t_y+1), font, font_s, (0,0,0), 2)
        cv2.putText(frame, text, (t_x, t_y), font, font_s, text_color, 2)

    def draw(self, frame):
        h, w, _ = frame.shape
        current_time = time.time()

        if self.state == self.STATE_FEEDBACK:
            if time.time() - self.feedback_start_time > self.FEEDBACK_DURATION:
                self._next_question()

        # --- ECRAN GAME OVER ---
        if self.state == self.STATE_GAMEOVER:
            panel_w = 700 
            panel_h = 350
            panel_x = w // 2 - panel_w // 2
            panel_y = 80
            
            # Folosim helper-ul pentru gradientul panoului principal
            self._draw_gradient_rect(frame, panel_x, panel_y, panel_w, panel_h, self.COLOR_ACIEE_DARK, self.COLOR_ACIEE_LIGHT)
            
            cv2.putText(frame, "REZULTAT FINAL", (w//2 - 130, panel_y + 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
            
            score_text = f"{self.score} / {len(self.questions)}"
            ts = cv2.getTextSize(score_text, cv2.FONT_HERSHEY_SIMPLEX, 2.5, 5)[0]
            cv2.putText(frame, score_text, (w//2 - ts[0]//2, panel_y + 140), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2.5, (0, 255, 255), 5)
            
            ratio = self.score / len(self.questions)
            msg_line1 = "Excelent! Esti nascut pentru inginerie!" if ratio >= 0.8 else "Bravo! Ai potential mare." if ratio >= 0.5 else "Nu te descuraja! Aici invatam impreuna."
            msg_line2 = "Te asteptam la facultatea ACIEE!" if ratio >= 0.8 else "Hai la ACIEE sa devii expert!" if ratio >= 0.5 else "Vino la ACIEE sa descoperi viitorul!"
            
            ts1 = cv2.getTextSize(msg_line1, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
            cv2.putText(frame, msg_line1, (w//2 - ts1[0]//2, panel_y + 220), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (220, 220, 220), 2)
            
            ts2 = cv2.getTextSize(msg_line2, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
            cv2.putText(frame, msg_line2, (w//2 - ts2[0]//2, panel_y + 270), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)
            
            self._draw_modern_button(frame, "RETRY", "REINCEARCA", self.game_over_layout, current_time)
            self._draw_modern_button(frame, "EXIT", "INAPOI LA MENIUL PRINCIPAL", self.game_over_layout, current_time)
            
            return frame

        # --- JOC ACTIV ---
        q = self.questions[self.current_q_index]

        # 1. HEADER INTREBARE
        header_w = int(w * 0.9)
        header_h = 140
        header_x = (w - header_w) // 2
        header_y = int(h * 0.25)
        
        self._draw_gradient_rect(frame, header_x, header_y, header_w, header_h, self.COLOR_ACIEE_DARK, self.COLOR_ACIEE_LIGHT)
        
        # 2. CONTOR INTREBARI
        q_count_text = f"Intrebarea {self.current_q_index + 1} / {len(self.questions)}"
        ts_q = cv2.getTextSize(q_count_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        
        panel_q_w = ts_q[0] + 40
        panel_q_h = 40
        panel_q_x = 30
        panel_q_y = 30
        
        overlay = frame.copy()
        cv2.rectangle(overlay, (panel_q_x, panel_q_y), (panel_q_x + panel_q_w, panel_q_y + panel_q_h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        cv2.rectangle(frame, (panel_q_x, panel_q_y), (panel_q_x + panel_q_w, panel_q_y + panel_q_h), (200, 200, 200), 1)
        
        cv2.putText(frame, q_count_text, (panel_q_x + 20, panel_q_y + 28), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Scor
        cv2.putText(frame, f"Scor: {self.score}", (header_x + header_w - 150, header_y + header_h - 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 1)

        # Text Intrebare
        font_scale = 1.3
        thick = 2
        text_size = cv2.getTextSize(q['text'], cv2.FONT_HERSHEY_SIMPLEX, font_scale, thick)[0]
        text_x = header_x + (header_w - text_size[0]) // 2
        text_y = header_y + (header_h + text_size[1]) // 2
        
        cv2.putText(frame, q['text'], (text_x+2, text_y+2), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thick)
        cv2.putText(frame, q['text'], (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thick)

        # 3. BUTOANE RASPUNS (Design Nou)
        for key, text in q["options"].items():
            self._draw_modern_button(frame, key, text, self.options_layout, current_time, is_answer_button=True)

        return frame