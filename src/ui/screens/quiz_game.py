import cv2
import time
import numpy as np
import math
import random
import threading
from src.core.ai_generator import AIGenerator

class QuizGame:
    def __init__(self):
        # --- CONFIGURARE JOC ---
        self.DWELL_THRESHOLD = 1.0  
        self.FEEDBACK_DURATION = 2.0 
        
        # --- STĂRI INTERNE ---
        self.STATE_LOADING = "LOADING" 
        self.STATE_PLAYING = "PLAYING"
        self.STATE_FEEDBACK = "FEEDBACK"
        self.STATE_GAMEOVER = "GAMEOVER"
        
        self.game_over = False 
        
        print("QuizGame: Initializare generator AI...")
        self.ai_generator = AIGenerator()
        
        self.questions = []
        self.current_q_index = 0
        self.score = 0
        
        # --- INTERACȚIUNE ---
        self.current_selection = None
        self.selection_start_time = 0
        self.progress = 0.0
        
        self.feedback_start_time = 0
        self.last_choice = None
        self.is_correct = False
        
        # --- CULORI ACIEE ---
        self.COLOR_ACIEE_DARK = (46, 27, 8)
        self.COLOR_ACIEE_LIGHT = (131, 77, 23)
        
        # Layout Răspunsuri
        self.options_layout = {
            "LEFT":  (0.1,  0.6, 0.35, 0.3), 
            "RIGHT": (0.55, 0.6, 0.35, 0.3)
        }

        # Layout Game Over
        self.game_over_layout = {
            "RETRY": (0.1, 0.75, 0.35, 0.15),
            "EXIT":  (0.55, 0.75, 0.35, 0.15)
        }
        
        self.anim_offsets = {k: random.uniform(0, 6.28) for k in list(self.options_layout.keys()) + list(self.game_over_layout.keys())}

        self.start_loading_questions()

    def start_loading_questions(self):
        self.state = self.STATE_LOADING
        self.questions = [] 
        
        def worker():
            print("QuizGame [Thread]: Cerem intrebari de la Gemini...")
            try:
                new_questions = self.ai_generator.generate_quiz()
                if new_questions and len(new_questions) > 0:
                    self.questions = new_questions
                else:
                    self.questions = self._get_hardcoded_fallback()
            except Exception as e:
                print(f"QuizGame [Thread] EROARE: {e}")
                self.questions = self._get_hardcoded_fallback()
            
            self.current_q_index = 0
            self.score = 0
            self.state = self.STATE_PLAYING

        thread = threading.Thread(target=worker)
        thread.daemon = True 
        thread.start()

    def _get_hardcoded_fallback(self):
        return [
            {"text": "Ce reprezinta CPU?", "options": {"LEFT": "Procesor", "RIGHT": "Placa Video"}, "correct": "LEFT"},
            {"text": "Memoria volatila este:", "options": {"LEFT": "HDD", "RIGHT": "RAM"}, "correct": "RIGHT"},
            {"text": "HTML este limbaj de programare?", "options": {"LEFT": "DA", "RIGHT": "NU"}, "correct": "RIGHT"},
            {"text": "Binar inseamna:", "options": {"LEFT": "0 si 1", "RIGHT": "1 si 2"}, "correct": "LEFT"},
            {"text": "Python este:", "options": {"LEFT": "Interpretat", "RIGHT": "Compilat"}, "correct": "LEFT"},
            {"text": "Tasta Copy este:", "options": {"LEFT": "Ctrl+C", "RIGHT": "Ctrl+V"}, "correct": "LEFT"}
        ]

    def _clean_text(self, text):
        """Elimina diacriticele si curata ghilimelele."""
        replacements = {
            'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ț': 't',
            'Ă': 'A', 'Â': 'A', 'Î': 'I', 'Ș': 'S', 'Ț': 'T',
            'ş': 's', 'ţ': 't', 'Ş': 'S', 'Ţ': 'T',
            # Ghilimele si simboluri
            '„': '"', '”': '"', '“': '"', '’': "'", '‘': "'", '–': '-', '—': '-'
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        return text

    def _draw_centered_text_wrapped(self, frame, text, center_x, center_y, max_w, max_h, color, thickness=2, font_face=cv2.FONT_HERSHEY_SIMPLEX):
        """
        Scrie text pe mai multe linii, centrat, micsorand fontul daca e nevoie.
        """
        words = text.split(' ')
        best_scale = 1.5 # Pornim de la un font mare
        min_scale = 0.5
        
        final_lines = []
        final_scale = best_scale
        
        # Iteram sa gasim marimea potrivita (de la mare la mic)
        for scale in np.arange(best_scale, min_scale - 0.1, -0.1):
            scale = round(scale, 1)
            
            # Verificam inaltimea liniei
            (w_space, h_line), baseline = cv2.getTextSize("Tg", font_face, scale, thickness)
            line_height = h_line + baseline + 10 # Spatiu intre linii
            
            lines = []
            current_line = ""
            
            valid_fit = True
            
            for word in words:
                # Testam cuvantul pe linia curenta
                test_line = current_line + (" " if current_line else "") + word
                (w_text, h_text), _ = cv2.getTextSize(test_line, font_face, scale, thickness)
                
                if w_text <= max_w:
                    current_line = test_line
                else:
                    # Cuvantul nu incape, trecem pe linie noua
                    if current_line: # Salvam linia veche
                        lines.append(current_line)
                    
                    # Testam daca cuvantul singur incape pe o linie (caz extrem)
                    (w_word, _), _ = cv2.getTextSize(word, font_face, scale, thickness)
                    if w_word > max_w:
                        valid_fit = False # Nici macar un cuvant nu incape
                        break
                        
                    current_line = word
            
            if current_line:
                lines.append(current_line)
                
            if not valid_fit:
                continue # Incercam font mai mic
            
            # Verificam inaltimea totala
            total_h = len(lines) * line_height
            if total_h <= max_h:
                final_lines = lines
                final_scale = scale
                break # Am gasit cea mai mare marime care incape!
        
        # Daca nu am gasit nimic (textul e prea lung chiar si pt font minim), fortam pe minim
        if not final_lines:
            final_lines = [text] # Va iesi din ecran, dar macar e ceva
            final_scale = min_scale

        # Desenare efectiva
        (w_dummy, h_line), baseline = cv2.getTextSize("Tg", font_face, final_scale, thickness)
        line_height = h_line + baseline + 10
        total_block_h = len(final_lines) * line_height
        
        start_y = center_y - (total_block_h // 2) + h_line # Ajustare pentru baseline
        
        for i, line in enumerate(final_lines):
            (lw, lh), _ = cv2.getTextSize(line, font_face, final_scale, thickness)
            lx = center_x - (lw // 2)
            ly = start_y + (i * line_height)
            
            # Umbra pentru contrast
            cv2.putText(frame, line, (lx+2, ly+2), font_face, final_scale, (0,0,0), thickness)
            # Textul
            cv2.putText(frame, line, (lx, ly), font_face, final_scale, color, thickness)

    def reset(self):
        self.game_over = False
        self.current_selection = None
        self.progress = 0.0
        self.start_loading_questions()

    def update(self, cursor_x, cursor_y):
        if self.state == self.STATE_LOADING:
            return None

        if self.state == self.STATE_GAMEOVER:
            self._handle_interaction(cursor_x, cursor_y, self.game_over_layout, is_game=False)
            return None

        if self.state == self.STATE_FEEDBACK:
            if time.time() - self.feedback_start_time > self.FEEDBACK_DURATION:
                self._next_question()
            return None

        if not self.questions:
            return None

        self._handle_interaction(cursor_x, cursor_y, self.options_layout, is_game=True)
        return None

    def _handle_interaction(self, cx, cy, layout, is_game):
        hovered = None
        for key, (bx, by, bw, bh) in layout.items():
            if bx < cx < bx + bw and by < cy < by + bh:
                hovered = key
                break
        
        if hovered and hovered == self.current_selection:
            elapsed = time.time() - self.selection_start_time
            self.progress = min(elapsed / self.DWELL_THRESHOLD, 1.0)
            
            if self.progress >= 1.0:
                self.progress = 0.0
                self.current_selection = None
                
                if is_game:
                    self._submit_answer(hovered)
                else:
                    if hovered == "RETRY":
                        self.reset()
                    elif hovered == "EXIT":
                        pass # Wrapper handles return via update
        else:
            self.current_selection = hovered
            self.selection_start_time = time.time()
            self.progress = 0.0

    # Override update pt Wrapper
    def update(self, cursor_x, cursor_y):
        if self.state == self.STATE_LOADING: return None

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
                    if hovered == "RETRY": self.reset()
                    elif hovered == "EXIT": return "EXIT_TO_APP"
            else:
                self.current_selection = hovered
                self.selection_start_time = time.time()
                self.progress = 0.0
            return None

        if self.state == self.STATE_FEEDBACK:
            if time.time() - self.feedback_start_time > self.FEEDBACK_DURATION:
                self._next_question()
            return None

        if not self.questions: return None

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
        if self.current_q_index >= len(self.questions): return
        q = self.questions[self.current_q_index]
        self.last_choice = choice
        self.is_correct = (choice == q["correct"])
        if self.is_correct: self.score += 1
        self.state = self.STATE_FEEDBACK
        self.feedback_start_time = time.time()

    def _next_question(self):
        self.current_q_index += 1
        if self.current_q_index >= len(self.questions):
            self.state = self.STATE_GAMEOVER
        else:
            self.state = self.STATE_PLAYING

    def _draw_gradient_rect(self, frame, x, y, w, h, c1, c2):
        if w <= 0 or h <= 0: return frame
        gradient = np.zeros((h, w, 3), dtype=np.uint8)
        for i in range(h):
            alpha = i / h
            color = (
                int(c1[0]*(1-alpha) + c2[0]*alpha),
                int(c1[1]*(1-alpha) + c2[1]*alpha),
                int(c1[2]*(1-alpha) + c2[2]*alpha)
            )
            gradient[i, :] = color
        
        if y+h > frame.shape[0] or x+w > frame.shape[1]: return frame
        frame[y:y+h, x:x+w] = gradient
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 255), 1)
        return frame

    def _draw_modern_button(self, frame, key, text, layout_dict, current_time, is_answer=False):
        # 1. Curatam textul (diacritice + ghilimele)
        text = self._clean_text(text)
        
        bx, by, bw, bh = layout_dict[key]
        h, w, _ = frame.shape
        
        float_off = math.sin(current_time * 3 + self.anim_offsets.get(key,0)) * 5
        x1 = int(bx*w)
        y1 = int(by*h + float_off)
        w_px = int(bw*w)
        h_px = int(bh*h)
        x2 = x1 + w_px
        y2 = y1 + h_px
        
        is_hover = (key == self.current_selection)
        
        c_top, c_bot = self.COLOR_ACIEE_DARK, self.COLOR_ACIEE_LIGHT
        border = (200,200,200)
        
        if is_answer and self.state == self.STATE_FEEDBACK:
            q = self.questions[self.current_q_index]
            if key == q["correct"]: c_top, c_bot, border = (0,100,0), (0,200,0), (0,255,0)
            elif key == self.last_choice and not self.is_correct: c_top, c_bot, border = (0,0,100), (0,0,200), (0,0,255)
            else: c_top, c_bot, border = (30,30,30), (50,50,50), (100,100,100)
        elif is_hover:
            c_top = tuple(min(255, c+40) for c in self.COLOR_ACIEE_DARK)
            c_bot = tuple(min(255, c+40) for c in self.COLOR_ACIEE_LIGHT)
            border = (0,255,255)

        # Draw
        if is_hover and self.state != self.STATE_FEEDBACK:
            cv2.rectangle(frame, (x1-2, y1-2), (x2+2, y2+2), (0,100,100), -1)
        
        if h_px > 0 and w_px > 0:
            grad = np.zeros((h_px, w_px, 3), dtype=np.uint8)
            for i in range(h_px):
                a = i/h_px
                grad[i,:] = (int(c_top[0]*(1-a)+c_bot[0]*a), int(c_top[1]*(1-a)+c_bot[1]*a), int(c_top[2]*(1-a)+c_bot[2]*a))
            frame[y1:y2, x1:x2] = grad

        cv2.rectangle(frame, (x1, y1), (x2, y2), border, 2)
        
        if is_hover and self.progress > 0 and self.state != self.STATE_FEEDBACK:
            bw_prog = int(w_px * self.progress)
            cv2.rectangle(frame, (x1, y2-6), (x1+bw_prog, y2), (0,255,0), -1)

        # --- TEXT WRAPPING ---
        center_x = x1 + w_px // 2
        center_y = y1 + h_px // 2
        # Padding: 20px
        self._draw_centered_text_wrapped(frame, text, center_x, center_y, w_px - 20, h_px - 20, (255,255,255))

    def draw(self, frame):
        h, w, _ = frame.shape
        curr_time = time.time()

        if self.state == self.STATE_LOADING:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0,0), (w,h), (0,0,0), -1)
            cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
            msg = "AI GENEREAZA INTREBARI..."
            font = cv2.FONT_HERSHEY_SIMPLEX
            ts = cv2.getTextSize(msg, font, 1.0, 2)[0]
            pulse = abs(math.sin(curr_time * 3)) * 255
            col = (255, pulse, 0)
            cv2.putText(frame, msg, (w//2 - ts[0]//2, h//2), font, 1.0, col, 2)
            cv2.putText(frame, "Te rugam asteapta", (w//2 - 100, h//2 + 50), font, 0.7, (200,200,200), 1)
            return frame

        if self.state == self.STATE_FEEDBACK:
            if time.time() - self.feedback_start_time > self.FEEDBACK_DURATION:
                self._next_question()

        if self.state == self.STATE_GAMEOVER:
            panel_w, panel_h = 700, 350
            px, py = w//2 - panel_w//2, 80
            self._draw_gradient_rect(frame, px, py, panel_w, panel_h, self.COLOR_ACIEE_DARK, self.COLOR_ACIEE_LIGHT)
            
            cv2.putText(frame, "REZULTAT FINAL", (w//2 - 130, py + 60), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), 2)
            score_txt = f"{self.score} / {len(self.questions)}"
            ts = cv2.getTextSize(score_txt, cv2.FONT_HERSHEY_SIMPLEX, 2.5, 5)[0]
            cv2.putText(frame, score_txt, (w//2 - ts[0]//2, py + 140), cv2.FONT_HERSHEY_SIMPLEX, 2.5, (0,255,255), 5)
            
            r = 0 if not self.questions else self.score/len(self.questions)
            m1 = "Excelent! Esti nascut pentru inginerie!" if r>=0.8 else "Bravo! Ai potential mare." if r>=0.5 else "Nu te descuraja!"
            m2 = "Te asteptam la ACIEE!" if r>=0.8 else "Hai la ACIEE sa devii expert!" if r>=0.5 else "Vino la ACIEE sa inveti!"
            
            # Clean text
            m1 = self._clean_text(m1)
            m2 = self._clean_text(m2)
            
            # Aici nu e nevoie de wrap complex pentru ca mesajele sunt scurte, dar putem folosi
            ts1 = cv2.getTextSize(m1, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
            cv2.putText(frame, m1, (w//2 - ts1[0]//2, py + 220), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (220,220,220), 2)
            ts2 = cv2.getTextSize(m2, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
            cv2.putText(frame, m2, (w//2 - ts2[0]//2, py + 270), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,255), 2)
            
            self._draw_modern_button(frame, "RETRY", "REINCEARCA (AI)", self.game_over_layout, curr_time)
            self._draw_modern_button(frame, "EXIT", "INAPOI LA MENIU", self.game_over_layout, curr_time)
            return frame

        if not self.questions: return frame
        
        q = self.questions[self.current_q_index]
        q_text = self._clean_text(q['text'])
        
        hw, hh = int(w*0.9), 140
        hx, hy = (w-hw)//2, int(h*0.25)
        self._draw_gradient_rect(frame, hx, hy, hw, hh, self.COLOR_ACIEE_DARK, self.COLOR_ACIEE_LIGHT)
        
        q_count_text = f"Intrebarea {self.current_q_index + 1} / {len(self.questions)}"
        q_count_text = self._clean_text(q_count_text)
        
        panel_q_x, panel_q_y = 30, 30
        ts_q = cv2.getTextSize(q_count_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        
        overlay = frame.copy()
        cv2.rectangle(overlay, (panel_q_x, panel_q_y), (panel_q_x + ts_q[0] + 40, panel_q_y + 40), (0,0,0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        cv2.rectangle(frame, (panel_q_x, panel_q_y), (panel_q_x + ts_q[0] + 40, panel_q_y + 40), (200,200,200), 1)
        cv2.putText(frame, q_count_text, (panel_q_x + 20, panel_q_y + 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

        score_lbl = f"Scor: {self.score}"
        cv2.putText(frame, score_lbl, (hx + hw - 150, hy + hh - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200,200,200), 1)
        
        # --- WRAP PENTRU INTREBARE ---
        center_qx = hx + hw // 2
        center_qy = hy + hh // 2
        self._draw_centered_text_wrapped(frame, q_text, center_qx, center_qy, hw - 40, hh - 20, (255,255,255))
        
        for k, v in q["options"].items():
            self._draw_modern_button(frame, k, v, self.options_layout, curr_time, is_answer=True)
            
        return frame