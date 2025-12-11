import cv2
import time
import numpy as np
import math
import os
import random # Imported for random animation start times

class MenuController:
    def __init__(self):
        # Layout: Dictionary of "Key": (Center_X_Norm, Center_Y_Norm, Radius_Norm_Fraction_of_Width)
        self.layout = {
            "INFO": (0.2, 0.3, 0.12),    
            "PLAY": (0.8, 0.3, 0.12),    
            "MAP":  (0.5, 0.75, 0.12)    
        }
        
        self.state = {
            "hovered": None,
            "start_hover_time": 0,
            "progress": 0.0,
            "selection_threshold": 2.0
        }

        # --- ANIMATION SETUP ---
        # Generate a random "phase" (0 to 2pi) for each button.
        # This ensures they don't all bob up and down at the exact same time.
        self.anim_offsets = {k: random.uniform(0, 6.28) for k in self.layout.keys()}

        # --- ASSET LOADING ---
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
        sprite_path = os.path.join(project_root, "assets", "images", "pixel_bubble.png")
        
        # Load with Alpha Channel (Transparency)
        self.bubble_sprite = cv2.imread(sprite_path, cv2.IMREAD_UNCHANGED)
        
        self.asset_loaded = True
        if self.bubble_sprite is None:
            print(f"ERROR: Could not load image at {sprite_path}")
            self.asset_loaded = False
            self.bubble_sprite = np.zeros((100, 100, 4), dtype=np.uint8)
            cv2.circle(self.bubble_sprite, (50,50), 45, (50, 50, 50, 255), -1)

    def get_layout(self):
        return self.layout

    def update(self, cursor_x, cursor_y):
        """
        Checks collision using Circular Distance logic.
        """
        currently_hovered = None
        aspect_ratio = 1.77 
        
        for name, (cx, cy, r) in self.layout.items():
            dx = cursor_x - cx
            dy = (cursor_y - cy) / aspect_ratio 
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist < r:
                currently_hovered = name
                break
        
        # State Machine
        if currently_hovered != self.state["hovered"]:
            self.state["hovered"] = currently_hovered
            self.state["start_hover_time"] = time.time()
            self.state["progress"] = 0.0
        
        if currently_hovered:
            elapsed = time.time() - self.state["start_hover_time"]
            self.state["progress"] = min(elapsed / self.state["selection_threshold"], 1.0)
            
            if elapsed >= self.state["selection_threshold"]:
                self.state["hovered"] = None
                self.state["progress"] = 0.0
                return currently_hovered
                
        return None

    def overlay_transparent(self, background, overlay, x, y):
        bg_h, bg_w, _ = background.shape
        ov_h, ov_w, ov_c = overlay.shape

        if x >= bg_w or y >= bg_h or x + ov_w < 0 or y + ov_h < 0: 
            return background

        ov_x_start = max(0, x)
        ov_y_start = max(0, y)
        bg_x_start = max(0, x)
        bg_y_start = max(0, y)
        
        ov_x_end = min(x + ov_w, bg_w)
        ov_y_end = min(y + ov_h, bg_h)
        bg_x_end = min(x + ov_w, bg_w)
        bg_y_end = min(y + ov_h, bg_h)
        
        roi_w = bg_x_end - bg_x_start
        roi_h = bg_y_end - bg_y_start
        
        if roi_w <= 0 or roi_h <=0: return background

        roi = background[bg_y_start:bg_y_end, bg_x_start:bg_x_end]
        
        ov_crop_x_start = bg_x_start - x
        ov_crop_y_start = bg_y_start - y
        overlay_crop = overlay[ov_crop_y_start:ov_crop_y_start+roi_h, ov_crop_x_start:ov_crop_x_start+roi_w]

        if overlay_crop.shape[2] == 4:
            alpha_channel = overlay_crop[:, :, 3] / 255.0
            overlay_bgr = overlay_crop[:, :, :3]

            for c in range(3):
                roi[:, :, c] = (alpha_channel * overlay_bgr[:, :, c] + 
                                (1.0 - alpha_channel) * roi[:, :, c])
        else:
            roi[:] = overlay_crop

        background[bg_y_start:bg_y_end, bg_x_start:bg_x_end] = roi
        return background

    def draw(self, frame):
        h, w, _ = frame.shape
        current_time = time.time()
        
        # Title
        cv2.putText(frame, "MAIN MENU", (50, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)

        # Draw Buttons
        for name, (cx_norm, cy_norm, r_norm) in self.layout.items():
            
            is_hovered = (self.state["hovered"] == name)
            
            # --- ANIMATION MATH ---
            # 1. Floating Effect (Idle)
            # Offset Y by a Sine wave. 
            # Amplitude = 15 pixels (height of float)
            # Speed = 2.5
            float_offset_y = 0
            scale_factor = 1.0

            if not is_hovered:
                # Normal floating when not touched
                float_offset_y = math.sin(current_time * 2.5 + self.anim_offsets[name]) * 15
            else:
                # 2. Pulsing Effect (Hover)
                # When hovered, stop floating and pulse size instead
                # Pulsing between 1.05x and 1.15x size
                scale_factor = 1.1 + 0.05 * math.sin(current_time * 8) 

            # Calculate actual positions
            center_x = int(cx_norm * w)
            center_y = int(cy_norm * h + float_offset_y) # Apply the float
            
            # Size calculations with Scale Factor
            target_diameter = int(r_norm * w * 2 * scale_factor)
            radius_px = target_diameter // 2
            
            # Resize sprite
            # Use INTER_NEAREST to keep that crisp pixel art look
            resized_bubble = cv2.resize(self.bubble_sprite, (target_diameter, target_diameter), interpolation=cv2.INTER_NEAREST)
            
            top_left_x = center_x - radius_px
            top_left_y = center_y - radius_px

            # Draw Bubble
            frame = self.overlay_transparent(frame, resized_bubble, top_left_x, top_left_y)

            # Draw Selection Ring
            if is_hovered and self.state["progress"] > 0:
                thickness = 8 
                angle = 360 * self.state["progress"]
                # Ring also follows the scale and float
                cv2.ellipse(frame, (center_x, center_y), (radius_px + thickness//2, radius_px + thickness//2),
                            -90, 0, angle, (255, 255, 0), thickness, lineType=cv2.LINE_4)

            # Draw Text
            font_scale = 1.0 * scale_factor # Text scales with bubble
            thickness = 2
            text_size = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
            tx = center_x - text_size[0] // 2
            ty = center_y + text_size[1] // 2
            
            # Outline (Black)
            cv2.putText(frame, name, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0,0,0), thickness+3, lineType=cv2.LINE_4)
            # Fill (White/Cyan)
            text_color = (255, 255, 255)
            if is_hovered: text_color = (200, 255, 255) 
            cv2.putText(frame, name, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, thickness, lineType=cv2.LINE_4)

        return frame