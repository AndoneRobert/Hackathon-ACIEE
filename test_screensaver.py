import cv2
import numpy as np
from src.ui.screens.screensaver import Screensaver

def draw_screensaver(frame, data):
    h, w, _ = frame.shape
    
    # 1. Simulate "Promotional Video" (Darkened Background)
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame) # Darken video
    
    # 2. Draw "Promotional Text"
    # Animate transparency or color based on frame count
    anim_frame = data.get("anim_frame", 0)
    alpha = (np.sin(anim_frame * 0.1) + 1) / 2 # 0.0 to 1.0
    text_color = (int(255 * alpha), int(255 * alpha), 255)
    
    cv2.putText(frame, "WELCOME TO THE UNIVERSITY", (50, h//2 - 50), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.5, text_color, 3)
    cv2.putText(frame, "Step closer to start", (50, h//2 + 50), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 200, 200), 2)

    # 3. Draw "Waking Up" Progress
    if data.get("waking_progress", 0) > 0:
        bar_w = int(w * data.get("waking_progress", 0))
        cv2.rectangle(frame, (0, h-20), (bar_w, h), (0, 255, 255), -1)
        cv2.putText(frame, "DETECTING USER...", (10, h-30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        
    return frame

def main():
    cap = cv2.VideoCapture(0)
    saver = Screensaver()
    
    print("Screensaver Test Started.")
    print("Hide from camera to sleep. Look at camera to wake up.")

    while True:
        success, frame = cap.read()
        if not success: break
        
        # Don't flip frame here, detection works better on raw feed often, 
        # but for consistency with UI we can flip.
        frame = cv2.flip(frame, 1) 
        
        # 1. Update Logic
        status = saver.update(frame)
        
        if status == "WAKE_UP":
            print(">>> WAKE UP TRIGGERED! (Switching to Menu) <<<")
            # In real app, reset state here
        
        # 2. Draw UI
        ui_data = saver.get_ui_data()
        frame = draw_screensaver(frame, ui_data)
        
        cv2.imshow("Screensaver Test", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()