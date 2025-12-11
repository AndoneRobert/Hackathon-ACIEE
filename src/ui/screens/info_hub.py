# src/ui/screens/info_hub.py
import cv2
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
    
    def draw(self, frame):
        h, w, _ = frame.shape
        data = self.get_ui_data()
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Draw Title
        cv2.putText(frame, "INFO HUB", (50, 50), 
                   font, 1.5, (255, 255, 255), 3)

        if data["mode"] == "SELECTION":
            # --- SELECTION MODE DRAWING ---
            cv2.putText(frame, "Alege specializarea:", (50, 120), 
                       font, 1.0, (200, 200, 200), 2)

            for key, (bx_norm, by_norm, bw_norm, bh_norm) in self.buttons.items():
                
                # Convert normalized coordinates to pixels
                x1 = int(bx_norm * w)
                y1 = int(by_norm * h)
                x2 = int((bx_norm + bw_norm) * w)
                y2 = int((by_norm + bh_norm) * h)
                
                is_hovered = (key == data["hovered"])
                
                # Colors
                bg_color = (15, 15, 45)
                border_color = (100, 100, 100)
                text_color = (255, 255, 255)
                
                if is_hovered:
                    bg_color = (30, 30, 90)
                    border_color = (255, 255, 0)
                    text_color = (255, 255, 0)
                
                # Draw Box
                cv2.rectangle(frame, (x1, y1), (x2, y2), bg_color, -1)
                cv2.rectangle(frame, (x1, y1), (x2, y2), border_color, 2)
                
                # Draw Progress Bar
                if is_hovered and data["progress"] > 0:
                    bar_w = int((x2 - x1) * data["progress"])
                    cv2.rectangle(frame, (x1, y2 - 10), (x1 + bar_w, y2), (0, 255, 0), -1)

                # Draw Text (Centered)
                text_content = self.specializations[key]["name"].split(',')[0]
                text_size = cv2.getTextSize(text_content, font, 0.8, 2)[0]
                tx = x1 + (x2 - x1 - text_size[0]) // 2
                ty = y1 + (y2 - y1 + text_size[1]) // 2
                
                cv2.putText(frame, text_content, (tx, ty), font, 0.8, text_color, 2)
        
        elif data["mode"] == "DETAIL":
            # --- DETAIL MODE DRAWING ---
            
            # Title Bar
            title_text = f"{data['spec_name']} - P. {data['page']}/{self.specializations[data['active_spec']]['pages']}"
            cv2.putText(frame, title_text, (50, 120), 
                       font, 1.0, (255, 255, 0), 2)
            
            # Content Box (80% of screen, centered)
            box_w_norm, box_h_norm = 0.85, 0.70
            bx_norm, by_norm = 0.075, 0.15 
            
            x1 = int(bx_norm * w)
            y1 = int(by_norm * h)
            x2 = int((bx_norm + box_w_norm) * w)
            y2 = int((by_norm + box_h_norm) * h)
            
            # Draw content background
            cv2.rectangle(frame, (x1, y1), (x2, y2), (20, 20, 50), -1)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 1)

            # Draw Page Text (Handle multi-line text)
            line_height = 30
            y_offset = y1 + 50
            for line in data["page_text"].split('\n'):
                # Trim the line to fit the box width
                
                # Simple single line drawing. If text is too long, it will be clipped.
                cv2.putText(frame, line.strip(), (x1 + 30, y_offset), 
                           font, 0.7, (200, 200, 255), 1, cv2.LINE_AA)
                y_offset += line_height
                
            # Swipe Hint
            if data['page'] > 1:
                cv2.putText(frame, "<- SWIPE RIGHT (Inapoi la pagina/meniu)", (x1, y2 + 40), 
                           font, 0.6, (255, 255, 255), 1)
            if data['page'] < self.specializations[data['active_spec']]['pages']:
                cv2.putText(frame, "SWIPE LEFT (Pagina urmatoare) ->", (x2 - 350, y2 + 40), 
                           font, 0.6, (255, 255, 255), 1)


        return frame