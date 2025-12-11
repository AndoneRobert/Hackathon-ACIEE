import time
import cv2

class QuizGame:
    def __init__(self):
        # --- CONFIGURARE ---
        self.DWELL_THRESHOLD = 1.0  # Secunde pentru selectare
        self.FEEDBACK_DURATION = 2.0 # Cât timp afișăm Corect/Greșit
        
        # --- STĂRI INTERNE ---
        self.STATE_PLAYING = "PLAYING"
        self.STATE_FEEDBACK = "FEEDBACK"
        self.STATE_GAMEOVER = "GAMEOVER"
        
        # Variabile cerute de main_app.py
        self.game_over = False 
        self.state = self.STATE_PLAYING
        
        # Datele Quiz-ului
        self.questions = self._load_questions()
        self.current_q_index = 0
        self.score = 0
        
        # Variabile pentru Interacțiune (Hover)
        self.current_selection = None
        self.selection_start_time = 0
        self.progress = 0.0
        
        # Variabile pentru Feedback
        self.feedback_start_time = 0
        self.last_choice = None
        self.is_correct = False
        
        # Layout Răspunsuri (Stânga / Dreapta)
        # Coordonate: (x, y, width, height) ca procent din ecran
        self.options_layout = {
            "LEFT":  (0.1,  0.4, 0.35, 0.4),
            "RIGHT": (0.55, 0.4, 0.35, 0.4)
        }

    def _load_questions(self):
        return [
            {"text": "Ce este CPU?", "options": {"LEFT": "Central Processing Unit", "RIGHT": "Central Power Unit"}, "correct": "LEFT"},
            {"text": "Memoria volatila este:", "options": {"LEFT": "HDD", "RIGHT": "RAM"}, "correct": "RIGHT"},
            {"text": "Binar inseamna:", "options": {"LEFT": "0 si 1", "RIGHT": "1 si 2"}, "correct": "LEFT"},
            {"text": "HTML e limbaj de programare?", "options": {"LEFT": "DA", "RIGHT": "NU"}, "correct": "RIGHT"},
            {"text": "Algoritmul este:", "options": {"LEFT": "Hardware", "RIGHT": "Pasi Logici"}, "correct": "RIGHT"},
             {"text": "Print in Python:", "options": {"LEFT": "print()", "RIGHT": "echo()"}, "correct": "LEFT"}
        ]

    def update(self, cursor_x, cursor_y):
        """
        Logica jocului. Se apelează la fiecare frame din main_app.
        """
        if self.state == self.STATE_GAMEOVER:
            return

        # 1. Pauză pentru Feedback (după ce răspunzi)
        if self.state == self.STATE_FEEDBACK:
            if time.time() - self.feedback_start_time > self.FEEDBACK_DURATION:
                self._next_question()
            return

        # 2. Logica de Joc (Așteaptă răspuns)
        hovered = None
        # Verificăm dacă cursorul este peste vreun buton
        for key, (bx, by, bw, bh) in self.options_layout.items():
            if bx < cursor_x < bx + bw and by < cursor_y < by + bh:
                hovered = key
                break
        
        # Calculăm progresul de selecție
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
        """Verifică răspunsul"""
        q = self.questions[self.current_q_index]
        self.last_choice = choice
        self.is_correct = (choice == q["correct"])
        
        if self.is_correct:
            self.score += 1
            
        self.state = self.STATE_FEEDBACK
        self.feedback_start_time = time.time()

    def _next_question(self):
        """Trece la următoarea întrebare"""
        self.current_q_index += 1
        if self.current_q_index >= len(self.questions):
            self.state = self.STATE_GAMEOVER
            self.game_over = True
        else:
            self.state = self.STATE_PLAYING

    def draw(self, frame):
        """
        Desenează interfața jocului.
        Această metodă este apelată de main_app.py: display_frame = game.draw(display_frame)
        """
        h, w, _ = frame.shape
        
        # --- ECRAN FINAL (GAME OVER) ---
        if self.state == self.STATE_GAMEOVER:
            cv2.putText(frame, "QUIZ COMPLETE", (w//2 - 150, h//2 - 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)
            cv2.putText(frame, f"SCORE: {self.score}/{len(self.questions)}", (w//2 - 120, h//2 + 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
            
            # Mesaj final în funcție de scor
            ratio = self.score / len(self.questions)
            msg = "Bravo!" if ratio > 0.5 else "Mai incearca!"
            cv2.putText(frame, msg, (w//2 - 80, h//2 + 120), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 200, 200), 2)
            return frame

        # --- ECRAN DE JOC (ÎNTREBARE) ---
        q = self.questions[self.current_q_index]
        
        # Titlu și Scor
        cv2.putText(frame, f"Q{self.current_q_index+1}: {q['text']}", (50, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        cv2.putText(frame, f"Score: {self.score}", (w-250, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

        # Desenăm Opțiunile (Butoanele)
        for key, text in q["options"].items():
            bx, by, bw, bh = self.options_layout[key]
            x1, y1 = int(bx * w), int(by * h)
            w_px, h_px = int(bw * w), int(bh * h)
            x2, y2 = x1 + w_px, y1 + h_px
            
            # Logică Culori
            color = (50, 50, 50)         # Gri implicit
            border_color = (200, 200, 200) # Contur implicit
            
            if self.state == self.STATE_FEEDBACK:
                # Arătăm rezultatul (Verde/Roșu)
                if key == q["correct"]:
                    color = (0, 150, 0) # Verde
                    text += " (OK)"
                elif key == self.last_choice and not self.is_correct:
                    color = (0, 0, 150) # Roșu
                    text += " (X)"
            elif key == self.current_selection:
                # Hover activ
                color = (100, 100, 100)
                border_color = (0, 255, 255) # Galben

            # Desenăm Cutiile (Overlay Transparent)
            overlay = frame.copy()
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
            cv2.rectangle(frame, (x1, y1), (x2, y2), border_color, 2)
            
            # Bara de Progres (doar la hover în timpul jocului)
            if key == self.current_selection and self.state == self.STATE_PLAYING and self.progress > 0:
                bar_w = int(w_px * self.progress)
                cv2.rectangle(frame, (x1, y2-10), (x1+bar_w, y2), (0, 255, 0), -1)

            # Centrare Text în Buton
            font_scale = 0.8
            tsz = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)[0]
            tx = x1 + (w_px - tsz[0]) // 2
            ty = y1 + (h_px + tsz[1]) // 2
            cv2.putText(frame, text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 2)

        return frame