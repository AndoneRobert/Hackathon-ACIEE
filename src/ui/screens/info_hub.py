import cv2
import time

class InfoHub:
    def __init__(self):
        self.mode = "SELECTION"  # Modes: "SELECTION", "CONTENT"
        
        # Sample Data
        self.faculties = {
            "AUTOMATICS": ["Computer Science", "Robotics", "Systems Engineering"],
            "ELECTRICAL": ["Electronics", "Telecommunications", "Power Eng."],
            "MECHANICAL": ["Automotive", "Mechatronics", "Industrial Design"]
        }
        
        # Layout for Faculty Buttons (Normalized: x, y, w, h)
        self.buttons = {
            "AUTOMATICS": (0.1, 0.3, 0.25, 0.2),
            "ELECTRICAL": (0.375, 0.3, 0.25, 0.2),
            "MECHANICAL": (0.65, 0.3, 0.25, 0.2)
        }
        
        # State
        self.active_faculty = None
        self.page_index = 0
        self.hovered = None
        self.hover_start = 0
        self.selection_progress = 0.0
        self.SELECTION_TIME = 1.5
        self.last_nav_time = 0

    def update(self, cx, cy, gesture):
        """
        Handle hover selection and swipe navigation.
        Returns 'BACK_TO_MENU' if needed.
        """
        # --- Mode: SELECTION ---
        if self.mode == "SELECTION":
            # Check for Back Gesture (e.g., if gesture is 'SWIPE_DOWN' or similar)
            # For now, we rely on hover logic to select.
            
            curr_hover = None
            for name, (bx, by, bw, bh) in self.buttons.items():
                if bx < cx < bx + bw and by < cy < by + bh:
                    curr_hover = name
                    break
            
            if curr_hover:
                if self.hovered != curr_hover:
                    self.hovered = curr_hover
                    self.hover_start = time.time()
                    self.selection_progress = 0.0
                else:
                    elapsed = time.time() - self.hover_start
                    self.selection_progress = min(elapsed / self.SELECTION_TIME, 1.0)
                    
                    if elapsed >= self.SELECTION_TIME:
                        self.active_faculty = curr_hover
                        self.mode = "CONTENT"
                        self.page_index = 0
                        self.hovered = None
                        self.selection_progress = 0.0
            else:
                self.hovered = None
                self.selection_progress = 0.0

        # --- Mode: CONTENT ---
        elif self.mode == "CONTENT":
            # Navigation Debounce
            if time.time() - self.last_nav_time > 1.0:
                if gesture == "SWIPE_LEFT":
                    # Next Page
                    specs = self.faculties[self.active_faculty]
                    if self.page_index < len(specs) - 1:
                        self.page_index += 1
                        self.last_nav_time = time.time()
                
                elif gesture == "SWIPE_RIGHT":
                    # Prev Page or Back
                    if self.page_index > 0:
                        self.page_index -= 1
                        self.last_nav_time = time.time()
                    else:
                        self.mode = "SELECTION"
                        self.last_nav_time = time.time()
                        
                elif gesture == "OPEN_PALM": 
                    # Optional: Quick exit gesture
                    return "BACK_TO_MENU"

        return None

    def get_ui_data(self):
        """Legacy helper, can be removed if strictly using draw()."""
        return {
            "mode": self.mode,
            "buttons": self.buttons,
            "hovered": self.hovered,
            "progress": self.selection_progress,
            "active_spec": self.faculties[self.active_faculty][self.page_index] if self.active_faculty else "",
            "page": self.page_index + 1
        }

    def draw(self, frame):
        """
        Draws the InfoHub UI.
        """
        h, w, _ = frame.shape
        
        # Background
        cv2.rectangle(frame, (0, 0), (w, h), (20, 20, 25), -1)
        
        if self.mode == "SELECTION":
            # Header
            cv2.putText(frame, "SELECT A FACULTY", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
            cv2.line(frame, (50, 120), (450, 120), (0, 255, 255), 2)
            
            # Draw Buttons
            for name, (bx, by, bw, bh) in self.buttons.items():
                x1, y1 = int(bx * w), int(by * h)
                x2, y2 = int((bx + bw) * w), int((by + bh) * h)
                
                is_hovered = (self.hovered == name)
                
                # Style
                color = (60, 60, 70)
                border = (200, 200, 200)
                if is_hovered:
                    color = (100, 50, 20)
                    border = (0, 200, 255)
                
                # Draw Box
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, -1)
                cv2.rectangle(frame, (x1, y1), (x2, y2), border, 2 if not is_hovered else 3)
                
                # Draw Progress
                if is_hovered:
                    bar_w = int((x2 - x1) * self.selection_progress)
                    cv2.rectangle(frame, (x1, y2 - 10), (x1 + bar_w, y2), (0, 255, 0), -1)
                
                # Text
                text_size = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
                tx = x1 + (x2 - x1 - text_size[0]) // 2
                ty = y1 + (y2 - y1 + text_size[1]) // 2
                cv2.putText(frame, name, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        elif self.mode == "CONTENT":
            # Data
            faculty = self.active_faculty
            specs = self.faculties[faculty]
            current_spec = specs[self.page_index]
            
            # Card Panel
            px1, py1 = 100, 100
            px2, py2 = w - 100, h - 100
            
            overlay = frame.copy()
            cv2.rectangle(overlay, (px1, py1), (px2, py2), (40, 40, 45), -1)
            cv2.addWeighted(overlay, 0.9, frame, 0.1, 0, frame)
            cv2.rectangle(frame, (px1, py1), (px2, py2), (0, 255, 255), 2)
            
            # Text Content
            cv2.putText(frame, f"FACULTY: {faculty}", (px1 + 50, py1 + 80), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (150, 150, 150), 2)
            
            cv2.putText(frame, current_spec, (px1 + 50, py1 + 180), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2.0, (255, 255, 255), 4)
            
            # Pagination
            page_str = f"Specialization {self.page_index + 1} / {len(specs)}"
            cv2.putText(frame, page_str, (px1 + 50, py2 - 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

            # Instructions
            hint = "Swipe LEFT for next  |  Swipe RIGHT to go back"
            ts = cv2.getTextSize(hint, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 1)[0]
            cv2.putText(frame, hint, (w // 2 - ts[0] // 2, py2 + 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)

        return frame