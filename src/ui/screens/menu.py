import cv2
import time
import numpy as np

class MenuController:
    def __init__(self):
        # Normalized Layout: (x, y, width, height)
        # We put them somewhat centrally
        self.layout = {
            "INFO": (0.1, 0.4, 0.25, 0.3),   # Left
            "PLAY": (0.375, 0.4, 0.25, 0.3), # Center
            "MAP":  (0.65, 0.4, 0.25, 0.3)   # Right
        }
        
        self.state = {
            "hovered": None,
            "start_hover_time": 0,
            "progress": 0.0,
            "selection_threshold": 2.0  # Seconds to trigger
        }

    def get_layout(self):
        return self.layout

    def get_state(self):
        return self.state

    def update(self, cursor_x, cursor_y):
        """
        Checks if cursor is over a button.
        Returns the button name if selected (after holding), else None.
        """
        currently_hovered = None

        # Check collision with all buttons
        for name, (bx, by, bw, bh) in self.layout.items():
            if bx < cursor_x < bx + bw and by < cursor_y < by + bh:
                currently_hovered = name
                break
        
        # State Machine for Hover Logic
        if currently_hovered != self.state["hovered"]:
            # New hover target or lost target
            self.state["hovered"] = currently_hovered
            self.state["start_hover_time"] = time.time()
            self.state["progress"] = 0.0
        
        # If hovering, update progress
        if currently_hovered:
            elapsed = time.time() - self.state["start_hover_time"]
            self.state["progress"] = min(elapsed / self.state["selection_threshold"], 1.0)
            
            if elapsed >= self.state["selection_threshold"]:
                # Reset after selection so it doesn't auto-trigger again immediately
                self.state["hovered"] = None
                self.state["progress"] = 0.0
                return currently_hovered
                
        return None

    def draw(self, frame):
        """
        Draws the menu UI onto the frame.
        """
        h, w, _ = frame.shape
        
        # 1. Draw Title Header
        # Dark strip at the top
        cv2.rectangle(frame, (0, 0), (w, 120), (15, 15, 15), -1)
        # Accent Line
        cv2.line(frame, (0, 120), (w, 120), (0, 255, 255), 2)
        
        cv2.putText(frame, "MAIN MENU", (50, 80), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
        cv2.putText(frame, "Hover over an item to select it", (w - 450, 80), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 1)

        # 2. Draw Buttons
        for name, (bx, by, bw, bh) in self.layout.items():
            x1, y1 = int(bx * w), int(by * h)
            x2, y2 = int((bx + bw) * w), int((by + bh) * h)
            
            is_hovered = (self.state["hovered"] == name)
            
            # --- Visual Styles ---
            if is_hovered:
                # Hover: Bright border, slightly lighter fill
                bg_color = (60, 60, 60)
                border_color = (0, 255, 255) # Cyan/Yellow
                thickness = 3
                font_scale = 1.1
            else:
                # Normal: Dark fill, gray border
                bg_color = (30, 30, 30)
                border_color = (100, 100, 100)
                thickness = 2
                font_scale = 1.0

            # Draw Card Background
            overlay = frame.copy()
            cv2.rectangle(overlay, (x1, y1), (x2, y2), bg_color, -1)
            cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
            
            # Draw Border
            cv2.rectangle(frame, (x1, y1), (x2, y2), border_color, thickness)
            
            # Draw Progress Bar (if hovered)
            if is_hovered:
                bar_height = 15
                bar_width = int((x2 - x1) * self.state["progress"])
                # Black background for bar
                cv2.rectangle(frame, (x1, y2 - bar_height), (x2, y2), (0, 0, 0), -1)
                # Green fill
                cv2.rectangle(frame, (x1, y2 - bar_height), (x1 + bar_width, y2), (0, 255, 0), -1)

            # Draw Text (Centered)
            text_size = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)[0]
            tx = x1 + (x2 - x1 - text_size[0]) // 2
            ty = y1 + (y2 - y1 + text_size[1]) // 2
            
            text_color = (255, 255, 255) if is_hovered else (200, 200, 200)
            cv2.putText(frame, name, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, 2)
            
            # Subtitles
            sub = ""
            if name == "INFO": sub = "Faculties & Specs"
            elif name == "PLAY": sub = "Quiz Game"
            elif name == "MAP": sub = "Campus Map"
            
            if sub:
                sub_size = cv2.getTextSize(sub, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)[0]
                stx = x1 + (x2 - x1 - sub_size[0]) // 2
                cv2.putText(frame, sub, (stx, y2 + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)

        return frame