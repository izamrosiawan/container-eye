# Container-Eye: Real-Time CCTV Defect Inspector for Port Logistics

**Container-Eye** adalah sistem pengawasan inspeksi visual berbasis *Computer Vision* dan *Deep Learning* (YOLOv8) yang dirancang khusus untuk memonitor kelaikan fisik peti kemas (*shipping containers*) secara otomatis dan *real-time* di portal gerbang pelabuhan (*gate-in / gate-out*).

## Fitur Utama
- **Fokus Layar CCTV Real-Time**: Tampilan antarmuka berkecepatan tinggi dengan *Heads-Up Display* (HUD) transparan.
- **Deteksi 4 Kategori Kerusakan (IICL-6)**:
  - `Dent` (Penyok dinding gelombang)
  - `Rust` (Korosi pelat baja)
  - `Hole` (Lubang tembus dinding - Kritis)
  - `Deframe` (Tekukan tiang sudut - Kritis)
- **Gate Decision Engine**: Keputusan otomatis `GATE PASS` (Hijau), `GATE CAUTION` (Kuning), atau `GATE HOLD / REJECT` (Merah).
- **Alarm Audio & Auto-Snapshot**: Membunyikan peringatan suara seketika dan menyimpan foto bukti saat anomali kritis terdeteksi.
- **Dukungan Multi-Input**: Siaran IP Camera RTSP, webcam USB, maupun berkas video simulasi.

## Cara Menjalankan
```bash
python main.py
```
