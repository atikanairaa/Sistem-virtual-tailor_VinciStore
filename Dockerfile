# Gunakan image Python 3.10 slim-buster yang ringan namun stabil
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Set direktori kerja
WORKDIR /app

# Install sistem dependensi wajib untuk OpenCV dan MediaPipe
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Salin requirements dan install package Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh kode aplikasi
COPY . .

# Expose port (HuggingFace Spaces secara default membutuhkan port 7860)
EXPOSE 7860

# Jalankan Gunicorn (WSGI Server Production)
# run:app merujuk pada file run.py dan instance app di dalamnya
# Menggunakan 1 worker dan 4 thread untuk efisiensi di HuggingFace Spaces
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "1", "--threads", "4", "run:app"]
