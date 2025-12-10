class InfoHub:
    def __init__(self):
        # Data: Specializations and their page counts
        self.specializations = {
            "CS": {"name": "Computer Science", "pages": 3},
            "MKT": {"name": "Marketing", "pages": 2},
            "ENG": {"name": "Engineering", "pages": 4},
            "ART": {"name": "Arts & Design", "pages": 2}
        }
        
        # Layout for buttons (Selection Mode)
        self.buttons = {
            "CS": (0.1, 0.2, 0.35, 0.3),  # Top-Left
            "MKT": (0.55, 0.2, 0.35, 0.3), # Top-Right
            "ENG": (0.1, 0.6, 0.35, 0.3),  # Bottom-Left
            "ART": (0.55, 0.6, 0.35, 0.3)  # Bottom-Right
        }
        
        # State
        self.active_spec = None   # None = Selection Mode, "CS" = Viewing CS
        self.current_page = 0
        self.dwell_timer = 0
        self.hovered_btn = None
        self.DWELL_THRESHOLD = 1.5

    def update(self, cursor_x, cursor_y, gesture):
        """
        Inputs: Cursor position (0-1) and Gesture ("CLICK", "SWIPE_LEFT", etc)
        """
        
        # MODE 1: SELECTING A SPECIALIZATION
        if self.active_spec is None:
            return self._update_selection_mode(cursor_x, cursor_y)

        # MODE 2: VIEWING PAGES (Swipe Logic)
        else:
            return self._update_detail_mode(gesture)

    def _update_selection_mode(self, x, y):
        # Check collision
        hit = None
        for key, (bx, by, bw, bh) in self.buttons.items():
            if bx < x < bx+bw and by < y < by+bh:
                hit = key
                break
        
        # Handle Dwell
        if hit and hit == self.hovered_btn:
            self.dwell_timer += 1 # In real app use time.time()
            # Simple frame counter for test (approx 45 frames = 1.5s)
            if self.dwell_timer > 45: 
                self.active_spec = hit
                self.current_page = 0
                self.dwell_timer = 0
                return "OPEN_DETAIL"
        else:
            self.hovered_btn = hit
            self.dwell_timer = 0
            
        return None

    def _update_detail_mode(self, gesture):
        if not gesture:
            return None
            
        max_pages = self.specializations[self.active_spec]["pages"]
        
        if gesture == "SWIPE_LEFT":
            # Next Page
            if self.current_page < max_pages - 1:
                self.current_page += 1
                return "NEXT_PAGE"
                
        elif gesture == "SWIPE_RIGHT":
            # Previous Page
            if self.current_page > 0:
                self.current_page -= 1
                return "PREV_PAGE"
            else:
                # Swipe Right on first page = Go Back to Menu
                self.active_spec = None
                return "BACK_TO_MENU"
                
        return None

    def get_ui_data(self):
        return {
            "mode": "SELECTION" if self.active_spec is None else "DETAIL",
            "active_spec": self.active_spec,
            "page": self.current_page + 1, # Display 1-indexed
            "buttons": self.buttons,
            "hovered": self.hovered_btn,
            "progress": min(self.dwell_timer / 45.0, 1.0)
        }
