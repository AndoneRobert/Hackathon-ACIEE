import cv2
import numpy as np
from src.ui.screens.quiz_game import QuizGame

# --- CONFIGURARE MOCK ---
WINDOW_NAME = "Mock Test - Quiz Module"
WIDTH, HEIGHT = 1280, 720 # Rezoluție HD standard
mouse_x_norm, mouse_y_norm = 0.5, 0.5

def mouse_callback(event, x, y, flags, param):
    global mouse_x_norm, mouse_y_norm
    mouse_x_norm = x / WIDTH
    mouse_y_norm = y / HEIGHT

def draw_transparent_box(frame, x, y, w, h, color, alpha, text=None, subtext=None, progress=0.0):
    """Desenează o cutie stilizată similară cu poza ta"""
    overlay = frame.copy()
    
    # 1. Background semi-transparent
    cv2.rectangle(overlay, (x, y), (x+w, y+h), color, -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    
    # 2. Contur
    border_color = (200, 200, 200) if progress == 0 else (0, 255, 255)
    thickness = 1 if progress == 0 else 3
    cv2.rectangle(frame, (x, y), (x+w, y+h), border_color, thickness)
    
    # 3. Bara de Progres (Jos)
    if progress > 0:
        bar_w = int(w * progress)
        cv2.rectangle(frame, (x, y+h-10), (x+bar_w, y+h), (0, 255, 0), -1)

    # 4. Text
    if text:
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 1.0
        thk = 2
        tsz = cv2.getTextSize(text, font, scale, thk)[0]
        text_x = x + (w - tsz[0]) // 2
        text_y = y + (h + tsz[1]) // 2 - 20 # Putin mai sus de centru
        cv2.putText(frame, text, (text_x, text_y), font, scale, (255, 255, 255), thk)
    
    if subtext:
        cv2.putText(frame, subtext, (x + 10, y + h - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)

def draw_ui(frame, data):
    h, w, _ = frame.shape
    
    # Titlu General
    cv2.putText(frame, "UNIVERSITY TOUCHLESS KIOSK", (50, 50), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.line(frame, (0, 70), (w, 70), (0, 255, 255), 2)

    # --- ECRAN 1: SELECTIE JOC ---
    if data["state"] == "GAME_SELECT":
        cv2.putText(frame, "CHOOSE A GAME MODE", (w//2 - 150, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        layout = data["layout"]
        
        # Buton Stanga (IT Quiz)
        lx, ly, lw, lh = layout["LEFT"]
        sel = (data["selection"] == "LEFT")
        prog = data["progress"] if sel else 0.0
        draw_transparent_box(frame, int(lx*w), int(ly*h), int(lw*w), int(lh*h), 
                           (50, 50, 50), 0.5, "IT QUIZ", "Test your skills", prog)

        # Buton Dreapta (Placeholder)
        rx, ry, rw, rh = layout["RIGHT"]
        sel = (data["selection"] == "RIGHT")
        prog = data["progress"] if sel else 0.0
        draw_transparent_box(frame, int(rx*w), int(ry*h), int(rw*w), int(rh*h), 
                           (20, 20, 20), 0.3, "COMING SOON", "Future Module", prog)

    # --- ECRAN 2: JOC ACTIV / FEEDBACK ---
    elif data["state"] in ["PLAYING", "FEEDBACK"]:
        # Întrebarea
        q_text = data["question"]
        # Wrap text simplu (doar pentru demo)
        cv2.putText(frame, f"Q{data['q_number']}: {q_text}", (100, 200), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
        
        layout = data["layout"]
        options = data["options"]
        
        # Desenam optiunile
        for key in ["LEFT", "RIGHT"]:
            bx, by, bw, bh = layout[key]
            screen_x, screen_y = int(bx*w), int(by*h)
            screen_w, screen_h = int(bw*w), int(bh*h)
            
            color = (50, 50, 50) # Gri default
            text_val = options[key]
            
            # LOGICA DE CULOARE PENTRU FEEDBACK
            if data["state"] == "FEEDBACK":
                if key == data["correct_ans"]:
                    color = (0, 150, 0) # Verde (Corect)
                    text_val += " (CORRECT)"
                elif key == data["last_choice"] and not data["is_correct"]:
                    color = (0, 0, 150) # Rosu (Gresit)
                    text_val += " (WRONG)"
            
            # Hover
            is_hovered = (data["selection"] == key) and (data["state"] == "PLAYING")
            prog = data["progress"] if is_hovered else 0.0
            
            if is_hovered: color = (100, 100, 100)

            draw_transparent_box(frame, screen_x, screen_y, screen_w, screen_h,
                               color, 0.6, text_val, "", prog)

    # --- ECRAN 3: GAMEOVER ---
    elif data["state"] == "GAMEOVER":
        score = data["score"]
        total = data["total"]
        msg = "EXCELLENT!" if score > total/2 else "GOOD TRY!"
        
        cv2.putText(frame, "QUIZ COMPLETE", (w//2 - 150, h//2 - 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)
        cv2.putText(frame, f"SCORE: {score} / {total}", (w//2 - 120, h//2 + 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
        cv2.putText(frame, msg, (w//2 - 100, h//2 + 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 200, 200), 2)
        
        cv2.putText(frame, "Hover anywhere to exit (mock)", (w//2 - 150, h - 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)

    return frame

def main():
    game = QuizGame()
    
    cv2.namedWindow(WINDOW_NAME)
    cv2.setMouseCallback(WINDOW_NAME, mouse_callback)
    
    # Imagine de fundal simulata (Gradient sau Negru)
    bg = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    # Facem un gradient gri inchis pentru aspect "premium"
    for y in range(HEIGHT):
        v = int(30 * (y / HEIGHT))
        bg[y, :] = (v, v, v + 10)

    print("--- MOCK STARTED ---")
    
    while True:
        frame = bg.copy()
        
        # Update Logic
        game.update(mouse_x_norm, mouse_y_norm)
        
        # Draw UI
        data = game.get_current_data()
        frame = draw_ui(frame, data)
        
        # Cursor
        cx, cy = int(mouse_x_norm * WIDTH), int(mouse_y_norm * HEIGHT)
        cv2.circle(frame, (cx, cy), 15, (0, 255, 255), 2)
        
        cv2.imshow(WINDOW_NAME, frame)
        
        k = cv2.waitKey(10) & 0xFF
        if k == ord('q'): break
        if k == ord('r'): game.reset_to_menu()

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()