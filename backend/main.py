from datetime import datetime
from pathlib import Path
import sqlite3
from typing import List

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

MODEL_PATH = PROJECT_DIR / "models" / "student_model.pkl"
DB_PATH = PROJECT_DIR / "data" / "predictions.db"

FRONTEND_DIR = PROJECT_DIR / "frontend"

if not FRONTEND_DIR.exists():
    FRONTEND_DIR = PROJECT_DIR / "Frontend"


app = FastAPI(
    title="Student Performance Prediction System",
    description="ML web app to predict student performance, pass/fail status, and risk level.",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StudentInput(BaseModel):
    student_name: str = Field(..., min_length=1, max_length=80)
    study_hours: float = Field(..., ge=0, le=24)
    attendance: float = Field(..., ge=0, le=100)
    previous_marks: float = Field(..., ge=0, le=100)
    assignments_completed: int = Field(..., ge=0, le=10)
    sleep_hours: float = Field(..., ge=0, le=24)
    internet_access: str
    extracurricular: str


class PredictionResponse(BaseModel):
    id: int
    student_name: str
    predicted_score: float
    status: str
    risk_level: str
    created_at: str


class HistoryItem(BaseModel):
    id: int
    student_name: str
    study_hours: float
    attendance: float
    previous_marks: float
    assignments_completed: int
    sleep_hours: float
    internet_access: str
    extracurricular: str
    predicted_score: float
    status: str
    risk_level: str
    created_at: str


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def create_tables():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                study_hours REAL NOT NULL,
                attendance REAL NOT NULL,
                previous_marks REAL NOT NULL,
                assignments_completed INTEGER NOT NULL,
                sleep_hours REAL NOT NULL,
                internet_access TEXT NOT NULL,
                extracurricular TEXT NOT NULL,
                predicted_score REAL NOT NULL,
                status TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        conn.commit()


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Model file not found. Run `python train_model.py` from the main project folder first."
        )

    return joblib.load(MODEL_PATH)


def get_status_and_risk(predicted_score):
    if predicted_score >= 40:
        status = "Pass"
    else:
        status = "Fail"

    if predicted_score >= 75:
        risk_level = "Low"
    elif predicted_score >= 50:
        risk_level = "Medium"
    else:
        risk_level = "High"

    return status, risk_level


@app.on_event("startup")
def startup_event():
    create_tables()
    print("✅ Database tables created.")


@app.get("/")
def serve_homepage():
    index_file = FRONTEND_DIR / "index.html"

    if not index_file.exists():
        raise HTTPException(status_code=404, detail="frontend/index.html not found.")

    return FileResponse(index_file)


@app.get("/style.css")
def serve_css():
    css_file = FRONTEND_DIR / "style.css"

    if not css_file.exists():
        raise HTTPException(status_code=404, detail="style.css not found.")

    return FileResponse(css_file)


@app.get("/script.js")
def serve_js():
    js_file = FRONTEND_DIR / "script.js"

    if not js_file.exists():
        raise HTTPException(status_code=404, detail="script.js not found.")

    return FileResponse(js_file)


if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/health")
def health_check():
    return {
        "status": "online",
        "message": "Backend is running successfully.",
    }


@app.post("/predict", response_model=PredictionResponse)
def predict_performance(student: StudentInput):
    try:
        internet_access = student.internet_access.strip().title()
        extracurricular = student.extracurricular.strip().title()

        if internet_access not in ["Yes", "No"]:
            raise HTTPException(status_code=400, detail="internet_access must be Yes or No.")

        if extracurricular not in ["Yes", "No"]:
            raise HTTPException(status_code=400, detail="extracurricular must be Yes or No.")

        model_package = load_model()
        pipeline = model_package["pipeline"]

        input_data = pd.DataFrame(
            [
                {
                    "study_hours": student.study_hours,
                    "attendance": student.attendance,
                    "previous_marks": student.previous_marks,
                    "assignments_completed": student.assignments_completed,
                    "sleep_hours": student.sleep_hours,
                    "internet_access": internet_access,
                    "extracurricular": extracurricular,
                }
            ]
        )

        predicted_score = float(pipeline.predict(input_data)[0])
        predicted_score = max(0, min(100, predicted_score))
        predicted_score = round(predicted_score, 2)

        status, risk_level = get_status_and_risk(predicted_score)
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO predictions (
                    student_name,
                    study_hours,
                    attendance,
                    previous_marks,
                    assignments_completed,
                    sleep_hours,
                    internet_access,
                    extracurricular,
                    predicted_score,
                    status,
                    risk_level,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    student.student_name,
                    student.study_hours,
                    student.attendance,
                    student.previous_marks,
                    student.assignments_completed,
                    student.sleep_hours,
                    internet_access,
                    extracurricular,
                    predicted_score,
                    status,
                    risk_level,
                    created_at,
                ),
            )

            conn.commit()
            prediction_id = cursor.lastrowid

        return PredictionResponse(
            id=prediction_id,
            student_name=student.student_name,
            predicted_score=predicted_score,
            status=status,
            risk_level=risk_level,
            created_at=created_at,
        )

    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error))

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {error}")


@app.get("/history", response_model=List[HistoryItem])
def get_prediction_history():
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM predictions
            ORDER BY id DESC
            LIMIT 50
            """
        )

        rows = cursor.fetchall()

    return [dict(row) for row in rows]


@app.delete("/history")
def clear_prediction_history():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM predictions")
        conn.commit()

    return {"message": "Prediction history cleared successfully."}