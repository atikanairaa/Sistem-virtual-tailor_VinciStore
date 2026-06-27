class UIManager {
    constructor() {
        this.mediaContainer = document.getElementById('mediaContainer');
        this.statusToast = document.getElementById('statusToast');
    }

    // Fungsi menggambar ditiadakan karena metode manual dihapus
    setDrawingEnabled(enabled) { return; }
    clearCanvas() {
        const canvas = document.getElementById('drawCanvas');
        if(canvas) canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
    }

    showToast(message, type = 'info') {
        this.statusToast.innerHTML = `<i class="fas fa-${type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i> <span style="margin-left:8px;">${message}</span>`;
        this.statusToast.style.borderColor = type === 'error' ? 'var(--danger)' : (type === 'success' ? 'var(--success)' : 'var(--primary)');
        this.statusToast.classList.add('show');
        setTimeout(() => this.statusToast.classList.remove('show'), 3000);
    }

    updateMeasurements(data) {
        const resultsDiv = document.getElementById('measurementsResults');
        const calStatus = document.getElementById('calibrationStatusBadge');

        if (!data || !data.measurements) {
            resultsDiv.innerHTML = '<div class="measurement-item"><span class="measurement-label">Status</span><span class="measurement-value" style="color:var(--text-muted)">Menunggu data masuk...</span></div>';
            calStatus.className = 'status-badge status-uncalibrated';
            calStatus.textContent = 'Siap Menganalisa';
            return;
        }

        const m = data.measurements;
        let html = '';

        // Tampilkan hanya data esensial
        if (m.chest_circumference_cm)
            html += `<div class="measurement-item"><span class="measurement-label">Lingkar Dada</span><span class="measurement-value" style="font-size:1.3rem; color: var(--primary);">${m.chest_circumference_cm.toFixed(1)} cm</span></div>`;

        if (m.body_shape)
            html += `<div class="measurement-item"><span class="measurement-label">Bentuk Tubuh</span><span class="measurement-value" id="valBodyShape">${m.body_shape}</span></div>`;

        if (m.fit_recommendation) {
            const fitColors = {
                'Regular Fit': '#10b981', 'Oversize Fit': '#d97706', 'Tight Fit': '#ef4444',
                'Not Recommended': '#f97316', 'Unknown': '#64748b'
            };
            const color = fitColors[m.fit_recommendation] || 'var(--primary)';
            html += `<div class="measurement-item">
                <span class="measurement-label">Rekomendasi Ukuran</span>
                <span class="measurement-value" id="valFitStatus" style="color: ${color}; font-weight: 800;">${m.fit_recommendation}</span>
            </div>`;
        }

        resultsDiv.innerHTML = html;
        calStatus.className = 'status-badge status-calibrated';
        calStatus.textContent = 'Analisa Selesai';
    }
}

window.ui = new UIManager();