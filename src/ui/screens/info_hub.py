# src/ui/screens/info_hub.py
import os
import cv2
import numpy as np
from .info_detail import get_page_text

# ============================================
# Helper pentru text wrapping
# ============================================
def wrap_text(text, font, font_scale, thickness, max_width):
    words = text.split(' ')
    wrapped = []
    current_line = ""

    for word in words:
        test_line = current_line + (' ' if current_line else '') + word
        (w, h), _ = cv2.getTextSize(test_line, font, font_scale, thickness)

        if w <= max_width:
            current_line = test_line
        else:
            wrapped.append(current_line)
            current_line = word

    if current_line:
        wrapped.append(current_line)

    return wrapped

# ============================================
# Helper pentru text cu umbra
# ============================================
def draw_text_with_shadow(frame, text, x, y, font, scale, thickness):
    cv2.putText(frame, text, (x + 2, y + 2), font, scale, (0, 0, 0), thickness, cv2.LINE_AA)
    cv2.putText(frame, text, (x, y), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)

# ============================================
# Helper pentru desenare cutie transparenta
# ============================================
def draw_transparent_box(frame, x1, y1, x2, y2, color=(200, 50, 50), alpha=0.7):
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 1)

# ============================================
# Helper pentru text transparent
# ============================================
def draw_transparent_text(frame, text, x, y, font, scale, color=(200, 50, 50), thickness=2, alpha=0.7):
    overlay = frame.copy()
    cv2.putText(overlay, text, (x, y), font, scale, color, thickness, cv2.LINE_AA)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

# ============================================

