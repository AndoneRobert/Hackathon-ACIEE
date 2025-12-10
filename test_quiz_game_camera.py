import cv2
import numpy as np
import time

# Importăm componentele reale
from src.vision.gesture_engine import GestureEngine
from src.ui.screens.quiz_game import QuizGame

# --- CONFIGURARE ---
WINDOW_NAME = "Test Quiz Game - CAMERA MODE"
WIDTH, HEIGHT = 1280, 720 # Vom forța această rezoluție pentru desenare

def draw_transparent_box(frame, x, y, w, h, color, alpha, text=None, subtext=None, progress=0.0):
    """(Aceeasi functie de desenare din Mock)"""
    # Verificam sa nu iesim din ecran
    img_h, img_w, _ = frame.shape
    
    # Clamp coordinates
    x = max(0, min(x, img_w-1))
    y = max(0, min(y, img_h-1))
    w = min(w, img_w - x)
    h = min(h, img_h - y)
    
    if w <= 0 or h <= 0: return

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
        scale = 1.0
        thk = 2
        tsz = cv2.getTextSize(text, font, scale, thk)[0]
        text_x = x + (w - tsz[0]) // 2
        text_y = y + (h + tsz[1]) // 2 - 20
        cv2.putText(frame, text, (text_x, text_y), font, scale, (255, 255, 255), thk)
    
    if subtext:
        cv2.putText(frame, subtext, (x + 10, y + h - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)

def draw_ui(frame, data):
    h, w, _ = frame.shape
    
    # Titlu
    cv2.putText(frame, "UNIVERSITY TOUCHLESS KIOSK (CAMERA TEST)", (30, 50), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)

    # --- ECRAN 1: SELECTIE JOC ---
    if data["state"] == "GAME_SELECT":
        cv2.putText(frame, "CHOOSE A GAME MODE", (w//2 - 150, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        layout = data["layout"]
        
        # Stanga
        lx, ly, lw, lh = layout["LEFT"]
        sel = (data["selection"] == "LEFT")
        prog = data["progress"] if sel else 0.0
        draw_transparent_box(frame, int(lx*w), int(ly*h), int(lw*w), int(lh*h), 
                           (50, 50, 50), 0.5, "IT QUIZ", "Start Game", prog)

        # Dreapta
        rx, ry, rw, rh = layout["RIGHT"]
        sel = (data["selection"] == "RIGHT")
        prog = data["progress"] if sel else 0.0
        draw_transparent_box(frame, int(rx*w), int(ry*h), int(rw*w), int(rh*h), 
                           (20, 20, 20), 0.3, "COMING SOON", "", prog)

    # --- ECRAN 2: JOC ACTIV / FEEDBACK ---
    elif data["state"] in ["PLAYING", "FEEDBACK"]:
        q_text = data["question"]
        cv2.putText(frame, f"Q{data['q_number']}: {q_text}", (50, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        
        layout = data["layout"]
        options = data["options"]
        
        for key in ["LEFT", "RIGHT"]:
            bx, by, bw, bh = layout[key]
            # Convertim coordonatele relative in pixeli
            screen_x, screen_y = int(bx*w), int(by*h)
            screen_w, screen_h = int(bw*w), int(bh*h)
            
            color = (50, 50, 50)
            text_val = options[key]
            
            if data["state"] == "FEEDBACK":
                if key == data["correct_ans"]:
                    color = (0, 150, 0)
                    text_val += " (OK)"
                elif key == data["last_choice"] and not data["is_correct"]:
                    color = (0, 0, 150)
                    text_val += " (X)"
            
            is_hovered = (data["selection"] == key) and (data["state"] == "PLAYING")
            prog = data["progress"] if is_hovered else 0.0
            
            if is_hovered: color = (100, 100, 100)

            draw_transparent_box(frame, screen_x, screen_y, screen_w, screen_h,
                               color, 0.6, text_val, "", prog)

    # --- ECRAN 3: GAMEOVER ---
    elif data["state"] == "GAMEOVER":
        score = data["score"]
        total = data["total"]
        cv2.putText(frame, "GAME OVER", (w//2 - 100, h//2 - 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)
        cv2.putText(frame, f"SCORE: {score}/{total}", (w//2 - 80, h//2 + 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
        cv2.putText(frame, "Resetting in 5s...", (w//2 - 100, h - 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 1)

    return frame

def main():
    # 1. Initializare Camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Eroare: Nu pot deschide camera!")
        return

    # 2. Initializare Componente
    engine = GestureEngine()
    game = QuizGame()
    
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

    print("--- CAMERA TEST STARTED ---")
    print("Foloseste mana pentru a controla cursorul.")
    print("Apasa 'q' pentru iesire.")
    
    game_over_timer = 0

    while True:
        success, frame = cap.read()
        if not success: break
        
        # Flip pentru efect de oglinda (natural pentru utilizator)
        frame = cv2.flip(frame, 1)
        
        # Redimensionam pentru consistenta vizuala
        frame = cv2.resize(frame, (WIDTH, HEIGHT))
        
        # --- A. PROCESARE GESTURI ---
        gesture_data = engine.process_frame(frame)
        
        # --- B. UPDATE JOC ---
        # Actualizam jocul doar daca avem cursor, altfel jocul ramane pe loc
        if gesture_data["cursor_detected"]:
            game.update(gesture_data["x"], gesture_data["y"])
        
        # Auto-reset la Game Over dupa 5 secunde
        data = game.get_current_data()
        if data["state"] == "GAMEOVER":
            if game_over_timer == 0:
                game_over_timer = time.time()
            elif time.time() - game_over_timer > 5.0:
                game.reset_to_menu()
                game_over_timer = 0
        
        # --- C. DESENARE UI ---
        # Desenam interfata peste frame-ul camerei
        # Intai intunecam putin video-ul ca sa se vada textul
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (WIDTH, HEIGHT), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        
        frame = draw_ui(frame, data)
        
        # --- D. DESENARE CURSOR ---
        if gesture_data["cursor_detected"]:
            cx, cy = int(gesture_data["x"] * WIDTH), int(gesture_data["y"] * HEIGHT)
            
            # Cerc principal
            cv2.circle(frame, (cx, cy), 15, (0, 255, 255), 2)
            # Punct centru
            cv2.circle(frame, (cx, cy), 5, (255, 255, 255), -1)
            
            # Debug: arata gest (optional)
            if gesture_data["gesture"]:
                cv2.putText(frame, gesture_data["gesture"], (cx + 20, cy), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.imshow(WINDOW_NAME, frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()