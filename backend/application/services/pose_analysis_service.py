# pyrefly: ignore [missing-import]
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Any

from application.dto.pose_analysis_request import PoseAnalysisRequest, CalibrationType
from application.services.measurement_service import MeasurementService
from infrastructure.mediapipe.pose_detector import PoseDetector
from infrastructure.calibration.height_calibrator import HeightCalibrator
from infrastructure.models.measurement_models import MeasurementModels
from domain.entities.body_measurements import BodyMeasurements


class PoseAnalysisService:
    def __init__(self, models_dir: Path):
        self.models_dir = models_dir
        self.pose_detector = PoseDetector(models_dir / "pose_landmarker_heavy.task")
        self.models = MeasurementModels(models_dir)
        self.measurement_service = MeasurementService(self.models)
        self.height_calibrator = HeightCalibrator()
    
    def analyze(self, request: PoseAnalysisRequest) -> Tuple[Optional[BodyMeasurements], Optional[str]]:
        # Decode image
        image = self._decode_image(request.image_bytes)
        if image is None:
            return None, "Format gambar tidak valid"
        
        # Detect pose
        result = self.pose_detector.detect(image)
        landmarks = self.pose_detector.get_landmarks(result)
        
        if landmarks is None:
            return None, "Tubuh tidak terdeteksi dalam gambar"
        
        if not self.pose_detector.are_shoulders_hips_visible(landmarks):
            return None, "Bahu dan pinggul tidak terlihat dengan jelas."
        
        # Get scale
        scale = self._get_scale(request, image, landmarks)
        if scale is None:
            return None, "Gagal menghitung skala. Pastikan posisi tegak dan seluruh tubuh terlihat di kamera."
        
        # Calculate measurements
        h, w = image.shape[:2]
        measurements = self.measurement_service.calculate(
            landmarks, w, h, scale,
            request.user_height_cm, request.dress_size_cm
        )
        
        if not measurements.is_valid():
            return None, "Hasil pengukuran tidak valid."
        
        return measurements, None
    
    def _get_scale(self, request: PoseAnalysisRequest, image: np.ndarray, 
                   landmarks: Any) -> Optional[float]:
        return self.height_calibrator.calibrate(
            landmarks, image.shape[1], image.shape[0], request.user_height_cm
        )
    
    def _decode_image(self, image_bytes: bytes) -> Optional[np.ndarray]:
        nparr = np.frombuffer(image_bytes, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    def close(self):
        self.pose_detector.close()