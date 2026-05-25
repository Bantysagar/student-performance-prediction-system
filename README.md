# Student Performance Prediction System

An ML-based web application to predict student performance, pass/fail status, and academic risk level using academic inputs.

## Features

- Predicts student final score
- Predicts pass/fail status
- Shows low, medium, or high risk level
- Stores prediction history in SQLite
- Simple frontend using HTML, CSS, and JavaScript
- FastAPI backend
- Machine learning model using Scikit-learn

## Technologies Used

- Python
- FastAPI
- Scikit-learn
- Pandas
- NumPy
- SQLite
- HTML
- CSS
- JavaScript

## How to Run

1. Create virtual environment:

python -m venv venv

2. Activate virtual environment:

Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned

.\venv\Scripts\Activate.ps1

3. Install dependencies:

pip install -r requirements.txt

4. Train ML model:

python train_model.py

5. Start backend:

cd backend

python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

6. Open app:

http://127.0.0.1:8000
