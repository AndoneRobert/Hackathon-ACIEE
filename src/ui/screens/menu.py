import time

class MenuController:
    def __init__(self):
        self.DWELL_THRESHOLD = 1.5  # Seconds to hover to select
        self.selection_start_time = 0
        self.hovered_option = None
        self.progress = 0.0
        
        # Define the layout (percentages of screen width/height)
        # (x, y, width, height)
        self.buttons = {
            "INFO": (0.05, 0.3, 0.25, 0.4),  # Left
            "PLAY": (0.375, 0.3, 0.25, 0.4), # Center
            "MAP":  (0.70, 0.3, 0.25, 0.4)   # Right
        }

    def update(self, cursor_x, cursor_y):
        """
        Checks if cursor is over a button and updates progress.
        Returns the name of the selected option if confirmed, else None.
        """
        current_hover = None
        
        # 1. Check collision with buttons
        for name, (bx, by, bw, bh) in self.buttons.items():
            if bx < cursor_x < bx + bw and by < cursor_y < by + bh:
                current_hover = name
                break
        
        # 2. Handle Hover Logic
        if current_hover == self.hovered_option and current_hover is not None:
            # User is still hovering
            elapsed = time.time() - self.selection_start_time
            self.progress = min(elapsed / self.DWELL_THRESHOLD, 1.0)
            
            if self.progress >= 1.0:
                self.progress = 0.0
                self.hovered_option = None
                return current_hover # SELECTION CONFIRMED
                
        elif current_hover != self.hovered_option:
            # User moved to a new target or empty space
            self.hovered_option = current_hover
            self.selection_start_time = time.time()
            self.progress = 0.0
            
        return None

    def get_layout(self):
        return self.buttons

    def get_state(self):
        return {
            "hovered": self.hovered_option,
            "progress": self.progress
        }