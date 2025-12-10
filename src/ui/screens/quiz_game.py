import time

class QuizGame:
    def __init__(self):
        # --- CONFIGURARE ---
        self.DWELL_THRESHOLD = 1.0   # Secunde necesare pentru a selecta
        self.FEEDBACK_DURATION = 2.0 # Cât timp afișăm Corect/Greșit
        
        # --- STĂRILE JOCULUI ---
        self.STATE_GAME_SELECT = "GAME_SELECT" # Meniul de alegere (Stânga/Dreapta)
        self.STATE_PLAYING = "PLAYING"         # Întrebarea activă
        self.STATE_FEEDBACK = "FEEDBACK"       # Pauza de după răspuns
        self.STATE_GAMEOVER = "GAMEOVER"       # Ecranul de final
        
        # --- LAYOUT BUTOANE (Valabil și pt meniu și pt răspunsuri) ---
        # Coordonate procentuale: (x, y, width, height)
        self.buttons_layout = {
            "LEFT":  (0.1,  0.4, 0.35, 0.4), # Stânga
            "RIGHT": (0.55, 0.4, 0.35, 0.4)  # Dreapta
        }
        
        # Inițializăm direct în meniul de selecție
        self.reset_to_menu()

    def reset_to_menu(self):
        """Resetează totul și duce utilizatorul la ecranul de alegere a jocului"""
        self.state = self.STATE_GAME_SELECT
        self.reset_quiz_vars()

    def reset_quiz_vars(self):
        """Resetează variabilele strict legate de Quiz (scor, întrebări)"""
        self.questions = self._load_questions()
        self.current_q_index = 0
        self.score = 0
        
        # Variabile pentru Hover (Selecție)
        self.current_selection = None 
        self.selection_start_time = 0
        self.progress = 0.0
        
        # Variabile pentru Feedback
        self.feedback_start_time = 0
        self.last_choice = None
        self.is_correct = False

    def _load_questions(self):
        """Lista de întrebări pentru IT Quiz"""
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
                "correct": "RIGHT"
            },
            {
                "text": "Ce este un algoritm?",
                "options": {"LEFT": "O componenta hardware", "RIGHT": "Pasi logici de rezolvare"},
                "correct": "RIGHT"
            },
            {
                "text": "Cum afisezi un mesaj in Python?",
                "options": {"LEFT": "print('Mesaj')", "RIGHT": "echo 'Mesaj'"},
                "correct": "LEFT"
            }
        ]

    def update(self, cursor_x, cursor_y):
        """
        Logica principală. Se apelează la fiecare frame.
        Input: Poziția cursorului (0.0 - 1.0).
        Output: True dacă jocul cere ieșirea (ex: back to main menu), False altfel.
        """
        
        # 1. ECRANUL DE SELECȚIE (IT Quiz vs Coming Soon)
        if self.state == self.STATE_GAME_SELECT:
            selection = self._handle_selection(cursor_x, cursor_y)
            
            if selection == "LEFT":
                # A ales IT QUIZ -> Începem jocul
                self.state = self.STATE_PLAYING
                self.reset_quiz_vars()
                
            elif selection == "RIGHT":
                # A ales Coming Soon -> Nu facem nimic momentan
                pass
            return False

        # 2. ÎN TIMPUL JOCULUI (Răspunde la întrebări)
        elif self.state == self.STATE_PLAYING:
            selection = self._handle_selection(cursor_x, cursor_y)
            if selection:
                self._submit_answer(selection)
            return False

        # 3. FEEDBACK (Pauza de 2 secunde după răspuns)
        elif self.state == self.STATE_FEEDBACK:
            # Verificăm dacă a trecut timpul
            if time.time() - self.feedback_start_time > self.FEEDBACK_DURATION:
                self._next_question()
            return False

        # 4. GAME OVER (Ecranul final)
        elif self.state == self.STATE_GAMEOVER:
            # Aici main_app se ocupă de desenare.
            # Putem implementa logică de exit dacă utilizatorul face hover oriunde,
            # dar momentan lăsăm main_app să decidă (prin timeout sau buton dedicat).
            return False

        return False

    def _handle_selection(self, x, y):
        """
        Verifică dacă cursorul este peste stânga sau dreapta și calculează progresul.
        Returnează 'LEFT' sau 'RIGHT' doar dacă selecția e completă (100%).
        """
        hovered_zone = None
        
        # Verificăm coliziunea cu butoanele definite în layout
        for zone_name, (bx, by, bw, bh) in self.buttons_layout.items():
            if bx < x < bx + bw and by < y < by + bh:
                hovered_zone = zone_name
                break
        
        # Logica de "Dwell" (Trebuie să ții cursorul un timp)
        if hovered_zone and hovered_zone == self.current_selection:
            elapsed = time.time() - self.selection_start_time
            self.progress = min(elapsed / self.DWELL_THRESHOLD, 1.0)
            
            if self.progress >= 1.0:
                # Selecție confirmată! Resetăm și returnăm rezultatul.
                self.progress = 0.0
                self.current_selection = None
                return hovered_zone 
        else:
            # Resetăm dacă a mutat mâna sau a schimbat zona
            self.current_selection = hovered_zone
            self.selection_start_time = time.time()
            self.progress = 0.0
            
        return None

    def _submit_answer(self, choice):
        """Verifică răspunsul și trece starea pe Feedback"""
        current_q = self.questions[self.current_q_index]
        self.last_choice = choice
        self.is_correct = (choice == current_q["correct"])
        
        if self.is_correct:
            self.score += 1
            
        self.state = self.STATE_FEEDBACK
        self.feedback_start_time = time.time()

    def _next_question(self):
        """Trece la următoarea întrebare sau termină jocul"""
        self.current_q_index += 1
        if self.current_q_index >= len(self.questions):
            self.state = self.STATE_GAMEOVER
        else:
            self.state = self.STATE_PLAYING

    def _get_final_message(self):
        """Generează mesajul de la final în funcție de performanță"""
        if len(self.questions) == 0: return "GATA!"
        
        ratio = self.score / len(self.questions)
        
        if ratio == 1.0:
            return "EXCELENT! Esti genial!"
        elif ratio >= 0.7:
            return "FOARTE BINE! Bravo!"
        elif ratio >= 0.5:
            return "BUN! Dar poti mai mult."
        else:
            return "NU TE DESCURAJA! Mai incearca."

    def get_current_data(self):
        """
        Împachetează toate datele necesare pentru ca main_app să deseneze interfața.
        """
        data = {
            "state": self.state,
            "layout": self.buttons_layout,
            "selection": self.current_selection,
            "progress": self.progress
        }

        # Date specifice pentru meniul de selecție
        if self.state == self.STATE_GAME_SELECT:
            return data 

        # Date specifice pentru ecranul de final
        if self.state == self.STATE_GAMEOVER:
            data["score"] = self.score
            data["total"] = len(self.questions)
            data["final_message"] = self._get_final_message()
            return data

        # Date specifice pentru joc (Întrebare / Răspuns)
        q = self.questions[self.current_q_index]
        data.update({
            "question": q["text"],
            "options": q["options"],
            "score": self.score,
            "q_number": self.current_q_index + 1,
            "total_q": len(self.questions),
            "is_correct": self.is_correct,
            "correct_ans": q["correct"],
            "last_choice": self.last_choice
        })
        
        return data