class InfoHub:
    def __init__(self):
        # --- INCARCARE LOGO ---
        self.logo_path = "assets/images/logo_ugal.jpeg"
        self.logo_img = None
        
        if os.path.exists(self.logo_path):
            try:
                temp_img = cv2.imread(self.logo_path, cv2.IMREAD_UNCHANGED)
                if temp_img is not None:
                    target_h = 100
                    h_orig, w_orig = temp_img.shape[:2]
                    aspect = w_orig / h_orig
                    target_w = int(target_h * aspect)
                    self.logo_img = cv2.resize(temp_img, (target_w, target_h))
                    print(f"InfoHub: Logo loaded ({target_w}x{target_h})")
                else:
                    print(f"InfoHub WARNING: Failed to load image at {self.logo_path}")
            except Exception as e:
                print(f"InfoHub Error: {e}")
        # ----------------------

        self.specializations = {
            "AIA": {"name": "Automatica, Informatica Aplicata si Sisteme Inteligente", "pages": 4},
            "CTI": {"name": "Calculatoare si Tehnologia Informatiei", "pages": 4},
            "IE": {"name": "Inginerie Electrica", "pages": 4},
            "IETTI": {"name": "Inginerie electronica, telecomunicatii si tehnologii informationale", "pages": 4}
        }
        
        self.buttons = {
            "AIA": (0.1, 0.2, 0.35, 0.3),  
            "CTI": (0.55, 0.2, 0.35, 0.3), 
            "IE": (0.1, 0.6, 0.35, 0.3),  
            "IETTI": (0.55, 0.6, 0.35, 0.3) 
        }
        
        self.back_btn_rect = (0.02, 0.02, 0.12, 0.08) 

        # --- BUTON EXIT (Jos Mijloc in Detail Mode) ---
        # Centrat orizontal (aprox 42.5% -> 57.5%), sub chenarul textului (care se termina la 0.85)
        # Format: (x, y, w, h)
        self.exit_btn_rect = (0.425, 0.88, 0.15, 0.08) 
        
        self.active_spec = None
        self.current_page = 0
        self.dwell_timer = 0
        self.hovered_btn = None
        
        self.DWELL_THRESHOLD = 22       
        self.BACK_DWELL_THRESHOLD = 11  

    def update(self, cursor_x, cursor_y, gesture):
        if self.active_spec is None:
            return self._update_selection_mode(cursor_x, cursor_y, gesture)
        else:
            return self._update_detail_mode(cursor_x, cursor_y, gesture)

    def _update_selection_mode(self, x, y, gesture):
        hit = None
        
        bbx, bby, bbw, bbh = self.back_btn_rect
        if bbx < x < bbx + bbw and bby < y < bby + bbh:
            hit = "BACK_BTN"
        else:
            for key, (bx, by, bw, bh) in self.buttons.items():
                if bx < x < bx+bw and by < y < by+bh:
                    hit = key
                    break
        
        if hit and hit == self.hovered_btn:
            self.dwell_timer += 1
            current_threshold = self.BACK_DWELL_THRESHOLD if hit == "BACK_BTN" else self.DWELL_THRESHOLD
            
            if self.dwell_timer > current_threshold: 
                self.dwell_timer = 0
                
                if hit == "BACK_BTN":
                    return "BACK_TO_MENU"
                else:
                    self.active_spec = hit
                    self.current_page = 0
                    return "OPEN_DETAIL"
        else:
            self.hovered_btn = hit
            self.dwell_timer = 0
            
        return None

    def _update_detail_mode(self, x, y, gesture):
        # 1. Verificam Butonul EXIT
        ebx, eby, ebw, ebh = self.exit_btn_rect
        
        # Daca cursorul este pe butonul EXIT
        if ebx < x < ebx + ebw and eby < y < eby + ebh:
            if self.hovered_btn == "EXIT_BTN":
                self.dwell_timer += 1
                # Folosim pragul rapid (11 cadre) sau normal (22) - aici am pus rapid
                if self.dwell_timer > self.BACK_DWELL_THRESHOLD:
                    self.dwell_timer = 0
                    self.hovered_btn = None
                    # ACTIUNE: Iesim la lista de specializari
                    self.active_spec = None
                    return None
            else:
                self.hovered_btn = "EXIT_BTN"
                self.dwell_timer = 0
        else:
            # Daca nu suntem pe buton, resetam timer-ul DOAR daca eram pe el inainte
            if self.hovered_btn == "EXIT_BTN":
                self.hovered_btn = None
                self.dwell_timer = 0

        # 2. Gestionare Swipe (Navigare Pagini)
        if not gesture:
            return None
            
        max_pages = self.specializations[self.active_spec]["pages"]
        
        # SWIPE DREAPTA -> NEXT PAGE
        if gesture == "SWIPE_RIGHT":
            if self.current_page < max_pages - 1:
                self.current_page += 1
                return "NEXT_PAGE"
                
        # SWIPE STANGA -> PREV PAGE (sau EXIT daca e prima pag)
        elif gesture == "SWIPE_LEFT":
            if self.current_page > 0:
                self.current_page -= 1
                return "PREV_PAGE"
            else:
                # Optional: Swipe Stanga pe prima pagina iese si el
                self.active_spec = None
                return None
                
        return None

    def get_ui_data(self):
        spec_name = None
        page_text = ""
        if self.active_spec is not None:
            spec = self.specializations.get(self.active_spec, {})
            spec_name = spec.get("name", self.active_spec)
            page_text = get_page_text(self.active_spec, self.current_page)

        # Determinam pragul in functie de buton
        if self.hovered_btn == "BACK_BTN" or self.hovered_btn == "EXIT_BTN":
            threshold = self.BACK_DWELL_THRESHOLD
        else:
            threshold = self.DWELL_THRESHOLD
            
        progress_val = min(self.dwell_timer / float(threshold), 1.0)

        return {
            "mode": "SELECTION" if self.active_spec is None else "DETAIL",
            "active_spec": self.active_spec,
            "spec_name": spec_name,
            "page": self.current_page + 1, 
            "buttons": self.buttons,
            "back_btn": self.back_btn_rect,
            "exit_btn": self.exit_btn_rect,
            "hovered": self.hovered_btn,
            "progress": progress_val,
            "page_text": page_text
        }
    
    def draw(self, frame):
        h, w, _ = frame.shape
        data = self.get_ui_data()
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # --- LOGO ---
        if self.logo_img is not None:
            lh, lw = self.logo_img.shape[:2]
            x_offset = (w - lw) // 2
            y_offset = 20 

            if y_offset + lh < h and x_offset + lw < w and x_offset >= 0:
                roi = frame[y_offset:y_offset+lh, x_offset:x_offset+lw]
                if self.logo_img.shape[2] == 4:
                    b, g, r, a = cv2.split(self.logo_img)
                    overlay_color = cv2.merge((b, g, r))
                    mask = a / 255.0
                    mask_inv = 1.0 - mask
                    for c in range(0, 3):
                        roi[:, :, c] = (mask * overlay_color[:, :, c] + mask_inv * roi[:, :, c])
                else:
                    frame[y_offset:y_offset+lh, x_offset:x_offset+lw] = self.logo_img
        else:
            text_w, _ = cv2.getTextSize("INFO HUB", font, 1.5, 3)[0]
            cv2.putText(frame, "INFO HUB", ((w - text_w)//2, 50), font, 1.5, (255, 255, 255), 3)
        # ------------

        if data["mode"] == "SELECTION":
            # --- SELECTION MODE ---
            
            # Buton BACK
            bbx, bby, bbw, bbh = data["back_btn"]
            x1 = int(bbx * w)
            y1 = int(bby * h)
            x2 = int((bbx + bbw) * w)
            y2 = int((bby + bbh) * h)
            
            is_back_hovered = (data["hovered"] == "BACK_BTN")
            back_color = (50, 50, 200) if is_back_hovered else (30, 30, 150)
            
            draw_transparent_box(frame, x1, y1, x2, y2, color=back_color, alpha=0.7)
            
            if is_back_hovered and data["progress"] > 0:
                bar_w = int((x2 - x1) * data["progress"])
                cv2.rectangle(frame, (x1, y2 - 5), (x1 + bar_w, y2), (0, 255, 0), -1)
                
            text_size = cv2.getTextSize("< Back", font, 0.7, 2)[0]
            tx = x1 + (x2 - x1 - text_size[0]) // 2
            ty = y1 + (y2 - y1 + text_size[1]) // 2
            cv2.putText(frame, "< Back", (tx, ty), font, 0.7, (255, 255, 255), 2)

            # Titlu
            draw_transparent_text(frame, "Alege specializarea:", 65, 160, 
                                  font, 1.0, color=(200, 50, 50), alpha=0.7)

            # Butoane Specializari
            for key, (bx_norm, by_norm, bw_norm, bh_norm) in self.buttons.items():
                x1 = int(bx_norm * w)
                y1 = int(by_norm * h)
                x2 = int((bx_norm + bw_norm) * w)
                y2 = int((by_norm + bh_norm) * h)
                
                is_hovered = (key == data["hovered"])
                base_color = (200, 50, 50) 
                if is_hovered:
                    base_color = (255, 100, 100) 
                
                draw_transparent_box(frame, x1, y1, x2, y2, color=base_color, alpha=0.7)
                
                if is_hovered and data["progress"] > 0:
                    bar_w = int((x2 - x1) * data["progress"])
                    cv2.rectangle(frame, (x1, y2 - 10), (x1 + bar_w, y2), (0, 255, 0), -1)

                text_content = self.specializations[key]["name"].split(',')[0]
                text_size = cv2.getTextSize(text_content, font, 0.8, 2)[0]
                tx = x1 + (x2 - x1 - text_size[0]) // 2
                ty = y1 + (y2 - y1 + text_size[1]) // 2
                
                cv2.putText(frame, text_content, (tx, ty), font, 0.8, (255, 255, 255), 2)

        elif data["mode"] == "DETAIL":
            # --- DETAIL MODE ---
            
            title_text = f"{data['spec_name']} - P. {data['page']}/{self.specializations[data['active_spec']]['pages']}"
            
            draw_text_with_shadow(frame, title_text, 50, 160, font, 1.0, 2)
            cv2.putText(frame, title_text, (50, 160), font, 1.0, (200, 50, 50), 2, cv2.LINE_AA)
            
            box_w_norm, box_h_norm = 0.85, 0.65
            bx_norm, by_norm = 0.075, 0.20 
            
            x1 = int(bx_norm * w)
            y1 = int(by_norm * h)
            x2 = int((bx_norm + box_w_norm) * w)
            y2 = int((by_norm + box_h_norm) * h)
            
            draw_transparent_box(frame, x1, y1, x2, y2, color=(200, 50, 50), alpha=0.7)

            line_height = 40 
            y_offset = y1 + 50
            max_text_width = (x2 - x1) - 60
            text_scale = 0.9

            for raw_line in data["page_text"].split('\n'):
             wrapped_lines = wrap_text(raw_line.strip(), font, text_scale, 1, max_text_width)
             for line in wrapped_lines:
               cv2.putText(frame, line, (x1 + 30, y_offset),
                           font, text_scale, (255, 255, 255), 2, cv2.LINE_AA)
               y_offset += line_height

            # --- BUTON EXIT (NOU) ---
            ebx, eby, ebw, ebh = data["exit_btn"]
            ex1 = int(ebx * w)
            ey1 = int(eby * h)
            ex2 = int((ebx + ebw) * w)
            ey2 = int((eby + ebh) * h)

            is_exit_hovered = (data["hovered"] == "EXIT_BTN")
            # Rosu pentru Exit (50, 50, 200) -> BGR
            exit_color = (50, 50, 255) if is_exit_hovered else (30, 30, 200)

            # Desenam cutie rosie transparenta
            draw_transparent_box(frame, ex1, ey1, ex2, ey2, color=exit_color, alpha=0.8)

            # Bara de progres pentru Exit
            if is_exit_hovered and data["progress"] > 0:
                bar_w = int((ex2 - ex1) * data["progress"])
                cv2.rectangle(frame, (ex1, ey2 - 5), (ex1 + bar_w, ey2), (0, 255, 0), -1)

            # Text "EXIT"
            text_size = cv2.getTextSize("EXIT", font, 0.8, 2)[0]
            tx = ex1 + (ex2 - ex1 - text_size[0]) // 2
            ty = ey1 + (ey2 - ey1 + text_size[1]) // 2
            cv2.putText(frame, "EXIT", (tx, ty), font, 0.8, (255, 255, 255), 2)

            # --- SWIPE HINTS (Ajustate) ---
            # Le mutam stanga si dreapta, ca sa nu se suprapuna cu butonul din mijloc
            
            # Back/Prev Hint (Stanga)
            back_text = "<- SWIPE LEFT (Inapoi)" if data['page'] > 1 else "<- SWIPE LEFT (Lista)"
            draw_text_with_shadow(frame, back_text, x1, ey1 + 30, font, 0.8, 2)

            if data['page'] < self.specializations[data['active_spec']]['pages']:
                # Next Hint (Dreapta)
                next_text = "SWIPE RIGHT (Inainte) ->"
                (tw, _), _ = cv2.getTextSize(next_text, font, 0.8, 2)
                draw_text_with_shadow(frame, next_text, x2 - tw, ey1 + 30, font, 0.8, 2)

        return frame