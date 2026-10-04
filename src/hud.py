import cv2

def draw_clean_hud(frame, detections, class_names, class_colors, critical_classes):
    is_critical = False

    for det in detections:
        cls_id = det["class_id"]
        # Jika model COCO generic, mapping ke nama atau pakai nama model
        cls_name = class_names.get(cls_id, f"Class {cls_id}")
        conf = det["confidence"]
        x1, y1, x2, y2 = det["box"]

        color = class_colors.get(cls_name, (0, 255, 0))
        if cls_name in critical_classes:
            is_critical = True

        # Bounding box tipis bersih (thickness=2)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        # Tag label kecil di atas box, tanpa tumpang tindih
        label_text = f"{cls_name} {int(conf * 100)}%"
        (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        tag_y = max(th + 4, y1)
        cv2.rectangle(frame, (x1, tag_y - th - 4), (x1 + tw + 6, tag_y + 2), color, -1)
        cv2.putText(frame, label_text, (x1 + 3, tag_y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)

    return frame, is_critical
