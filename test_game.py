import cv2
import numpy as np
from src.vision.gesture_engine import GestureEngine
from src.ui.screens.menu import MenuController

def draw_menu_ui(frame, menu, cursor_pos):
    h, w, _ = frame.shape
    layout = menu.get_layout()
    state = menu.get_state()
    
    # Colors
    WHITE = (255, 255, 255)
    GRAY = (100, 100, 100)
    GREEN = (0, 255, 0)
    BLUE = (255, 100, 0)

    # Draw Buttons
    for name, (bx, by, bw, bh) in layout.items():
        # Convert percentages to pixels
        x1, y1 = int(bx * w), int(by * h)
        x2, y2 = int((bx + bw) * w), int((by + bh) * h)
        
        color = GRAY
        thickness = 2
        
        # Highlight if hovered
        if state["hovered"] == name:
            color = BLUE
            thickness = 5
            
            # Draw Loading Bar at bottom of card
            bar_width = int((x2 - x1) * state["progress"])
            cv2.rectangle(frame, (x1, y2 - 20), (x1 + bar_width, y2), GREEN, -1)

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
        
        # Draw Text Centered
        text_size = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
        text_x = x1 + (x2 - x1 - text_size[0]) // 2
        text_y = y1 + (y2 - y1 + text_size[1]) // 2
        cv2.putText(frame, name, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1, WHITE, 2)

    # Draw Cursor
    cx, cy = int(cursor_pos[0] * w), int(cursor_pos[1] * h)
    cv2.circle(frame, (cx, cy), 15, GREEN, -1)

    return frame

def main():
    cap = cv2.VideoCapture(0)
    engine = GestureEngine()
    menu = MenuController()

    print("Starting Menu Test...")
    print("Hover over INFO, PLAY, or MAP to select.")

    while True:
        success, frame = cap.read()
        if not success: break
        
        frame = cv2.flip(frame, 1) # Mirror
        
        # 1. Vision
        data = engine.process_frame(frame)
        
        # 2. Logic
        if data["cursor_detected"]:
            selection = menu.update(data["x"], data["y"])
            if selection:
                print(f"SELECTED: {selection}")
                # In the real app, this is where you change screens
        
        # 3. Draw
        frame = draw_menu_ui(frame, menu, (data["x"], data["y"]))
        
        cv2.imshow("University Kiosk - Menu Test", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()