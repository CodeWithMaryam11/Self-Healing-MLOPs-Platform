import os
import subprocess
import sys

# Set the required secret key for MLflow Basic Auth CSRF protection
os.environ["MLFLOW_FLASK_SERVER_SECRET_KEY"] = "supersecret"

print("Starting MLflow server with basic-auth on port 5001...")
subprocess.run([
    sys.executable, "-m", "mlflow", "server",
    "--app-name", "basic-auth",
    "--backend-store-uri", "sqlite:///mlflow.db",
    "--port", "5001"
])
