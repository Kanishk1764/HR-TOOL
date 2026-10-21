import os
import sys
import uvicorn

if __name__ == "__main__":
    # Ensure current directory is at the front of sys.path
    root_dir = os.path.dirname(os.path.abspath(__file__))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)

    # Load environment variables from .env file (with fallback)
    for env_path in [os.path.join(root_dir, ".env"), os.path.join(root_dir, "backend", ".env")]:
        if os.path.exists(env_path):
            try:
                from dotenv import load_dotenv
                load_dotenv(env_path)
            except ImportError:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            os.environ.setdefault(k.strip(), v.strip().strip("'\""))

    print("=" * 65)
    print("🚀 Starting Resume Intelligence & Vacancy Matcher API")
    print("📍 URL: http://127.0.0.1:8000")
    print("📖 Docs: http://127.0.0.1:8000/docs")
    print("=" * 65)

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
