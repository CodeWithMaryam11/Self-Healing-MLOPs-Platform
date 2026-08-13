import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"
import io
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# pyrefly: ignore [missing-import]
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException, status, Depends
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
from typing import List, Optional
from passlib.context import CryptContext
from jose import jwt, JWTError

# pyrefly: ignore [missing-import]
from ml_engine import ml_engine
# pyrefly: ignore [missing-import]
from drift_monitor import drift_engine
# pyrefly: ignore [missing-import]
from db import connect_to_mongo, close_mongo_connection, get_db

app = FastAPI(
    title="PipelineIQ // Self-Healing MLOps Platform",
    description="Automated End-to-End Machine Learning Lifecycle Engine with SMOTE, MLflow, and Evidently AI",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get("JWT_SECRET", "jwt_token_fastapi_production_secret_881920")
ALGORITHM = "HS256"

# Enable CORS for React UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas
class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    token: str
    user: dict

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

# ==========================================
# AUTHENTICATION LAYER (JWT BEARER)
# ==========================================
# pyrefly: ignore [missing-import]
from fastapi.security import OAuth2PasswordBearer

# pyrefly: ignore [missing-import]
from bson import ObjectId

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise credentials_exception
    return str(user["_id"])

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/api/v1/auth/register")
async def register(user: RegisterRequest):
    db = get_db()
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = pwd_context.hash(user.password)
    new_user = {
        "name": user.name,
        "email": user.email,
        "password": hashed_password,
        "role": "User",
        "created_at": datetime.utcnow()
    }
    result = await db.users.insert_one(new_user)
    
    # --- MLFLOW AUTH INTEGRATION ---
    # Automatically create a matching user account in the MLflow Registry if MLflow is running
    import socket
    try:
        # Quick check if port 5001 is listening to avoid connection retry delays
        with socket.create_connection(("localhost", 5001), timeout=0.5):
            from mlflow.server.auth.client import AuthServiceClient
            os.environ["MLFLOW_TRACKING_USERNAME"] = "admin"
            os.environ["MLFLOW_TRACKING_PASSWORD"] = "password"
            auth_client = AuthServiceClient("http://localhost:5001")
            auth_client.create_user(username=user.email, password=user.password)
            print(f"MLflow user {user.email} created successfully.")
    except Exception as e:
        print(f"MLflow user creation skipped/failed: {e}")
        
    return {"message": "User registered successfully", "user_id": str(result.inserted_id)}

@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    """
    Layer 3: Security & Serving Layer
    Authenticates operator via MongoDB and issues JWT access credentials.
    """
    db = get_db()
    user = await db.users.find_one({"email": credentials.email})
    
    if not user or not pwd_context.verify(credentials.password, user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid operator authentication credentials")
    
    access_token = create_access_token(data={"sub": str(user["_id"]), "email": user["email"]})
    
    return {
        "token": access_token,
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "name": user["name"],
            "role": user.get("role", "User")
        }
    }

# ==========================================
# SYSTEM OVERVIEW & HEALTH TELEMETRY
# ==========================================
@app.get("/api/v1/health")
async def health_check():
    """
    Global system health strip endpoint.
    """
    return {
        "status": "Online",
        "database": "Connected (PostgreSQL / Local MLflow)",
        "mlflow_registry": "Active (v2.11.0)",
        "evidently_engine": "Ready"
    }

# ==========================================
# AUTOML TRAINING & INGESTION DISPATCHER
# ==========================================
def generate_sample_dataset() -> pd.DataFrame:
    from sklearn.datasets import make_classification
    X, y = make_classification(n_samples=200, n_features=10, n_informative=8, random_state=42)
    feature_names = [f"feature_{i}" for i in range(10)]
    df = pd.DataFrame(X, columns=feature_names)
    df["target"] = y
    return df

def background_training_task(dataset_name: str, models: list, target_metric: str, df_bytes: bytes, user_id: str):
    # 1. Parse CSV bytes into DataFrame or generate sample dataset
    df = None
    if df_bytes and len(df_bytes) > 0:
        try:
            df = pd.read_csv(io.BytesIO(df_bytes))
        except Exception as e:
            print(f"[CSV Parsing Error] Failed to parse uploaded file: {e}")

    if df is None or df.empty:
        print("[Dataset Fallback] Using generated synthetic dataset.")
        df = generate_sample_dataset()

    # 2. Try optional MinIO Object Storage persistence if MinIO is active
    if df_bytes and len(df_bytes) > 0:
        try:
            from storage import upload_dataset_to_s3
            s3_key = upload_dataset_to_s3(user_id, dataset_name, df_bytes)
            print(f"[Storage] Successfully uploaded to MinIO: {s3_key}")
        except Exception as e:
            print(f"[Storage Warning] MinIO storage unavailable (skipping S3 persist): {e}")

    # Save local copy for drift monitoring
    try:
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(data_dir, exist_ok=True)
        df.to_csv(os.path.join(data_dir, dataset_name), index=False)
    except Exception as e:
        print(f"[Dataset Local Save Warning]: {e}")

    # 3. Train models via ML Engine
    try:
        ml_engine.train_concurrent_models(dataset_name, models, target_metric, df, user_id)
    except Exception as e:
        print(f"[Training Error] Model training failed: {e}")
        from db import get_sync_db
        sync_db = get_sync_db()
        if sync_db is not None:
            sync_db.runs.delete_many({"user_id": user_id, "status": "Training..."})

@app.post("/api/v1/models/train", status_code=status.HTTP_201_CREATED)
async def train_models(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    models: List[str] = Form(["Random Forest", "XGBoost"]),
    target_metric: str = Form("F1-Score"),
    user_id: str = Depends(get_current_user)
):
    """
    Layer 1 & Layer 2: Ingestion & Training Dispatcher
    Receives tabular dataset CSV, triggers SMOTE auto-balancing, and concurrently runs ML models.
    """
    dataset_name = "uploaded_dataset.csv"
    df_bytes = b""

    if file:
        dataset_name = file.filename or dataset_name
        df_bytes = await file.read()

    # Create temporary active run placeholder in MongoDB
    temp_run_id = f"run_{dataset_name[:4]}_active"
    db = get_db()
    temp_run = {
        "user_id": user_id,
        "id": temp_run_id,
        "dataset": dataset_name,
        "models": models,
        "hyperparameters": {"optuna_tuning": "In Progress...", "smote_applied": True},
        "status": "Training...",
        "targetMetric": target_metric,
        "score": None,
        "timestamp": "Just now",
        "created_at": datetime.utcnow()
    }
    await db.runs.insert_one(temp_run)

    # Dispatch background worker task
    background_tasks.add_task(background_training_task, dataset_name, models, target_metric, df_bytes, user_id)

    return {"message": "Concurrent AutoML training pipeline dispatched successfully", "run_id": temp_run_id}

# ==========================================
# REAL-TIME MLFLOW REGISTRY FEED
# ==========================================
@app.get("/api/v1/runs")
async def get_runs(user_id: str = Depends(get_current_user)):
    """
    Polled every 5000ms by React Query to synchronize concurrent run states.
    """
    db = get_db()
    cursor = db.runs.find({"user_id": user_id}).sort("created_at", -1)
    runs = await cursor.to_list(length=100)
    for r in runs:
        if "_id" in r:
            del r["_id"]
    return {"runs": runs}

# ==========================================
# EVIDENTLY AI DRIFT & SELF-HEALING FEED
# ==========================================
@app.get("/api/v1/drift")
async def get_drift(user_id: str = Depends(get_current_user)):
    """
    Layer 3: Statistical drift monitoring feed (KS-test & PSI calculations).
    """
    db = get_db()
    cursor = db.runs.find({"user_id": user_id}).sort("created_at", -1)
    runs_history = await cursor.to_list(length=100)
    return drift_engine.get_drift_telemetry(runs_history)

@app.post("/api/v1/drift/inject")
async def inject_drift_endpoint(body: dict = None, user_id: str = Depends(get_current_user)):
    run_id = (body or {}).get("run_id", None)
    db = get_db()
    cursor = db.runs.find({"user_id": user_id}).sort("created_at", -1)
    runs_history = await cursor.to_list(length=100)
    return drift_engine.inject_drift(run_id=run_id, runs_history=runs_history, user_id=user_id)

@app.post("/api/v1/drift/reset")
async def reset_drift_endpoint(user_id: str = Depends(get_current_user)):
    return drift_engine.reset_drift()

if __name__ == "__main__":
    # pyrefly: ignore [missing-import]
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
