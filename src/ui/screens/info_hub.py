# src/ui/screens/info_hub.py
from .info_detail import get_page_text

class InfoHub:
    def __init__(self):
        # Data: Specializations and their page counts
        self.specializations = {
            "AIA": {"name": "Automatica, Informatica Aplicata si Sisteme Inteligente", "pages": 4},
            "CTI": {"name": "Calculatoare si Tehnologia Informatiei", "pages": 4},
            "IE": {"name": "Inginerie Electrica", "pages": 4},
            "IETTI": {"name": "Inginerie electronica, telecomunicatii si tehnologii informationale", "pages": 4}
        }
        
        # Layout for buttons (Selection Mode)
        self.buttons = {
            "AIA": (0.1, 0.2, 0.35, 0.3),  # Top-Left
            "CTI": (0.55, 0.2, 0.35, 0.3), # Top-Right
            "IE": (0.1, 0.6, 0.35, 0.3),  # Bottom-Left
            "IETTI": (0.55, 0.6, 0.35, 0.3)  # Bottom-Right
        }
        
        # State
        self.active_spec = None
        self.current_page = 0
        self.dwell_timer = 0
        self.hovered_btn = None
        self.DWELL_THRESHOLD = 1.5

    def update(self, cursor_x, cursor_y, gesture):
        if self.active_spec is None:
            return self._update_selection_mode(cursor_x, cursor_y)
        else:
            return self._update_detail_mode(gesture)

    def _update_selection_mode(self, x, y):
        hit = None
        for key, (bx, by, bw, bh) in self.buttons.items():
            if bx < x < bx+bw and by < y < by+bh:
                hit = key
                break
        
        if hit and hit == self.hovered_btn:
            self.dwell_timer += 1
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
            if self.current_page < max_pages - 1:
                self.current_page += 1
                return "NEXT_PAGE"
                
        elif gesture == "SWIPE_RIGHT":
            if self.current_page > 0:
                self.current_page -= 1
                return "PREV_PAGE"
            else:
                self.active_spec = None
                return "BACK_TO_MENU"
                
        return None

    def get_ui_data(self):
        spec_name = None
        page_text = ""
        if self.active_spec is not None:
            spec = self.specializations.get(self.active_spec, {})
            spec_name = spec.get("name", self.active_spec)
            page_text = get_page_text(self.active_spec, self.current_page)

        return {
            "mode": "SELECTION" if self.active_spec is None else "DETAIL",
            "active_spec": self.active_spec,
            "spec_name": spec_name,
            "page": self.current_page + 1, # Display 1-indexed
            "buttons": self.buttons,
            "hovered": self.hovered_btn,
            "progress": min(self.dwell_timer / 45.0, 1.0),
            "page_text": page_text
        }