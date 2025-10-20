#!/usr/bin/env python3
"""
Full System Launcher for GST Grievance Resolution System
Launches both backend FastAPI server and React frontend simultaneously
"""

import os
import sys
import subprocess
import signal
import time
import threading
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking system dependencies...")

    # Check Python
    try:
        result = subprocess.run([sys.executable, '--version'], capture_output=True, text=True)
        print(f"✅ Python: {result.stdout.strip()}")
    except Exception as e:
        print(f"❌ Python error: {e}")
        return False

    # Check Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Node.js is not installed. Please install Node.js first.")
            return False
        print(f"✅ Node.js: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ Node.js not found. Please install Node.js first.")
        return False

    # Check npm
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ npm is not installed.")
            return False
        print(f"✅ npm: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ npm not found.")
        return False

    return True

def check_environment():
    """Check if environment variables are set"""
    print("🔍 Checking environment configuration...")

    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        print("⚠️  .env file not found. Creating a template...")
        env_template = """# GST Grievance Resolution System - Environment Variables

# Required API Keys
GOOGLE_API_KEY=your_google_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Optional Settings
EMBEDDING_DEVICE=auto  # auto, cpu, mps, cuda
LOG_LEVEL=INFO
"""
        try:
            with open(env_file, 'w') as f:
                f.write(env_template)
            print("✅ .env template created. Please add your API keys.")
        except Exception as e:
            print(f"❌ Failed to create .env template: {e}")
            return False
    else:
        print("✅ .env file found")

    return True

def install_python_dependencies():
    """Install Python dependencies"""
    requirements_file = Path(__file__).parent / "requirements.txt"

    if not requirements_file.exists():
        print("⚠️  requirements.txt not found. Skipping Python dependencies.")
        return True

    print("📦 Checking Python dependencies...")
    try:
        # Check if requirements are satisfied
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ Failed to install Python dependencies:")
            print(result.stderr)
            return False

        print("✅ Python dependencies installed/verified")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing Python dependencies: {e}")
        return False

def install_frontend_dependencies():
    """Install frontend dependencies"""
    frontend_dir = Path(__file__).parent / "frontend"

    if not frontend_dir.exists():
        print(f"❌ Frontend directory not found: {frontend_dir}")
        return False

    # Check if node_modules exists
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        print("📦 Installing frontend dependencies...")
        try:
            result = subprocess.run(
                ['npm', 'install'],
                cwd=frontend_dir,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                print(f"❌ Failed to install frontend dependencies:")
                print(result.stderr)
                return False

            print("✅ Frontend dependencies installed successfully")

        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing frontend dependencies: {e}")
            return False
    else:
        print("✅ Frontend dependencies already installed")

    return True

def start_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting FastAPI backend server...")

    backend_process = None
    try:
        backend_process = subprocess.Popen(
            [sys.executable, 'backend_server.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        return backend_process

    except Exception as e:
        print(f"❌ Failed to start backend server: {e}")
        return None

def start_frontend():
    """Start the React development server"""
    print("🚀 Starting React frontend server...")

    frontend_dir = Path(__file__).parent / "frontend"
    frontend_process = None

    try:
        frontend_process = subprocess.Popen(
            ['npm', 'run', 'dev'],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        return frontend_process

    except Exception as e:
        print(f"❌ Failed to start frontend server: {e}")
        return None

def monitor_processes(backend_process, frontend_process):
    """Monitor and display output from both processes"""
    print("\n🎯 Full System Started Successfully!")
    print("=" * 60)
    print("📍 Frontend: http://localhost:3000")
    print("📍 Backend API: http://localhost:8000")
    print("📍 API Docs: http://localhost:8000/docs")
    print("\n💡 Press Ctrl+C to stop both servers")
    print("=" * 60)

    def stream_output(process, name):
        """Stream output from a process"""
        try:
            for line in process.stdout:
                print(f"[{name}] {line.rstrip()}")
        except Exception:
            pass

    # Start threads to monitor output
    backend_thread = threading.Thread(
        target=stream_output,
        args=(backend_process, "BACKEND")
    )
    frontend_thread = threading.Thread(
        target=stream_output,
        args=(frontend_process, "FRONTEND")
    )

    backend_thread.daemon = True
    frontend_thread.daemon = True

    backend_thread.start()
    frontend_thread.start()

    # Wait for processes to complete or interrupt
    try:
        while backend_process.poll() is None and frontend_process.poll() is None:
            time.sleep(1)

        if backend_process.poll() is not None:
            print("❌ Backend server stopped unexpectedly")
        if frontend_process.poll() is not None:
            print("❌ Frontend server stopped unexpectedly")

    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")

def main():
    """Main launcher function"""
    print("🎯 GST Grievance Resolution System - Full System Launcher")
    print("=" * 60)

    # Change to project directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # Check all dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install missing dependencies.")
        sys.exit(1)

    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed.")
        sys.exit(1)

    # Install dependencies
    print("\n📦 Installing/verifying dependencies...")
    if not install_python_dependencies():
        print("\n❌ Python dependency installation failed.")
        sys.exit(1)

    if not install_frontend_dependencies():
        print("\n❌ Frontend dependency installation failed.")
        sys.exit(1)

    print("\n✅ All dependencies verified successfully!")

    # Start servers
    print("\n🚀 Starting servers...")

    # Start backend first
    backend_process = start_backend()
    if not backend_process:
        print("\n❌ Failed to start backend server.")
        sys.exit(1)

    # Give backend time to start
    time.sleep(2)

    # Start frontend
    frontend_process = start_frontend()
    if not frontend_process:
        print("\n❌ Failed to start frontend server.")
        backend_process.terminate()
        sys.exit(1)

    # Set up signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down servers...")
        if backend_process:
            backend_process.terminate()
        if frontend_process:
            frontend_process.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Monitor processes
    try:
        monitor_processes(backend_process, frontend_process)
    except KeyboardInterrupt:
        pass
    finally:
        # Clean up processes
        if backend_process:
            backend_process.terminate()
            backend_process.wait()
        if frontend_process:
            frontend_process.terminate()
            frontend_process.wait()

if __name__ == "__main__":
    main()