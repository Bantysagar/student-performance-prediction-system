from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "student_model.pkl"


def create_dataset(rows=1000, random_state=42):
    rng = np.random.default_rng(random_state)

    study_hours = rng.uniform(0, 10, rows)
    attendance = rng.uniform(40, 100, rows)
    previous_marks = rng.uniform(20, 100, rows)
    assignments_completed = rng.integers(0, 11, rows)
    sleep_hours = rng.uniform(3, 10, rows)
    internet_access = rng.choice(["Yes", "No"], rows, p=[0.78, 0.22])
    extracurricular = rng.choice(["Yes", "No"], rows, p=[0.45, 0.55])

    noise = rng.normal(0, 5, rows)

    final_score = (
        0.32 * previous_marks
        + 2.4 * study_hours
        + 0.22 * attendance
        + 1.8 * assignments_completed
        + 1.2 * sleep_hours
        + np.where(internet_access == "Yes", 4, -3)
        + np.where(extracurricular == "Yes", 1.5, 0)
        + noise
    )

    final_score = np.clip(final_score, 0, 100)

    data = pd.DataFrame(
        {
            "study_hours": study_hours.round(2),
            "attendance": attendance.round(2),
            "previous_marks": previous_marks.round(2),
            "assignments_completed": assignments_completed,
            "sleep_hours": sleep_hours.round(2),
            "internet_access": internet_access,
            "extracurricular": extracurricular,
            "final_score": final_score.round(2),
        }
    )

    return data


def train_model():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    data = create_dataset()

    features = [
        "study_hours",
        "attendance",
        "previous_marks",
        "assignments_completed",
        "sleep_hours",
        "internet_access",
        "extracurricular",
    ]

    target = "final_score"

    X = data[features]
    y = data[target]

    numeric_features = [
        "study_hours",
        "attendance",
        "previous_marks",
        "assignments_completed",
        "sleep_hours",
    ]

    categorical_features = [
        "internet_access",
        "extracurricular",
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical_features),
            ("numeric", "passthrough", numeric_features),
        ]
    )

    model = RandomForestRegressor(
        n_estimators=160,
        random_state=42,
        max_depth=12,
        min_samples_split=4,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
    )

    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    model_package = {
        "pipeline": pipeline,
        "features": features,
        "mae": round(float(mae), 3),
        "r2_score": round(float(r2), 3),
    }

    joblib.dump(model_package, MODEL_PATH)

    print("✅ Model trained successfully.")
    print(f"✅ Model saved at: {MODEL_PATH}")
    print(f"📊 MAE: {mae:.3f}")
    print(f"📊 R2 Score: {r2:.3f}")


if __name__ == "__main__":
    train_model()