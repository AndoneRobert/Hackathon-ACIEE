import cv2
import numpy as np

# Paleta comuna pentru toata echipa
SHARED_PALETTE = {
    "CYAN":   (235, 206, 135),
    "PINK":   (203, 192, 255),
    "BG_DARK": (40, 20, 45),
    "TEXT":   (255, 255, 255)
}

# back_button - de importat in alte screens
# from src.ui.shared import draw_back_button
def draw_back_button(frame, rect_norm, is_hovered, progress):
    """
    Deseneaza butonul de Back standardizat.
    rect_norm: tuple (x_norm, y_norm, w_norm, h_norm) - coordonate 0.0-1.0
    is_hovered: bool
    progress: float (0.0 - 1.0)
    """
    h, w, _ = frame.shape
    bx, by, bw, bh = rect_norm
    
    # Calculare pixeli
    x1, y1 = int(bx * w), int(by * h)
    x2, y2 = int((bx + bw) * w), int((by + bh) * h)
    
    # Culori
    corner_color = SHARED_PALETTE["PINK"] if is_hovered else SHARED_PALETTE["CYAN"]
    bg_color = SHARED_PALETTE["BG_DARK"]
    
    # Fundal Transparent
    roi = frame[y1:y2, x1:x2]
    color_block = np.zeros_like(roi, dtype=np.uint8)
    color_block[:] = bg_color
    cv2.addWeighted(color_block, 0.4, roi, 0.6, 0, roi)
    frame[y1:y2, x1:x2] = roi

    # Colturi Tech
    corner_len_w = int((x2 - x1) * 0.3)
    corner_len_h = int((y2 - y1) * 0.4)
    thick = 3 if is_hovered else 2

    cv2.line(frame, (x1, y1), (x1 + corner_len_w, y1), corner_color, thick)
    cv2.line(frame, (x1, y1), (x1, y1 + corner_len_h), corner_color, thick)
    cv2.line(frame, (x2, y2), (x2 - corner_len_w, y2), corner_color, thick)
    cv2.line(frame, (x2, y2), (x2, y2 - corner_len_h), corner_color, thick)

    # Progres
    if is_hovered and progress > 0:
        prog_w = int((x2 - x1) * progress)
        cv2.rectangle(frame, (x1, y2 - 4), (x1 + prog_w, y2), SHARED_PALETTE["PINK"], -1)

    # Text
    text = "<< BACK"
    font_scale = 0.7
    ts = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)[0]
    tx = x1 + (x2 - x1 - ts[0]) // 2
    ty = y1 + (y2 - y1 + ts[1]) // 2
    cv2.putText(frame, text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, SHARED_PALETTE["TEXT"], 2)