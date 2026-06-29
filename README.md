# Virtual Tailor

Virtual Tailor adalah aplikasi berbasis web yang menggunakan kecerdasan buatan (Computer Vision) untuk melakukan pengukuran tubuh manusia secara otomatis dan memberikan rekomendasi kecocokan (fit recommendation) terhadap produk pakaian.

Sistem ini dikembangkan dengan **Flask** untuk backend, **MediaPipe** untuk deteksi pose tubuh (pose estimation), dan menggunakan arsitektur **Domain-Driven Design (DDD)**.

## 🔄 Workflow Sistem

1. **Pemilihan Produk**: Pelanggan memilih pakaian dari katalog yang tersedia (contoh: kemeja, jaket, kaos). Masing-masing produk memiliki target ukuran tertentu.
2. **Metode Pengukuran**: Pelanggan dapat menggunakan **Live Camera (Webcam)** atau **Upload Foto**.
3. **Kalibrasi**: Pelanggan mengatur metode kalibrasi untuk mengonversi piksel pada gambar menjadi ukuran sentimeter (cm) yang akurat. Metode yang tersedia:
   - **Height (Rekomendasi)**: Menggunakan tinggi badan asli pelanggan.
   - **Reference Object**: Menggunakan objek referensi berukuran standar (seperti kartu KTP/ATM berukuran ~8.56cm).
4. **Pemindaian Pose (Pose Detection)**: Sistem menggunakan MediaPipe untuk mendeteksi landmark tubuh pelanggan pada gambar/kamera.
5. **Kalkulasi Ukuran (Measurement)**: Sistem menghitung lebar bahu, lingkar dada, dan lebar pinggul pelanggan berdasarkan jarak landmark yang telah dikalibrasi.
6. **Analisis Bentuk Tubuh & Rekomendasi Fit**: Berdasarkan ukuran yang didapat, sistem menentukan bentuk tubuh pelanggan (misal: *Inverted Triangle*, *Rectangle*) dan memberikan status rekomendasi kecocokan (misal: *Perfect Fit*, *Too Tight*) terhadap produk yang dipilih di awal.
7. **Add to Cart**: Pelanggan dapat melanjutkan berbelanja dengan ukuran kustom tersebut.

## 📂 Struktur Repository

Proyek ini dipisahkan secara modular mengikuti prinsip Domain-Driven Design (DDD) untuk kemudahan *maintenance* dan skalabilitas.

```text
virtual_tailor/
├── backend/                        # Kode Utama Backend & Web UI
│   ├── app.py                      # Entry point utama aplikasi Flask
│   ├── config.py                   # Konfigurasi environment (port, debug, dll)
│   ├── application/                # Layer Application (Service Layer)
│   │   ├── dto/                    # Data Transfer Objects (struktur data request/response)
│   │   └── services/               # Bussiness logic flow (PoseAnalysisService, MeasurementService)
│   ├── domain/                     # Layer Domain (Core Business Logic)
│   │   └── entities/               # Entitas model data inti (BodyMeasurements)
│   ├── infrastructure/             # Layer Infrastructure (External libraries/hardware)
│   │   ├── calibration/            # Logika kalibrasi piksel ke cm (HeightCalibrator)
│   │   ├── mediapipe/              # Integrasi model AI deteksi pose (MediaPipe PoseDetector)
│   │   └── models/                 # Model machine learning eksternal
│   ├── interfaces/                 # Layer Interfaces (Controllers/Routes)
│   │   └── api/                    # Endpoint API Flask (routes.py)
│   ├── models/                     # Tempat meletakkan file model .task dari MediaPipe (pose_landmarker)
│   ├── static/                     # Frontend UI (HTML, CSS, JS) yang di-serve oleh Flask
│   │   ├── css/                    # Stylesheet aplikasi (styles.css)
│   │   ├── js/                     # Logika klien (app.js, api.js, ui.js)
│   │   ├── index.html              # Halaman utama aplikasi (Katalog & UI)
│   └── requirements.txt            # Dependensi library Python
├── frontend/                       # (Opsional/Draft) Pengembangan frontend modern terpisah (Node.js/React)
├── run.py                          # Script alternatif untuk menjalankan sistem
└── README.md                       # Dokumentasi sistem ini
```

### Penjelasan Fungsi Komponen Penting Backend:
- **`app.py`**: Mengonfigurasi dan menjalankan server Flask, mendaftarkan blueprint API, dan me-routing akses file web statis.
- **`interfaces/api/routes.py`**: Menangani permintaan (HTTP requests) dari pelanggan seperti mengambil produk, melakukan `prescan` posisi, dan proses `analyze` gambar yang diunggah atau ditangkap kamera.
- **`application/services/pose_analysis_service.py`**: Orkestrator utama analisis. Menerima gambar dari route, memerintahkan `PoseDetector` mencari landmark, mengalibrasi skala piksel, lalu meminta pengukuran ke `MeasurementService`.
- **`application/services/measurement_service.py`**: Menghitung jarak spesifik tubuh (bahu, dada, pinggul), bentuk tubuh, serta perbandingan fit dengan baju.
- **`infrastructure/mediapipe/pose_detector.py`**: Menjalankan library ML MediaPipe Pose Landmarker untuk mengekstraksi koordinat landmark secara akurat.
- **`static/js/app.js`**: Menghandle state aplikasi klien seperti pemanggilan WebRTC webcam, navigasi tab, menggambar overlay instruksi di Canvas, serta menghubungi API backend secara asinkron.
