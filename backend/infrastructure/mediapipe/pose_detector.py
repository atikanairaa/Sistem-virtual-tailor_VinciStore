# pyrefly: ignore [missing-import]
import cv2
import mediapipe as mp
import numpy as np
from pathlib import Path
from typing import Any, Optional, Tuple
# pyrefly: ignore [missing-import]
from mediapipe.tasks import python as tasks_python
# pyrefly: ignore [missing-import]
from mediapipe.tasks.python import vision

class PoseDetector:
    """MediaPipe pose detector wrapper"""
    
    def __init__(self, model_path: Path):
        self.model_path = model_path
        self._ensure_model_exists()
        self.landmarker = self._create_landmarker()
    
    def _ensure_model_exists(self):
        if not self.model_path.exists():
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task"
            import urllib.request
            print(f"Downloading model to {self.model_path}...")
            urllib.request.urlretrieve(url, self.model_path)
            print("Model downloaded successfully")
    
    def _create_landmarker(self):
        base_options = tasks_python.BaseOptions(model_asset_path=str(self.model_path))
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        return vision.PoseLandmarker.create_from_options(options)
    
    def detect(self, image: np.ndarray) -> Any:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        return self.landmarker.detect(mp_image)
    
    def get_landmarks(self, result: Any) -> Optional[Any]:
        if result and result.pose_landmarks:
            return result.pose_landmarks[0]
        return None
    
    def are_shoulders_hips_visible(self, landmarks: Any) -> bool:
        if not landmarks or len(landmarks) <= 24:
            return False
        
        def visible(idx: int) -> bool:
            try:
                lm = landmarks[idx]
                return 0 <= lm.x <= 1 and 0 <= lm.y <= 1
            except:
                return False
        
        return visible(11) and visible(12) and visible(23) and visible(24)
    
    def close(self):
        if hasattr(self, 'landmarker'):
            self.landmarker.close()