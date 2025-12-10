import cv2
from src.vision.gesture_engine import GestureEngine
from src.ui.screens.info_hub import InfoHub

def draw_info_ui(frame, data, cursor_pos):
    h, w, _ = frame.shape
    WHITE = (255, 255, 255)
    BLUE = (255, 100, 0)
    GREEN = (0, 255, 0)
    
    # MODE 1: SELECTION
    if data["mode"] == "SELECTION":
        cv2.putText(frame, "SELECT FACULTY", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, WHITE, 2)
        
        for key, (bx, by, bw, bh) in data["buttons"].items():
            x1, y1 = int(bx*w), int(by*h)
            x2, y2 = int((bx+bw)*w), int((by+bh)*h)
            
            color = (100, 100, 100)
            if data["hovered"] == key:
                color = BLUE
                # Draw Progress Bar
                bar_w = int((x2-x1) * data["progress"])
                cv2.rectangle(frame, (x1, y2-10), (x1+bar_w, y2), GREEN, -1)
                
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, key, (x1+20, y1+50), cv2.FONT_HERSHEY_SIMPLEX, 1, WHITE, 2)

    # MODE 2: DETAIL (PAGES)
    else:
        spec = data["active_spec"]
        page = data["page"]
        
        # Draw "Page" Background
        cv2.rectangle(frame, (50, 50), (w-50, h-50), BLUE, 2)
        
        cv2.putText(frame, f"Viewing: {spec}", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, WHITE, 3)
        cv2.putText(frame, f"PAGE {page}", (w//2 - 100, h//2), cv2.FONT_HERSHEY_SIMPLEX, 3, GREEN, 5)
        
        cv2.putText(frame, "< SWIPE RIGHT (Back)   |   SWIPE LEFT (Next) >", 
                   (100, h-100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, WHITE, 2)

    # Cursor
    cx, cy = int(cursor_pos[0]*w), int(cursor_pos[1]*h)
    cv2.circle(frame, (cx, cy), 15, GREEN, -1)
    
    return frame

def main():
    cap = cv2.VideoCapture(0)
    engine = GestureEngine()
    hub = InfoHub()
    
    print("Test Started. Hover to Select. Swipe Left/Right to change pages.")

    while True:
        success, frame = cap.read()
        if not success: break
        frame = cv2.flip(frame, 1)
        
        # 1. Vision
        vision_data = engine.process_frame(frame)
        
        # 2. Logic
        if vision_data["cursor_detected"]:
            hub.update(vision_data["x"], vision_data["y"], vision_data["gesture"])
            
        # 3. Draw
        ui_data = hub.get_ui_data()
        frame = draw_info_ui(frame, ui_data, (vision_data["x"], vision_data["y"]))
        
        cv2.imshow("Info Hub Test", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()