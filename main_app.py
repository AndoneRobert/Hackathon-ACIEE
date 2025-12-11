import cv2
import time
import os
import numpy as np

# --- IMPORT COMPONENTS ---
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

# Time in seconds before returning to screensaver
IDLE_TIMEOUT = 20.0 

def main():
    # 1. SETUP WINDOW & CAMERA
    SCREEN_W, SCREEN_H = 1920, 1080
    
    # RPI FIX: Explicitly set V4L2 backend for robust camera initialization on Linux/RPi
    # Note: cv2.CAP_V4L2 requires 'opencv-contrib-python' which is in your requirements.txt.
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2) #
    
    # RPI FIX: Check if camera opened correctly
    if not cap.isOpened():
        print("FATAL ERROR: Could not open camera (Index 0). Check if /dev/video0 exists or if the camera is enabled.")
        return # Exit main function if camera fails

    window_name = "University AI Kiosk"
    
    # RPI FIX: Use simpler window setup for troubleshooting, removing fullscreen initially
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE) 
    # cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN) # Commented out for now
    
    # 2. LOAD LOGO
    logo_path = "assets/images/logo_ugal.jpeg" #
    logo_img = None #
    if os.path.exists(logo_path): #
        temp_img = cv2.imread(logo_path, cv2.IMREAD_UNCHANGED) #
        if temp_img is not None: #
            target_width = 400 #
            h_logo, w_logo = temp_img.shape[:2] #
            aspect = h_logo / w_logo #
            logo_img = cv2.resize(temp_img, (target_width, int(target_width * aspect))) #
            print(f"SUCCESS: Logo loaded from {logo_path}") #

    # 3. INITIALIZE COMPONENTS
    engine = GestureEngine() #
    saver = Screensaver() #
    menu = MenuController() #
    game = QuizGame() #
    info = InfoHub() #

    current_state = STATE_SAVER #
    last_activity_time = time.time() #
    
    # 4. MAIN LOOP
    while True: #
        success, frame = cap.read() #
        if not success: break #
        
        # Mirror and resize to full screen
        raw_frame = cv2.flip(frame, 1) #
        display_frame = cv2.resize(raw_frame, (SCREEN_W, SCREEN_H)) #
        h, w, _ = display_frame.shape #
        
        # --- GESTURE PROCESSING ---
        gesture_data = engine.process_frame(raw_frame) #
        
        # FIX: Check if a face is present using the existing saver instance
        is_face_present = saver.is_face_present(display_frame) #

        # Reset timer if EITHER hand is detected OR face is detected
        if gesture_data["cursor_detected"] or is_face_present: #
            last_activity_time = time.time() #

        # --- STATE MACHINE ---
        
        # === A. SCREENSAVER ===
        if current_state == STATE_SAVER: #
            status = saver.update(display_frame) #
            if status == "WAKE_UP": #
                current_state = STATE_MENU #
                last_activity_time = time.time() #
            
            display_frame = saver.draw(display_frame, logo_img) #

        # === B. MAIN MENU ===
        elif current_state == STATE_MENU: #
            if time.time() - last_activity_time > IDLE_TIMEOUT: #
                current_state = STATE_SAVER #

            if gesture_data["cursor_detected"]: #
                selection = menu.update(gesture_data["x"], gesture_data["y"]) #
                
                if selection == "INFO": #
                    current_state = STATE_INFO #
                    info = InfoHub() # Reset state #
                elif selection == "PLAY": #
                    current_state = STATE_GAME #
                    game = QuizGame() # Reset state #
                elif selection == "MAP": #
                    print("Map Selected (Placeholder)") #
            
            display_frame = menu.draw(display_frame) #

        # === C. QUIZ GAME ===
        elif current_state == STATE_GAME: #
            if time.time() - last_activity_time > IDLE_TIMEOUT: #
                current_state = STATE_SAVER #

            if gesture_data["cursor_detected"]: #
                game.update(gesture_data["x"], gesture_data["y"]) #
            
            if game.game_over: #
                # Add exit logic here if needed, or wait for timeout #
                pass #
                
            display_frame = game.draw(display_frame) #

        # === D. INFO HUB ===
        elif current_state == STATE_INFO: #
            if time.time() - last_activity_time > IDLE_TIMEOUT: #
                current_state = STATE_SAVER #

            # Update accepts gesture for swiping
            if gesture_data["cursor_detected"] or gesture_data["gesture"]: #
                res = info.update(gesture_data["x"], gesture_data["y"], gesture_data["gesture"]) #
                if res == "BACK_TO_MENU": #
                    current_state = STATE_MENU #
            
            display_frame = info.draw(display_frame) #

        # --- DRAW GLOBAL CURSOR ---
        if current_state != STATE_SAVER and gesture_data["cursor_detected"]: #
            cx, cy = int(gesture_data["x"] * w), int(gesture_data["y"] * h) #
            cv2.circle(display_frame, (cx, cy), 15, (0, 255, 255), 2) #
            cv2.circle(display_frame, (cx, cy), 4, (255, 255, 255), -1) #

        cv2.imshow(window_name, display_frame) #
        if cv2.waitKey(1) & 0xFF == ord('q'): break #

    cap.release() #
    cv2.destroyAllWindows() #

if __name__ == "__main__": #
    main() #