import cv2
import time
import numpy as np

# Import components
from src.vision.gesture_engine import GestureEngine
from src.ui.screens.screensaver import Screensaver
from src.ui.screens.menu import MenuController
from src.ui.screens.game import QuizGame
from src.ui.screens.info_hub import InfoHub

# --- CONFIGURATION ---
STATE_SAVER = "SAVER"
STATE_MENU  = "MENU"
STATE_INFO  = "INFO"
STATE_GAME  = "GAME"
STATE_MAP   = "MAP"

IDLE_TIMEOUT = 10.0

def get_screen_resolution():
    return 1920, 1080

def main():
    SCREEN_W, SCREEN_H = get_screen_resolution()
    
    cap = cv2.VideoCapture(0)
    
    window_name = "University AI Kiosk"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # Initialize Components
    engine = GestureEngine()
    saver = Screensaver()
    menu = MenuController()
    game = QuizGame()
    info = InfoHub()

    current_state = STATE_SAVER
    last_activity_time = time.time()
    
    # Optimization: Only check face every few frames to save CPU
    frame_count = 0 

    print("Kiosk Started with FACE + HAND Presence Detection.")
    print("Press 'q' to quit.")

    while True:
        success, frame = cap.read()
        if not success: break
        
        frame_count += 1
        raw_frame = cv2.flip(frame, 1)
        
        # --- A. CHECK PRESENCE (To keep app awake) ---
        user_is_active = False

        # 1. Check Hand Gesture (Always check this fast)
        gesture_data = engine.process_frame(raw_frame)
        if gesture_data["cursor_detected"]:
            user_is_active = True
        
        # 2. Check Face Presence (Only if hand not found, check every 5th frame)
        # This prevents the app from resetting if you are just looking at it
        if not user_is_active and current_state != STATE_SAVER:
            if frame_count % 5 == 0: 
                if saver.is_face_present(raw_frame):
                    user_is_active = True
        
        # Reset timeout if active
        if user_is_active:
            last_activity_time = time.time()

        # --- B. RESIZE FOR DISPLAY ---
        display_frame = cv2.resize(raw_frame, (SCREEN_W, SCREEN_H), interpolation=cv2.INTER_LINEAR)
        h, w, _ = display_frame.shape

        # --- C. LOGIC & DRAWING ---
        
        if current_state == STATE_SAVER:
            status = saver.update(raw_frame)
            if status == "WAKE_UP":
                current_state = STATE_MENU
                last_activity_time = time.time()
            display_frame = draw_screensaver_ui(display_frame, saver.get_ui_data())

        elif current_state == STATE_MENU:
            if time.time() - last_activity_time > IDLE_TIMEOUT:
                current_state = STATE_SAVER
            
            if gesture_data["cursor_detected"]:
                selection = menu.update(gesture_data["x"], gesture_data["y"])
                if selection == "INFO":
                    current_state = STATE_INFO
                    info = InfoHub()
                elif selection == "PLAY":
                    current_state = STATE_GAME
                    game = QuizGame()
                elif selection == "MAP":
                    pass 
            
            display_frame = draw_menu_ui(display_frame, menu, gesture_data)

        elif current_state == STATE_GAME:
            if time.time() - last_activity_time > IDLE_TIMEOUT:
                current_state = STATE_SAVER

            if gesture_data["cursor_detected"]:
                game.update(gesture_data["x"], gesture_data["y"])
                
            game_data = game.get_current_data()
            if game_data["game_over"]:
                current_state = STATE_MENU
                
            display_frame = draw_game_ui(display_frame, game_data, gesture_data)

        elif current_state == STATE_INFO:
            if time.time() - last_activity_time > IDLE_TIMEOUT:
                current_state = STATE_SAVER

            if gesture_data["cursor_detected"]:
                result = info.update(gesture_data["x"], gesture_data["y"], gesture_data["gesture"])
                if result == "BACK_TO_MENU":
                    current_state = STATE_MENU

            display_frame = draw_info_ui(display_frame, info.get_ui_data(), gesture_data)

        # --- D. DRAW CURSOR ---
        if current_state != STATE_SAVER and gesture_data["cursor_detected"]:
            cx, cy = int(gesture_data["x"] * w), int(gesture_data["y"] * h)
            color = (0, 255, 255) 
            cv2.line(display_frame, (cx - 20, cy), (cx + 20, cy), color, 2)
            cv2.line(display_frame, (cx, cy - 20), (cx, cy + 20), color, 2)
            cv2.circle(display_frame, (cx, cy), 15, color, 2)
            cv2.circle(display_frame, (cx, cy), 3, (255, 255, 255), -1)

        cv2.imshow(window_name, display_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

# ==========================================
#      VISUAL RENDERING FUNCTIONS
# ==========================================

def draw_screensaver_ui(frame, data):
    h, w, _ = frame.shape
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (20, 10, 40), -1) 
    cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)
    
    for p in data["particles"]:
        x, y, speed, color = p
        draw_x = int(x * (w / 640)) if w > 640 else x
        draw_y = int(y * (h / 480)) if h > 480 else y
        cv2.circle(frame, (draw_x, draw_y), 2, color, -1)
        cv2.line(frame, (draw_x, draw_y), (draw_x, draw_y-10), color, 1)

    pulse = data["pulse"]
    glow_intensity = int(20 * pulse)
    center_y = h // 2
    
    cv2.rectangle(frame, (100 - glow_intensity, center_y - 80 - glow_intensity), 
                         (w - 100 + glow_intensity, center_y + 80 + glow_intensity), 
                         (255, 100, 0), 1) 
    cv2.rectangle(frame, (100, center_y - 80), (w - 100, center_y + 80), (0, 0, 0), -1)
    
    cv2.putText(frame, "FACULTY OF AUTOMATION,", (w//2 - 250, center_y - 20), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(frame, "COMPUTERS & ELECTRONICS", (w//2 - 260, center_y + 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3) 

    if int(time.time() * 2) % 2 == 0: 
        cv2.putText(frame, "[ STEP FORWARD TO START ]", (w//2 - 180, h - 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    if data["waking_progress"] > 0:
        bw = int(w * data["waking_progress"])
        cv2.rectangle(frame, (0, h-10), (w, h), (50, 50, 50), -1)
        cv2.rectangle(frame, (0, h-10), (bw, h), (255, 200, 0), -1)
        cv2.putText(frame, "INITIALIZING SYSTEM...", (20, h - 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2)
    return frame

def draw_menu_ui(frame, menu, data):
    h, w, _ = frame.shape
    layout = menu.get_layout()
    state = menu.get_state()
    
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (20, 20, 40), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    cv2.rectangle(frame, (0, 0), (w, 120), (0, 0, 0), -1) 
    cv2.line(frame, (0, 120), (w, 120), (0, 255, 255), 2) 
    
    cv2.putText(frame, "UNIVERSITY TOUCHLESS KIOSK", (50, 80), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
    cv2.putText(frame, "Hover to Select", (w - 300, 80), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 1)

    for name, (bx, by, bw, bh) in layout.items():
        x1, y1 = int(bx * w), int(by * h)
        x2, y2 = int((bx + bw) * w), int((by + bh) * h)
        
        BASE_COLOR = (50, 50, 50)
        HOVER_COLOR = (255, 100, 0)
        TEXT_COLOR = (200, 200, 200)
        
        is_hovered = (state["hovered"] == name)
        
        card_overlay = frame.copy()
        bg_color = HOVER_COLOR if is_hovered else BASE_COLOR
        opacity = 0.6 if is_hovered else 0.4
        
        cv2.rectangle(card_overlay, (x1, y1), (x2, y2), bg_color, -1)
        cv2.addWeighted(card_overlay, opacity, frame, 1 - opacity, 0, frame)
        
        if is_hovered:
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 3)
            cv2.rectangle(frame, (x1-5, y1-5), (x2+5, y2+5), HOVER_COLOR, 2)
            TEXT_COLOR = (255, 255, 255)
        else:
            cv2.rectangle(frame, (x1, y1), (x2, y2), (100, 100, 100), 2)

        if is_hovered:
            bar_height = 10
            bar_width = int((x2 - x1) * state["progress"])
            cv2.rectangle(frame, (x1, y2 - bar_height), (x2, y2), (0, 0, 0), -1)
            cv2.rectangle(frame, (x1, y2 - bar_height), (x1 + bar_width, y2), (0, 255, 0), -1)

        font_scale = 1.2 if is_hovered else 1.0
        thickness = 3 if is_hovered else 2
        text_size = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
        tx = x1 + (x2 - x1 - text_size[0]) // 2
        ty = y1 + (y2 - y1 + text_size[1]) // 2
        cv2.putText(frame, name, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, TEXT_COLOR, thickness)
        
        desc = ""
        if name == "INFO": desc = "Faculties"
        elif name == "PLAY": desc = "Quiz Game"
        elif name == "MAP": desc = "Campus Map"
        cv2.putText(frame, desc, (x1 + 20, y2 - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)
    return frame

def draw_game_ui(frame, game_data, gesture_data):
    h, w, _ = frame.shape
    if game_data["game_over"]:
        cv2.putText(frame, "GAME OVER", (w//2 - 150, h//2), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4)
        cv2.putText(frame, f"Score: {game_data.get('score', 0)}", (w//2 - 100, h//2 + 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
        return frame

    cv2.putText(frame, game_data["question"], (50, h//2), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    positions = {"A": (50, 100), "B": (w-300, 100), "C": (50, h-100), "D": (w-300, h-100)}
    for key, text in game_data["answers"].items():
        color = (255, 255, 255)
        if game_data["selection"] == key:
            color = (255, 0, 0)
            bx, by = positions[key]
            bar_w = int(200 * game_data["progress"])
            cv2.rectangle(frame, (bx, by+15), (bx+bar_w, by+25), (0, 255, 0), -1)
        cv2.putText(frame, f"{key}: {text}", positions[key], cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    return frame

def draw_info_ui(frame, data, gesture_data):
    h, w, _ = frame.shape
    if data["mode"] == "SELECTION":
        cv2.putText(frame, "SELECT FACULTY", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
        for key, (bx, by, bw, bh) in data["buttons"].items():
            x1, y1 = int(bx*w), int(by*h)
            x2, y2 = int((bx+bw)*w), int((by+bh)*h)
            color = (100, 100, 100)
            if data["hovered"] == key:
                color = (255, 100, 0)
                bar_w = int((x2-x1) * data["progress"])
                cv2.rectangle(frame, (x1, y2-15), (x1+bar_w, y2), (0, 255, 0), -1)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, key, (x1+20, y1+50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    else:
        cv2.rectangle(frame, (50, 50), (w-50, h-50), (255, 100, 0), 2)
        cv2.putText(frame, f"{data['active_spec']} - PAGE {data['page']}", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, "Swipe LEFT for next page / RIGHT for back", (100, h-100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    return frame

if __name__ == "__main__":
    main()