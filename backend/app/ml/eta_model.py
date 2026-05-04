import logging
import math
import os
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Feature order used for both training and inference
FEATURE_NAMES = [
    "distance_km",
    "vessel_type",
    "speed_knots",
    "num_segments",
    "time_of_day",
    "season",
]


def build_feature_vector(
    distance_km: float,
    vessel_type: int,
    speed_knots: float,
    num_segments: int,
    time_of_day: int = 12,
    season: int = 1,
) -> np.ndarray:
    """Return a 1-D feature array ready for model prediction."""
    return np.array(
        [distance_km, vessel_type, speed_knots, num_segments, time_of_day, season],
        dtype=np.float32,
    ).reshape(1, -1)


def _formula_eta(
    distance_km: float,
    vessel_type: int,
    speed_knots: float,
    time_of_day: int = 12,
) -> float:
    """Simple physics-based fallback when no ML model is available."""
    speed_kmh = speed_knots * 1.852
    vessel_factor = {0: 1.0, 1: 1.1, 2: 1.2}.get(vessel_type, 1.0)
    time_factor = 1.0 + 0.1 * math.sin(time_of_day * math.pi / 12)
    if speed_kmh <= 0:
        return float("inf")
    return (distance_km / speed_kmh) * 60.0 * vessel_factor * time_factor


class ETAModel:
    def __init__(self):
        self._model = None

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load(self, filepath: str) -> None:
        """Load a joblib model from *filepath*."""
        import joblib

        if not os.path.exists(filepath):
            logger.warning("ETA model file not found: %s – will use fallback formula", filepath)
            return
        self._model = joblib.load(filepath)
        logger.info("ETA model loaded from %s", filepath)

    def save(self, filepath: str) -> None:
        """Save the current model to *filepath* using joblib."""
        import joblib

        if self._model is None:
            raise RuntimeError("No model to save.")
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        joblib.dump(self._model, filepath)
        logger.info("ETA model saved to %s", filepath)

    def is_loaded(self) -> bool:
        return self._model is not None

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict(self, features: dict) -> float:
        """Predict travel time in minutes.

        *features* keys: distance_km, vessel_type, speed_knots,
        num_segments, time_of_day, season.
        Falls back to the physics formula when the model is not loaded.
        """
        distance_km = float(features.get("distance_km", 0.0))
        vessel_type = int(features.get("vessel_type", 0))
        speed_knots = float(features.get("speed_knots", 7.0))
        num_segments = int(features.get("num_segments", 1))
        time_of_day = int(features.get("time_of_day", 12))
        season = int(features.get("season", 1))

        if not self.is_loaded():
            logger.debug("ETA model not loaded – using formula fallback")
            return _formula_eta(distance_km, vessel_type, speed_knots, time_of_day)

        X = build_feature_vector(
            distance_km, vessel_type, speed_knots, num_segments, time_of_day, season
        )
        try:
            prediction = float(self._model.predict(X)[0])
            return max(prediction, 0.0)
        except Exception as exc:
            logger.error("Model prediction failed: %s – using formula fallback", exc)
            return _formula_eta(distance_km, vessel_type, speed_knots, time_of_day)
