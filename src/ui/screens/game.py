import cv2
import time

class QuizGame:
    def __init__(self):
        # Sample Question Data
        self.questions = [
            {
                "q": "What is the output of print(2 ** 3)?",
                "options": {"A": "6", "B": "8", "C": "9", "D": "Error"},
                "correct": "B"
            },
            {
                "q": "Which keyword is used for loops?",
                "options": {"A": "for", "B": "loop", "C": "repeat", "D": "cycle"},
                "correct": "A"
            },
            {
                "q": "In OpenCV, which color space is default?",
                "options": {"A": "RGB", "B": "HSV", "C": "BGR", "D": "CMYK"},
                "correct": "C"
            }
        ]
        
        # Game State
        self.current_q_index = 0
        self.score = 0
        self.game_over = False
        
        # Selection / Hover Logic
        self.selection = None
        self.selection_start = 0
        self.selection_progress = 0.0
        self.SELECTION_TIME = 2.0  # Seconds to hold to select
        
        # Cooldown to prevent double-skipping
        self.last_answer_time = 0

    def update(self, cursor_x, cursor_y):
        """
        Updates hover logic and checks for answer selection.
        """
        if self.game_over:
            return

        # Prevent immediate input after a question change
        if time.time() - self.last_answer_time < 1.0:
            return

        current_q = self.questions[self.current_q_index]
        hovered_option = None

        # Define Hitboxes (Normalized 0.0 - 1.0)
        # We roughly map these to where we draw them
        hitboxes = {
            "A": (0.05, 0.3, 0.4, 0.2),  # x, y, w, h
            "B": (0.55, 0.3, 0.4, 0.2),
            "C": (0.05, 0.6, 0.4, 0.2),
            "D": (0.55, 0.6, 0.4, 0.2)
        }

        for key, (hx, hy, hw, hh) in hitboxes.items():
            if hx < cursor_x < hx + hw and hy < cursor_y < hy + hh:
                hovered_option = key
                break
        
        # Logic for holding selection
        if hovered_option:
            if self.selection != hovered_option:
                self.selection = hovered_option
                self.selection_start = time.time()
                self.selection_progress = 0.0
            else:
                elapsed = time.time() - self.selection_start
                self.selection_progress = min(elapsed / self.SELECTION_TIME, 1.0)
                
                if elapsed >= self.SELECTION_TIME:
                    self.submit_answer(hovered_option)
        else:
            self.selection = None
            self.selection_progress = 0.0

    def submit_answer(self, answer_key):
        """Checks answer and advances game."""
        correct = self.questions[self.current_q_index]["correct"]
        if answer_key == correct:
            self.score += 10
        
        self.current_q_index += 1
        self.last_answer_time = time.time()
        self.selection = None
        self.selection_progress = 0.0
        
        if self.current_q_index >= len(self.questions):
            self.game_over = True

    def get_current_data(self):
        """Returns minimal data for the main loop logic (if needed)."""
        if self.game_over:
            return {"game_over": True, "score": self.score}
        
        q = self.questions[self.current_q_index]
        return {
            "game_over": False,
            "question": q["q"],
            "answers": q["options"],
            "selection": self.selection,
            "progress": self.selection_progress,
            "score": self.score
        }

    def draw(self, frame):
        """
        Draws the Game UI directly onto the frame.
        """
        h, w, _ = frame.shape
        
        # --- GAME OVER SCREEN ---
        if self.game_over:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 50), -1)
            cv2.addWeighted(overlay, 0.9, frame, 0.1, 0, frame)
            
            cv2.putText(frame, "GAME OVER", (w//2 - 200, h//2 - 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2.5, (255, 255, 255), 4)
            
            score_text = f"Final Score: {self.score}"
            ts = cv2.getTextSize(score_text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)[0]
            cv2.putText(frame, score_text, ((w - ts[0])//2, h//2 + 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)
            return frame

        # --- ACTIVE GAME UI ---
        
        # 1. Header (Question)
        current_q = self.questions[self.current_q_index]
        
        # Dark panel for question
        cv2.rectangle(frame, (50, 40), (w - 50, 160), (30, 30, 30), -1)
        cv2.rectangle(frame, (50, 40), (w - 50, 160), (255, 255, 255), 2)
        
        # Draw Question Text
        cv2.putText(frame, f"Q{self.current_q_index + 1}: {current_q['q']}", (80, 115), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

        # Draw Score
        cv2.putText(frame, f"Score: {self.score}", (w - 250, 130), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # 2. Answer Options (A, B, C, D)
        layout_map = {
            "A": (int(0.05*w), int(0.3*h), int(0.4*w), int(0.2*h)),
            "B": (int(0.55*w), int(0.3*h), int(0.4*w), int(0.2*h)),
            "C": (int(0.05*w), int(0.6*h), int(0.4*w), int(0.2*h)),
            "D": (int(0.55*w), int(0.6*h), int(0.4*w), int(0.2*h)),
        }

        for key, text in current_q["options"].items():
            bx, by, bw, bh = layout_map[key]
            
            is_selected = (self.selection == key)
            
            # Colors
            bg_color = (60, 60, 60)
            border_color = (200, 200, 200)
            
            if is_selected:
                bg_color = (100, 50, 0) # Dark Orange
                border_color = (0, 165, 255) # Orange/Gold
            
            # Draw Box
            cv2.rectangle(frame, (bx, by), (bx+bw, by+bh), bg_color, -1)
            cv2.rectangle(frame, (bx, by), (bx+bw, by+bh), border_color, 2 if not is_selected else 4)
            
            # Draw Progress Bar (if holding)
            if is_selected:
                bar_w = int(bw * self.selection_progress)
                cv2.rectangle(frame, (bx, by + bh - 15), (bx + bar_w, by + bh), (0, 255, 0), -1)

            # Draw Text (Centered in box)
            label = f"{key}: {text}"
            font_scale = 1.0
            font_thick = 2
            ts = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thick)[0]
            tx = bx + (bw - ts[0]) // 2
            ty = by + (bh + ts[1]) // 2
            
            cv2.putText(frame, label, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255,255,255), font_thick)

        return frame