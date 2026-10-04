import cv2
import time
import numpy as np

def draw_hud(frame, detections, latency_ms, fps, port_name, gate_name, frame_id, class_names, class_colors, critical_classes):
    h, w = frame.shape[:2]
    overlay = frame.copy()

    # Hitung anomali
    critical_detected = False
    defect_counts = {name: 0 for name in class_names.values()}

    for det in detections:
        cls_id = det["class_id"]
        cls_name = class_names.get(cls_id, f"ID_{cls_id}")
        conf = det["confidence"]
        x1, y1, x2, y2 = det["box"]

        color = class_colors.get(cls_name, (0, 255, 0))
        defect_counts[cls_name] = defect_counts.get(cls_name, 0) + 1

        if cls_name in critical_classes:
            critical_detected = True

        # Bounding box tebal bergaya high-tech CCTV
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        # Sudut siku-siku (Corner brackets)
        line_len = min(20, (x2 - x1) // 3, (y2 - y1) // 3)
        cv2.line(frame, (x1, y1), (x1 + line_len, y1), color, 4)
        cv2.line(frame, (x1, y1), (x1, y1 + line_len), color, 4)
        cv2.line(frame, (x2, y1), (x2 - line_len, y1), color, 4)
        cv2.line(frame, (x2, y1), (x2, y1 + line_len), color, 4)
        cv2.line(frame, (x1, y2), (x1 + line_len, y2), color, 4)
        cv2.line(frame, (x1, y2), (x1, y2 - line_len), color, 4)
        cv2.line(frame, (x2, y2), (x2 - line_len, y2), color, 4)
        cv2.line(frame, (x2, y2), (x2, y2 - line_len), color, 4)

        # Tag label
        label_text = f"{cls_name.upper()} {int(conf * 100)}%"
        if cls_name in critical_classes:
            label_text = f"[!] CRITICAL: {label_text}"

        (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        tag_y = max(th + 6, y1 - 6)
        cv2.rectangle(frame, (x1, tag_y - th - 4), (x1 + tw + 8, tag_y + 4), color, -1)
        cv2.putText(frame, label_text, (x1 + 4, tag_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

    # 1. Header Bar Atas (Translucent Dark Strip)
    header_h = 55
    cv2.rectangle(overlay, (0, 0), (w, header_h), (15, 15, 15), -1)

    # 2. Footer Bar Bawah (Banner Status Gerbang)
    footer_h = 60
    cv2.rectangle(overlay, (0, h - footer_h), (w, h), (15, 15, 15), -1)

    # Blend alpha
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    # Garis tepi pemisah header & footer
    cv2.line(frame, (0, header_h), (w, header_h), (50, 50, 50), 1)
    cv2.line(frame, (0, h - footer_h), (w, h - footer_h), (50, 50, 50), 1)

    # Text Header Kiri
    time_str = time.strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(frame, f"{port_name} | {gate_name}", (15, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (230, 230, 230), 1, cv2.LINE_AA)
    cv2.putText(frame, f"FEED: {frame_id} | TIME: {time_str}", (15, 44), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 160, 160), 1, cv2.LINE_AA)

    # Telemetri Kanan Atas
    fps_color = (0, 255, 0) if fps >= 30 else (0, 165, 255)
    telemetry_str = f"FPS: {fps:.1f} | INFER: {latency_ms:.1f} ms"
    cv2.putText(frame, telemetry_str, (w - 240, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.55, fps_color, 1, cv2.LINE_AA)
    
    # Rec indicator berkedip
    if int(time.time() * 2) % 2 == 0:
        cv2.circle(frame, (w - 260, 24), 6, (0, 0, 255), -1)
        cv2.putText(frame, "LIVE", (w - 295, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1, cv2.LINE_AA)

    # Footer Status Keputusan Kelaikan IICL-6
    if critical_detected:
        status_text = "[!] GATE HOLD / REJECT - KERUSAKAN KRITIS DITEMUKAN (TIDAK LAIK MUAT)"
        status_color = (0, 0, 255) # Merah
        banner_fill = (0, 0, 180)
    elif len(detections) > 0:
        status_text = "[!] GATE CAUTION - CACAT MINOR TERDETEKSI (PERLU INSPEKSI VISUAL TAMBAHAN)"
        status_color = (0, 215, 255) # Kuning
        banner_fill = (0, 140, 180)
    else:
        status_text = "[OK] GATE PASS - KONTAINER LAIK MUAT / SEAWORTHY (IICL-6)"
        status_color = (0, 255, 0) # Hijau
        banner_fill = (0, 160, 0)

    # Kotak aksen status di kiri bawah
    cv2.rectangle(frame, (15, h - footer_h + 10), (32, h - 10), status_color, -1)
    cv2.putText(frame, status_text, (40, h - footer_h + 36), cv2.FONT_HERSHEY_SIMPLEX, 0.60, status_color, 2, cv2.LINE_AA)

    # Summary defect di kanan bawah
    summary_str = f"Defects: {len(detections)} [Dent:{defect_counts.get('Dent',0)} Rust:{defect_counts.get('Rust',0)} Hole:{defect_counts.get('Hole',0)} Deframe:{defect_counts.get('Deframe',0)}]"
    cv2.putText(frame, summary_str, (w - 470, h - footer_h + 36), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)

    return frame, critical_detected
