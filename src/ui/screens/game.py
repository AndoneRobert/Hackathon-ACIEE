import time

class QuizGame:
    def __init__(self):
        # Configuration
        self.DWELL_THRESHOLD = 1.0  # Seconds to hold hand in corner to select
        
        # Game State
        self.questions = self._load_questions()
        self.current_q_index = 0
        self.score = 0
        self.game_over = False
        
        # Selection State
        self.current_selection = None # 'A', 'B', 'C', 'D' or None
        self.selection_start_time = 0
        self.progress = 0.0 # 0.0 to 1.0 (for the visual loading bar)

    def _load_questions(self):
        # In a real app, load this from assets/data/quiz.json
        return [
            {
                "text": "Which faculty was founded first?",
                "answers": {"A": "Arts", "B": "Science", "C": "Law", "D": "Engineering"},
                "correct": "C"
            },
            {
                "text": "How many students attend this uni?",
                "answers": {"A": "5,000", "B": "15,000", "C": "50,000", "D": "25,000"},
                "correct": "B"
            },
            {
                "text": "What is the mascot animal?",
                "answers": {"A": "Lion", "B": "Eagle", "C": "Bear", "D": "Wolf"},
                "correct": "A"
            }
        ]

    def update(self, cursor_x, cursor_y):
        """
        Updates game state based on hand position (0.0 to 1.0).
        """
        if self.game_over:
            return

        # 1. Determine which quadrant the hand is in
        selected_zone = self._get_quadrant(cursor_x, cursor_y)

        # 2. Dwell Logic (The "Hold to Select" mechanic)
        if selected_zone and selected_zone == self.current_selection:
            # User is holding position... calculate progress
            elapsed = time.time() - self.selection_start_time
            self.progress = min(elapsed / self.DWELL_THRESHOLD, 1.0)
            
            # If threshold reached, confirm the answer
            if self.progress >= 1.0:
                self._confirm_answer(selected_zone)
                self.progress = 0.0
                self.current_selection = None
        else:
            # User moved to a new zone or center
            self.current_selection = selected_zone
            self.selection_start_time = time.time()
            self.progress = 0.0

    def _get_quadrant(self, x, y):
        # Divide screen into 4 corners with a "dead zone" in the middle
        # to prevent accidental switching.
        
        margin = 0.4 # The middle 20% of the screen is "neutral"
        
        if x < margin and y < margin: return "A"       # Top-Left
        if x > 1-margin and y < margin: return "B"     # Top-Right
        if x < margin and y > 1-margin: return "C"     # Bottom-Left
        if x > 1-margin and y > 1-margin: return "D"   # Bottom-Right
        
        return None # Hand is in the middle

    def _confirm_answer(self, choice):
        current_q = self.questions[self.current_q_index]
        
        if choice == current_q["correct"]:
            self.score += 1
            print(f"Correct! Score: {self.score}")
        else:
            print(f"Wrong! Correct was {current_q['correct']}")

        # Move to next question
        self.current_q_index += 1
        if self.current_q_index >= len(self.questions):
            self.game_over = True
            print("GAME OVER")

    def get_current_data(self):
        """Returns data needed for the UI to draw"""
        if self.game_over:
            return {"game_over": True, "score": self.score, "total": len(self.questions)}
            
        q = self.questions[self.current_q_index]
        return {
            "game_over": False,
            "question": q["text"],
            "answers": q["answers"],
            "selection": self.current_selection,
            "progress": self.progress
        }