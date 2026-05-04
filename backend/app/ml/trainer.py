import logging
import math
import os
from typing import Dict, Tuple

import numpy as np

logger = logging.getLogger(__name__)

_DEFAULT_MODEL_PATH = "data/eta_model.joblib"
_N_SAMPLES = 5_000
_RANDOM_SEED = 42


def _generate_training_data(n_samples: int = _N_SAMPLES):
    """Generate synthetic waterway routing training data."""
    rng = np.random.default_rng(_RANDOM_SEED)

    distance_km = rng.uniform(1.0, 500.0, n_samples)
    vessel_type = rng.integers(0, 3, n_samples)        # 0=small, 1=medium, 2=large
    speed_knots = rng.uniform(3.0, 15.0, n_samples)
    num_segments = rng.integers(1, 51, n_samples)
    time_of_day = rng.integers(0, 24, n_samples)
    season = rng.integers(1, 5, n_samples)             # 1-4

    # Physics-based target
    speed_kmh = speed_knots * 1.852
    vessel_factors = np.where(vessel_type == 0, 1.0, np.where(vessel_type == 1, 1.1, 1.2))
    time_factors = 1.0 + 0.1 * np.sin(time_of_day * math.pi / 12)
    eta_minutes = (distance_km / speed_kmh) * 60.0 * vessel_factors * time_factors

    # 5 % Gaussian noise
    noise = rng.normal(0.0, 0.05 * eta_minutes, n_samples)
    eta_minutes = np.maximum(eta_minutes + noise, 0.5)

    X = np.column_stack(
        [distance_km, vessel_type, speed_knots, num_segments, time_of_day, season]
    ).astype(np.float32)
    y = eta_minutes.astype(np.float32)
    return X, y


def train_eta_model(
    model_path: str = _DEFAULT_MODEL_PATH,
) -> Tuple[object, Dict[str, float]]:
    """Train an ETA regression model on synthetic waterway data.

    Returns the trained model and a dict with MAE and RMSE metrics.
    Saves the model to *model_path*.
    """
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    from sklearn.model_selection import train_test_split

    logger.info("Generating %d synthetic training samples…", _N_SAMPLES)
    X, y = _generate_training_data()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=_RANDOM_SEED
    )

    model = _fit_model(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(mean_squared_error(y_test, y_pred) ** 0.5)
    metrics = {"mae": round(mae, 3), "rmse": round(rmse, 3)}
    logger.info("Training complete – MAE=%.3f min  RMSE=%.3f min", mae, rmse)

    # Persist
    import joblib

    os.makedirs(os.path.dirname(model_path) or ".", exist_ok=True)
    joblib.dump(model, model_path)
    logger.info("Model saved to %s", model_path)

    return model, metrics


def _fit_model(X_train, y_train):
    """Try XGBoost first; fall back to RandomForestRegressor."""
    try:
        from xgboost import XGBRegressor

        model = XGBRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=_RANDOM_SEED,
            n_jobs=-1,
            verbosity=0,
        )
        model.fit(X_train, y_train)
        logger.info("Trained XGBRegressor")
        return model
    except ImportError:
        logger.warning("XGBoost not available – falling back to RandomForestRegressor")

    from sklearn.ensemble import RandomForestRegressor

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=10,
        random_state=_RANDOM_SEED,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    logger.info("Trained RandomForestRegressor")
    return model
