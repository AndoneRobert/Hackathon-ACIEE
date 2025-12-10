import time

class QuizGame:
    def __init__(self):
        # Configuration
        self.DWELL_THRESHOLD = 1.0  # Timp de hover pentru selectare
        self.FEEDBACK_DURATION = 2.0 # Cât timp vezi rezultatul
        
        # State Constants
        self.STATE_GAME_SELECT = "GAME_SELECT" # Ecranul nou cu 2 jocuri
        self.STATE_PLAYING = "PLAYING"         # Quiz-ul efectiv
        self.STATE_FEEDBACK = "FEEDBACK"       # Corect/Gresit
        self.STATE_GAMEOVER = "GAMEOVER"       # Scor final
        
        # Layout Butoane (Procente din ecran: x, y, w, h)
        # Folosim aceleași coordonate pentru Selecție Joc și Răspunsuri (Stânga/Dreapta)
        self.buttons_layout = {
            "LEFT":  (0.1,  0.4, 0.35, 0.4), # Stânga
            "RIGHT": (0.55, 0.4, 0.35, 0.4)  # Dreapta
        }
        
        self.reset_to_menu()

    def reset_to_menu(self):
        """Revine la ecranul de alegere a jocului"""
        self.state = self.STATE_GAME_SELECT
        self.reset_quiz_vars()

    def reset_quiz_vars(self):
        """Resetează variabilele pentru o sesiune nouă de Quiz"""
        self.questions = self._load_questions()
        self.current_q_index = 0
        self.score = 0
        
        # Variabile de selecție (Hover)
        self.current_selection = None 
        self.selection_start_time = 0
        self.progress = 0.0
        
        # Feedback
        self.feedback_start_time = 0
        self.last_choice = None
        self.is_correct = False

    def _load_questions(self):
        # Întrebări de informatică (Liceu -> Facultate)
        # Format: 2 variante de răspuns (LEFT / RIGHT)
        return [
            {
                "text": "Ce reprezinta CPU?",
                "options": {"LEFT": "Central Processing Unit", "RIGHT": "Central Power Unit"},
                "correct": "LEFT"
            },
            {
                "text": "Care memorie este volatila?",
                "options": {"LEFT": "HDD (Hard Disk)", "RIGHT": "RAM (Random Access)"},
                "correct": "RIGHT"
            },
            {
                "text": "Limbajul binar foloseste doar:",
                "options": {"LEFT": "0 si 1", "RIGHT": "1 si 2"},
                "correct": "LEFT"
            },
            {
                "text": "HTML este un limbaj de programare?",
                "options": {"LEFT": "DA", "RIGHT": "NU (e de marcare)"},
                "correct": "RIGHT" # HTML e Markup Language
            },
            {
                "text": "Ce este un algoritm?",
                "options": {"LEFT": "O componenta hardware", "RIGHT": "O secventa de pasi logici"},
                "correct": "RIGHT"
            },
            {
                # Întrebare mai grea
                "text": "In Python, cum afisezi un mesaj?",
                "options": {"LEFT": "print('Mesaj')", "RIGHT": "echo 'Mesaj'"},
                "correct": "LEFT"
            }
        ]

    def update(self, cursor_x, cursor_y):
        """
        Gestionează logica în funcție de starea curentă.
        Returnează True dacă utilizatorul iese din tot modulul (Back to Menu principal).
        """
        
        # 1. SELECTIE JOC (Ecranul nou)
        if self.state == self.STATE_GAME_SELECT:
            selection = self._handle_selection(cursor_x, cursor_y)
            if selection == "LEFT":
                # Start Quiz
                self.state = self.STATE_PLAYING
                self.reset_quiz_vars()
            elif selection == "RIGHT":
                # Jocul 2 (Placeholder) - nu face nimic momentan
                pass
            return False

        # 2. QUIZ PLAYING
        elif self.state == self.STATE_PLAYING:
            selection = self._handle_selection(cursor_x, cursor_y)
            if selection:
                self._submit_answer(selection)
            return False

        # 3. FEEDBACK (Pauza)
        elif self.state == self.STATE_FEEDBACK:
            if time.time() - self.feedback_start_time > self.FEEDBACK_DURATION:
                self._next_question()
            return False

        # 4. GAMEOVER
        elif self.state == self.STATE_GAMEOVER:
            # Aici am putea adăuga un buton de "Back", dar momentan
            # resetăm automat după 5 secunde sau lăsăm main_app să iasă
            # Implementăm o ieșire simplă la hover oriunde pentru demo
            return False # Se ocupă main_app de ieșire sau resetăm noi manual

        return False

    def _handle_selection(self, x, y):
        """Logica generică de Hover pe butoanele LEFT/RIGHT"""
        hovered_zone = None
        
        # Verificăm coliziunea
        for zone_name, (bx, by, bw, bh) in self.buttons_layout.items():
            if bx < x < bx + bw and by < y < by + bh:
                hovered_zone = zone_name
                break
        
        # Calculăm progresul (Dwell time)
        if hovered_zone and hovered_zone == self.current_selection:
            elapsed = time.time() - self.selection_start_time
            self.progress = min(elapsed / self.DWELL_THRESHOLD, 1.0)
            
            if self.progress >= 1.0:
                self.progress = 0.0
                self.current_selection = None
                return hovered_zone # CONFIRMED SELECTION
        else:
            self.current_selection = hovered_zone
            self.selection_start_time = time.time()
            self.progress = 0.0
            
        return None

    def _submit_answer(self, choice):
        current_q = self.questions[self.current_q_index]
        self.last_choice = choice
        self.is_correct = (choice == current_q["correct"])
        
        if self.is_correct:
            self.score += 1
            
        self.state = self.STATE_FEEDBACK
        self.feedback_start_time = time.time()

    def _next_question(self):
        self.current_q_index += 1
        if self.current_q_index >= len(self.questions):
            self.state = self.STATE_GAMEOVER
        else:
            self.state = self.STATE_PLAYING

    def get_current_data(self):
        """Returnează datele pentru UI"""
        
        data = {
            "state": self.state,
            "layout": self.buttons_layout,
            "selection": self.current_selection,
            "progress": self.progress
        }

        if self.state == self.STATE_GAME_SELECT:
            return data # UI-ul va ști să deseneze meniul de selecție

        if self.state == self.STATE_GAMEOVER:
            data["score"] = self.score
            data["total"] = len(self.questions)
            return data

        # Pentru Playing/Feedback
        q = self.questions[self.current_q_index]
        data.update({
            "question": q["text"],
            "options": q["options"],
            "score": self.score,
            "q_number": self.current_q_index + 1,
            "total_q": len(self.questions),
            # Feedback specific
            "is_correct": self.is_correct,
            "correct_ans": q["correct"],
            "last_choice": self.last_choice
        })
        
        return data