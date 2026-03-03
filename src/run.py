import argparse
import subprocess
import sys
import os
import logging
from dotenv import load_dotenv


load_dotenv()
back_end_port = int(os.getenv('FAST_API_PORT'))
front_end_port = int(os.getenv('GRADIO_PORT'))
deploy_mode = os.getenv('DEPLOY_MODE')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_backend(alt=False):
    """Start the FastAPI backend server"""
    logging.info("Starting backend server...")
    try:
        logging.info(f"You can now access the backend API on http://127.0.0.1:{back_end_port}")
        cmd = [sys.executable, "src/api.py"]
        if alt:
            cmd.append("--alt")
        subprocess.run(cmd, check=True) 
    except subprocess.CalledProcessError as e:
        logging.error(f"Error starting backend server: {e}")
        sys.exit(1)

def run_frontend():
    """Start the Gradio frontend server"""
    logging.info("Starting frontend server...")
    try:
        logging.info(f"You can access the web application on http://127.0.0.1:{front_end_port}")
        subprocess.run([sys.executable, "src/app.py"], check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error starting frontend server: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Run Quest PDF Tools servers")
    parser.add_argument(
        "--mode",
        choices=["backend", "full"],
        default="full",
        help="Run mode: 'backend' for API only, 'full' for both frontend and backend (default: full)"
    )
    parser.add_argument(
        "--alt",
        action="store_true",
        default=False,
        help="Use alternative pymupdf4llm-based text extraction for section extraction"
    )

    args = parser.parse_args()

    if args.mode == "backend":
        run_backend(alt=args.alt)
    else:  # full mode
        # Start backend in a separate process
        logging.info(f"You can now access the backend API on http://127.0.0.1:{back_end_port}")
        backend_cmd = [sys.executable, "src/api.py"]
        if args.alt:
            backend_cmd.append("--alt")
        backend_process = subprocess.Popen(backend_cmd)
        try:
            # Start frontend (this will block until frontend is closed)
            run_frontend()
        finally:
            # Ensure backend is terminated when frontend exits
            backend_process.terminate()
            backend_process.wait()

if __name__ == "__main__":
    main()