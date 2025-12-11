import cv2
import numpy as np
# CHANGE: Importing 'Menu' from 'menu' (filename menu.py)
from menu import MenuController

# Global variables to store mouse position
mouse_x, mouse_y = 0, 0

def mouse_callback(event, x, y, flags, param):
    global mouse_x, mouse_y
    if event == cv2.EVENT_MOUSEMOVE:
        mouse_x, mouse_y = x, y

def run_test():
    WINDOW_NAME = "Menu Test Playground"
    WIDTH, HEIGHT = 1280, 720
    
    # CHANGE: Instantiating the class as 'Menu'
    menu = Menu()
    
    cv2.namedWindow(WINDOW_NAME)
    cv2.setMouseCallback(WINDOW_NAME, mouse_callback)
    
    print(f"Starting Test... Resolution: {WIDTH}x{HEIGHT}")
    print("Hover over the pixel bubbles to test selection.")
    print("Press 'q' to quit.")

    while True:
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

        # Normalize Mouse Coordinates (0.0 to 1.0)
        norm_x = mouse_x / WIDTH
        norm_y = mouse_y / HEIGHT

        selected_item = menu.update(norm_x, norm_y)

        if selected_item:
            print(f">>> SELECTION CONFIRMED: {selected_item} <<<")
            cv2.rectangle(frame, (0,0), (WIDTH, HEIGHT), (0, 255, 0), 10)

        final_frame = menu.draw(frame)

        # Draw Cursor
        cv2.circle(final_frame, (mouse_x, mouse_y), 10, (0, 0, 255), -1)
        
        cv2.imshow(WINDOW_NAME, final_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_test()