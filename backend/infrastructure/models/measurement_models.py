import joblib
import numpy as np
from pathlib import Path
from typing import Optional


class MeasurementModels:
    """
    Load and run the trained ML models for body measurement prediction.

    Feature order contracts (must match training data):
    - regression (tebal dada):  [lebar_dada, tinggi_badan]
    - shape KNN:                [lebar_bahu, lebar_dada, lebar_pinggang, tinggi_badan]
    - fit KNN:                  [ld_user, bahu_user, tinggi_user, ld_baju]
    """

    def __init__(self, models_dir: Path):
        self.models_dir = models_dir
        self.regression   = self._load("model_regresi_tebal.pkl")
        self.shape_model  = self._load("model_knn_shape.pkl")
        self.fit_model    = self._load("model_knn_fit.pkl")
        self.shape_scaler = self._load("scaler_shape.pkl")
        self.fit_scaler   = self._load("scaler_fit.pkl")

    def _load(self, filename: str) -> Optional[object]:
        path = self.models_dir / filename
        if path.exists():
            try:
                return joblib.load(path)
            except Exception as e:
                print(f"[MeasurementModels] WARNING: Could not load {filename}: {e}")
        else:
            print(f"[MeasurementModels] WARNING: Model file not found: {path}")
        return None

    def predict_chest_thickness(self, chest_width_cm: float, height_cm: float) -> Optional[float]:
        """
        Predict chest depth/thickness from lateral chest width and user height.
        Model features: [lebar_dada, tinggi_badan]
        """
        if self.regression is None:
            print("[MeasurementModels] predict_chest_thickness: regression model not loaded")
            return None
        try:
            # Match training feature order: lebar_dada, tinggi_badan
            result = self.regression.predict([[chest_width_cm, height_cm]])
            thickness = float(result[0])
            print(f"[MeasurementModels] chest_thickness: width={chest_width_cm:.1f}, height={height_cm:.1f} -> {thickness:.2f}cm")
            return thickness
        except Exception as e:
            print(f"[MeasurementModels] predict_chest_thickness ERROR: {e}")
            return None

    def predict_shape(self, shoulder_cm: float, chest_width_cm: float,
                      hip_cm: float, height_cm: float) -> Optional[str]:
        """
        Predict body shape category using KNN classifier.
        Model features: [lebar_bahu, lebar_dada, lebar_pinggang, tinggi_badan]
        Possible outputs: 'Apple', 'Inverted Triangle', 'Rectangle'
        """
        if self.shape_model is None or self.shape_scaler is None:
            print("[MeasurementModels] predict_shape: model or scaler not loaded")
            return None
        try:
            # Match training feature order: lebar_bahu, lebar_dada, lebar_pinggang, tinggi_badan
            features = np.array([[shoulder_cm, chest_width_cm, hip_cm, height_cm]])
            scaled = self.shape_scaler.transform(features)
            label = str(self.shape_model.predict(scaled)[0])
            print(f"[MeasurementModels] body_shape: shoulder={shoulder_cm:.1f}, chest={chest_width_cm:.1f}, "
                  f"hip={hip_cm:.1f}, height={height_cm:.1f} -> '{label}'")
            return label
        except Exception as e:
            print(f"[MeasurementModels] predict_shape ERROR: {e}")
            return None

    def predict_fit(self, chest_circ_cm: float, shoulder_cm: float,
                    height_cm: float, dress_size_cm: float) -> Optional[str]:
        """
        Predict clothing fit recommendation using KNN classifier.
        Model features: [ld_user, bahu_user, tinggi_user, ld_baju]
          - ld_user     = user chest circumference (lingkar dada)
          - bahu_user   = user shoulder width
          - tinggi_user = user height
          - ld_baju     = target garment chest size (lingkar dada baju)
        Possible outputs: 'Regular Fit', 'Oversize Fit', 'Tight Fit', 'Not Recommended'
        """
        if self.fit_model is None or self.fit_scaler is None:
            print("[MeasurementModels] predict_fit: model or scaler not loaded")
            return None
        try:
            # Match training feature order: ld_user, bahu_user, tinggi_user, ld_baju
            features = np.array([[chest_circ_cm, shoulder_cm, height_cm, dress_size_cm]])
            scaled = self.fit_scaler.transform(features)
            label = str(self.fit_model.predict(scaled)[0])
            print(f"[MeasurementModels] fit_recommendation: ld_user={chest_circ_cm:.1f}, "
                  f"bahu={shoulder_cm:.1f}, tinggi={height_cm:.1f}, ld_baju={dress_size_cm:.1f} -> '{label}'")
            return label
        except Exception as e:
            print(f"[MeasurementModels] predict_fit ERROR: {e}")
            return None