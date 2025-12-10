import cv2
import time
import os
import numpy as np

# Import components
from src.vision.gesture_engine import GestureEngine
from src.ui.screens.screensaver import Screensaver
from src.ui.screens.menu import MenuController
# Aici am schimbat importul pentru a folosi fisierul tau redenumit
from src.ui.screens.quiz_game import QuizGame 
from src.ui.screens.info_hub import InfoHub

# --- CONFIGURATION ---
STATE_SAVER = "SAVER"
STATE_MENU  = "MENU"
STATE_INFO  = "INFO"
STATE_GAME  = "GAME"
STATE_MAP   = "MAP"

IDLE_TIMEOUT = 20.0 # Am marit putin timeout-ul pentru demo

def get_screen_resolution():
    # Poti modifica aici daca vrei alta rezolutie fixa
    return 1280, 720

def main():
    SCREEN_W, SCREEN_H = get_screen_resolution()
    
    cap = cv2.VideoCapture(0)
    window_name = "University AI Kiosk"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    # Daca vrei fullscreen, decomenteaza linia de mai jos:
    # cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # --- LOAD LOGO ---
    logo_path = "assets/images/logo_ugal.jpeg"
    logo_img = None
    if os.path.exists(logo_path):
        logo_img = cv2.imread(logo_path, cv2.IMREAD_UNCHANGED)
        if logo_img is not None:
            # Resize logic (Make it 200px wide)
            target_width = 200
            h, w = logo_img.shape[:2]
            aspect = h / w
            logo_img = cv2.resize(logo_img, (target_width, int(target_width * aspect)))

    # Initialize Components
    engine = GestureEngine()
    saver = Screensaver()
    menu = MenuController()
    game = QuizGame()
    info = InfoHub()

    current_state = STATE_SAVER
    last_activity_time = time.time()
    frame_count = 0 

    print("Kiosk Started.")

    while True:
        success, frame = cap.read()
        if not success: break
        
        frame_count += 1
        raw_frame = cv2.flip(frame, 1)
        
        # --- A. CHECK PRESENCE ---
        user_is_active = False
        gesture_data = engine.process_frame(raw_frame)
        if gesture_data["cursor_detected"]:
            user_is_active = True
        
        # Check face detection only occasionally to save CPU
        if not user_is_active and current_state != STATE_SAVER:
            if frame_count % 10 == 0: 
                if saver.is_face_present(raw_frame):
                    user_is_active = True
        
        if user_is_active:
            last_activity_time = time.time()

        # --- B. RESIZE ---
        # Resize frame to standard UI resolution
        display_frame = cv2.resize(raw_frame, (SCREEN_W, SCREEN_H), interpolation=cv2.INTER_LINEAR)
        h, w, _ = display_frame.shape

        # --- C. LOGIC & DRAWING ---
        if current_state == STATE_SAVER:
            status = saver.update(raw_frame)
            if status == "WAKE_UP":
                current_state = STATE_MENU
                last_activity_time = time.time()
            display_frame = draw_screensaver_ui(display_frame, saver.get_ui_data(), logo_img)

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
                    # Aici resetam jocul ca sa inceapa cu ecranul de selectie
                    game = QuizGame() 
                    game.reset_to_menu()
                elif selection == "MAP":
                    pass 
            display_frame = draw_menu_ui(display_frame, menu, gesture_data)

        elif current_state == STATE_GAME:
            if time.time() - last_activity_time > IDLE_TIMEOUT:
                current_state = STATE_SAVER
            
            # Logic Update
            exit_requested = False
            if gesture_data["cursor_detected"]:
                exit_requested = game.update(gesture_data["x"], gesture_data["y"])  
            
            game_data = game.get_current_data()
            
            # Daca am terminat jocul (sau iesim manual)
            if exit_requested:
                current_state = STATE_MENU

            # Draw
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
            # Un cursor mai frumos
            cv2.circle(display_frame, (cx, cy), 15, (0, 255, 255), 2)
            cv2.circle(display_frame, (cx, cy), 4, (255, 255, 255), -1)

        cv2.imshow(window_name, display_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

# --- HELPER FUNCTIONS ---

def draw_transparent_box(frame, x, y, w, h, color, alpha, text=None, subtext=None, progress=0.0):
    """Helper pentru desenarea cutiilor semi-transparente"""
    overlay = frame.copy()
    cv2.rectangle(overlay, (x, y), (x+w, y+h), color, -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    
    border_color = (200, 200, 200) if progress == 0 else (0, 255, 255)
    thickness = 1 if progress == 0 else 3
    cv2.rectangle(frame, (x, y), (x+w, y+h), border_color, thickness)
    
    if progress > 0:
        bar_w = int(w * progress)
        cv2.rectangle(frame, (x, y+h-10), (x+bar_w, y+h), (0, 255, 0), -1)

    if text:
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.8
        thk = 2
        tsz = cv2.getTextSize(text, font, scale, thk)[0]
        text_x = x + (w - tsz[0]) // 2
        text_y = y + (h + tsz[1]) // 2 - 15
        cv2.putText(frame, text, (text_x, text_y), font, scale, (255, 255, 255), thk)
    
    if subtext:
        cv2.putText(frame, subtext, (x + 10, y + h - 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)


def draw_game_ui(frame, data, gesture_data):
    """
    Functie actualizata pentru a desena toate starile jocului:
    SELECTIE -> JOC -> REZULTAT
    """
    h, w, _ = frame.shape
    
    # Intunecam putin fundalul pentru vizibilitate
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
    
    state = data.get("state", "")

    # --- 1. GAME SELECTION SCREEN ---
    if state == "GAME_SELECT":
        cv2.putText(frame, "SELECT A GAME MODE", (w//2 - 180, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
        
        layout = data["layout"]
        
        # Stanga: IT QUIZ
        lx, ly, lw, lh = layout["LEFT"]
        sel = (data["selection"] == "LEFT")
        prog = data["progress"] if sel else 0.0
        draw_transparent_box(frame, int(lx*w), int(ly*h), int(lw*w), int(lh*h), 
                           (50, 50, 50), 0.6, "IT QUIZ", "Start Trivia", prog)

        # Dreapta: COMING SOON
        rx, ry, rw, rh = layout["RIGHT"]
        sel = (data["selection"] == "RIGHT")
        prog = data["progress"] if sel else 0.0
        draw_transparent_box(frame, int(rx*w), int(ry*h), int(rw*w), int(rh*h), 
                           (20, 20, 20), 0.4, "COMING SOON", "Locked", prog)

    # --- 2. PLAYING / FEEDBACK ---
    elif state in ["PLAYING", "FEEDBACK"]:
        # Header Info
        cv2.putText(frame, f"Question {data['q_number']} / {data['total_q']}", (50, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 1)
        cv2.putText(frame, f"Score: {data['score']}", (w - 200, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # Intrebarea
        q_text = data["question"]
        # Facem textul intrebarii sa incapa
        font_scale = 1.0 if len(q_text) < 40 else 0.8
        cv2.putText(frame, q_text, (50, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 2)

        layout = data["layout"]
        options = data["options"]

        for key in ["LEFT", "RIGHT"]:
            bx, by, bw, bh = layout[key]
            screen_x, screen_y = int(bx*w), int(by*h)
            screen_w, screen_h = int(bw*w), int(bh*h)
            
            color = (50, 50, 50)
            text_val = options[key]
            
            # Logica Culori Feedback
            if state == "FEEDBACK":
                if key == data["correct_ans"]:
                    color = (0, 150, 0) # Verde
                    text_val += " (OK)"
                elif key == data["last_choice"] and not data["is_correct"]:
                    color = (0, 0, 150) # Rosu
                    text_val += " (WRONG)"
            
            # Logica Hover
            is_hovered = (data["selection"] == key) and (state == "PLAYING")
            prog = data["progress"] if is_hovered else 0.0
            if is_hovered: color = (100, 100, 100)

            draw_transparent_box(frame, screen_x, screen_y, screen_w, screen_h,
                               color, 0.6, text_val, "", prog)

    # --- 3. GAME OVER ---
    elif state == "GAMEOVER":
        score = data["score"]
        total = data["total"]
        final_msg = data.get("final_message", "Completed!")

        cv2.putText(frame, "QUIZ FINISHED", (w//2 - 150, h//2 - 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)
        cv2.putText(frame, f"FINAL SCORE: {score} / {total}", (w//2 - 160, h//2), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
        cv2.putText(frame, final_msg, (w//2 - 200, h//2 + 80), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (200, 200, 200), 2)
        
        # Instructiune de iesire
        if int(time.time()*2) % 2 == 0:
            cv2.putText(frame, "Hover << BACK TO MENU >> (Top Left)", (20, 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
        
        # Un buton virtual de Exit (pentru consistenta)
        # Putem adauga logica in quiz_game.py ca un hover oriunde reseteaza, 
        # sau utilizatorul asteapta timeout-ul general.

    return frame

# --- RETAIN OTHER UI FUNCTIONS ---
def draw_screensaver_ui(frame, data, logo_img=None):
    h, w, _ = frame.shape
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (20, 10, 40), -1) 
    cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)
    
    # Draw Matrix Particles
    for p in data["particles"]:
        x, y, speed, color = p
        draw_x = int(x * (w / 640)) if w > 640 else x
        draw_y = int(y * (h / 480)) if h > 480 else y
        cv2.circle(frame, (draw_x, draw_y), 2, color, -1)
        cv2.line(frame, (draw_x, draw_y), (draw_x, draw_y-10), color, 1)

    if logo_img is not None:
        try:
            ly, lx = logo_img.shape[:2]
            x_pos = (w // 2) - (lx // 2)
            y_pos = 50 
            roi = frame[y_pos:y_pos+ly, x_pos:x_pos+lx]
            if logo_img.shape[2] == 4:
                b, g, r, a = cv2.split(logo_img)
                overlay_color = cv2.merge((b, g, r))
                mask = cv2.merge((a, a, a))
                img1_bg = cv2.bitwise_and(roi.copy(), cv2.bitwise_not(mask))
                img2_fg = cv2.bitwise_and(overlay_color, mask)
                frame[y_pos:y_pos+ly, x_pos:x_pos+lx] = cv2.add(img1_bg, img2_fg)
            else:
                frame[y_pos:y_pos+ly, x_pos:x_pos+lx] = logo_img
        except Exception:
            pass

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
            TEXT_COLOR = (255, 255, 255)
            # Bar
            bar_height = 10
            bar_width = int((x2 - x1) * state["progress"])
            cv2.rectangle(frame, (x1, y2 - bar_height), (x1 + bar_width, y2), (0, 255, 0), -1)
        else:
            cv2.rectangle(frame, (x1, y1), (x2, y2), (100, 100, 100), 2)
            
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