# pyrefly: ignore [missing-import]
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Any

from application.dto.pose_analysis_request import PoseAnalysisRequest, CalibrationType
from application.services.measurement_service import MeasurementService
from infrastructure.mediapipe.pose_detector import PoseDetector
from infrastructure.calibration.height_calibrator import HeightCalibrator
from infrastructure.calibration.reference_calibrator import ReferenceCalibrator
from infrastructure.models.measurement_models import MeasurementModels
from domain.entities.body_measurements import BodyMeasurements


class PoseAnalysisService:
    def __init__(self, models_dir: Path):
        self.models_dir = models_dir
        self.pose_detector = PoseDetector(models_dir / "pose_landmarker_heavy.task")
        self.models = MeasurementModels(models_dir)
        self.measurement_service = MeasurementService(self.models)
        self.height_calibrator = HeightCalibrator()
        self.reference_calibrator = ReferenceCalibrator()
    
    def analyze(self, request: PoseAnalysisRequest) -> Tuple[Optional[BodyMeasurements], Optional[str]]:
        # Decode image
        image = self._decode_image(request.image_bytes)
        if image is None:
            return None, "Invalid image format"
        
        # Detect pose
        result = self.pose_detector.detect(image)
        landmarks = self.pose_detector.get_landmarks(result)
        
        if landmarks is None:
            return None, "No pose detected in image"
        
        if not self.pose_detector.are_shoulders_hips_visible(landmarks):
            return None, "Shoulders and hips must be visible"
        
        # Get scale
        scale = self._get_scale(request, image, landmarks)
        if scale is None:
            return None, "Calibration failed. Ensure body is fully visible."
        
        # Calculate measurements
        h, w = image.shape[:2]
        measurements = self.measurement_service.calculate(
            landmarks, w, h, scale,
            request.user_height_cm, request.dress_size_cm
        )
        
        if not measurements.is_valid():
            return None, "Measurements outside reasonable range"
        
        return measurements, None
    
    def _get_scale(self, request: PoseAnalysisRequest, image: np.ndarray, 
                   landmarks: Any) -> Optional[float]:
        
        if request.calibration_type == CalibrationType.HEIGHT:
            h, w = image.shape[:2]
            return self.height_calibrator.calibrate(
                landmarks, w, h, request.calibration_value_cm
            )
        
        # REFERENCE method using user-drawn line length on the frontend
        elif request.calibration_type == CalibrationType.REFERENCE:
            if request.reference_pixel_length and request.reference_pixel_length > 0:
                scale = request.calibration_value_cm / request.reference_pixel_length
                print(f"[PoseService] Reference scale: {request.calibration_value_cm}cm / {request.reference_pixel_length:.1f}px = {scale:.6f} cm/px")
                if 0.005 <= scale <= 2.0:
                    return scale
                print(f"[PoseService] !! Reference scale out of range: {scale:.6f} (expected 0.005-2.0)")
            else:
                print("[PoseService] !! Reference pixel length missing or zero")
            return None
            
        # REFERENCE_AUTO method using automatic card detection
        elif request.calibration_type == CalibrationType.REFERENCE_AUTO:
            scale = self.reference_calibrator.calibrate(image, request.calibration_value_cm, landmarks)
            # Perspective correction has been removed. 
            # Because the instructions tell the user to hold the card flat against their chest,
            # applying a Z-depth difference based on the bent wrist artificially inflated the scale by up to ~25%.
            return scale
        
        return None
    
    def _decode_image(self, image_bytes: bytes) -> Optional[np.ndarray]:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img if img is not None else None
    
    def close(self):
        self.pose_detector.close()