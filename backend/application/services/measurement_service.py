import numpy as np
from typing import Any, Optional
from domain.entities.body_measurements import BodyMeasurements
from domain.value_objects.body_shape import BodyShape
from domain.value_objects.fit_type import FitType

class MeasurementService:
    def __init__(self, models):
        self.models = models
        # Margin kompensasi untuk estimasi antropometri 2D ke 3D
        self.SHOULDER_MARGIN = 1.15
        self.HIP_MARGIN = 1.35
    
    def calculate(self, landmarks: Any, image_width: int, image_height: int,
                  scale_cm_per_px: float, user_height_cm: float, 
                  dress_size_cm: float) -> BodyMeasurements:
        
        def distance_px(i1: int, i2: int) -> Optional[float]:
            try:
                p1 = landmarks[i1]
                p2 = landmarks[i2]
                dx = (p1.x - p2.x) * image_width
                dy = (p1.y - p2.y) * image_height
                return float(np.sqrt(dx*dx + dy*dy))
            except:
                return None
        
        def to_cm(px: float) -> float:
            return px * scale_cm_per_px
        
        # 1. Ekstraksi Fitur (Pixel)
        shoulder_px = distance_px(11, 12)
        hip_px = distance_px(23, 24)
        chest_px = self._chest_width_px(landmarks, image_width, image_height)
        
        # 2. Transformasi ke CM dengan Skala Tunggal (Height-Based)
        shoulder_cm = to_cm(shoulder_px) * self.SHOULDER_MARGIN if shoulder_px else None
        hip_cm = to_cm(hip_px) * self.HIP_MARGIN if hip_px else None
        chest_width_cm = to_cm(chest_px) if chest_px else None
        
        # 3. Estimasi Lingkar Dada (Menggunakan Regresi Ketebalan Tubuh)
        chest_circ_cm = None
        if chest_width_cm and user_height_cm > 0:
            thickness = self.models.predict_chest_thickness(chest_width_cm, user_height_cm)
            if thickness and thickness > 0:
                chest_circ_cm = self._ellipse_perimeter(chest_width_cm/2, thickness/2)
        
        # 4. Klasifikasi Bentuk Tubuh (KNN Model)
        shape = None
        if all([shoulder_cm, chest_width_cm, hip_cm]):
            shape_str = self.models.predict_shape(shoulder_cm, chest_width_cm, hip_cm, user_height_cm)
            if shape_str:
                try:
                    shape = BodyShape(shape_str)
                except ValueError:
                    shape = BodyShape.UNKNOWN
        
        # 5. Rekomendasi Fit (KNN Model)
        fit = None
        if chest_circ_cm and shoulder_cm:
            fit_str = self.models.predict_fit(chest_circ_cm, shoulder_cm, user_height_cm, dress_size_cm)
            if fit_str:
                try:
                    fit = FitType(fit_str)
                except ValueError:
                    fit = FitType.UNKNOWN
        
        return BodyMeasurements(
            shoulder_width_cm=shoulder_cm,
            hip_width_cm=hip_cm,
            chest_width_cm=chest_width_cm,
            chest_circumference_cm=chest_circ_cm,
            body_shape=shape,
            fit_recommendation=fit
        )
    
    def _chest_width_px(self, landmarks: Any, w: int, h: int) -> Optional[float]:
        try:
            left_shoulder = (landmarks[11].x * w, landmarks[11].y * h)
            right_shoulder = (landmarks[12].x * w, landmarks[12].y * h)
            left_hip = (landmarks[23].x * w, landmarks[23].y * h)
            right_hip = (landmarks[24].x * w, landmarks[24].y * h)
            chest_left_x = left_shoulder[0] + (left_hip[0] - left_shoulder[0]) * 0.25
            chest_right_x = right_shoulder[0] + (right_hip[0] - right_shoulder[0]) * 0.25
            return abs(chest_right_x - chest_left_x)
        except: return None
    
    def _ellipse_perimeter(self, a: float, b: float) -> Optional[float]:
        if a <= 0 or b <= 0: return None
        term = 3 * (a + b) - np.sqrt((3*a + b) * (a + 3*b))
        return float(np.pi * term)