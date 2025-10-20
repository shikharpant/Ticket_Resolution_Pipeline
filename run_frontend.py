#!/usr/bin/env python3
"""
Frontend Launcher for GST Grievance Resolution System
Launches the React development server with proper configuration
"""

import os
import sys
import subprocess
import signal
from pathlib import Path

def check_dependencies():
    """Check if Node.js and npm are installed"""
    try:
        # Check Node.js
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Node.js is not installed. Please install Node.js first.")
            print("   Download from: https://nodejs.org/")
            return False

        node_version = result.stdout.strip()
        print(f"✅ Node.js found: {node_version}")

        # Check npm
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ npm is not installed.")
            return False

        npm_version = result.stdout.strip()
        print(f"✅ npm found: {npm_version}")

        return True

    except FileNotFoundError:
        print("❌ Node.js/npm not found. Please install Node.js first.")
        print("   Download from: https://nodejs.org/")
        return False

def install_dependencies():
    """Install npm dependencies if needed"""
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
                print(f"❌ Failed to install dependencies:")
                print(result.stderr)
                return False

            print("✅ Dependencies installed successfully")

        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing dependencies: {e}")
            return False
    else:
        print("✅ Dependencies already installed")

    return True

def start_frontend():
    """Start the React development server"""
    frontend_dir = Path(__file__).parent / "frontend"

    if not frontend_dir.exists():
        print(f"❌ Frontend directory not found: {frontend_dir}")
        return False

    print("🚀 Starting React development server...")
    print("   Frontend will be available at: http://localhost:3000")
    print("   Backend API should be running at: http://localhost:8000")
    print("\n💡 Press Ctrl+C to stop the server")

    try:
        # Start the development server
        process = subprocess.Popen(
            ['npm', 'run', 'dev'],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        # Handle graceful shutdown
        def signal_handler(sig, frame):
            print("\n🛑 Shutting down development server...")
            process.terminate()
            process.wait()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Stream output
        for line in process.stdout:
            print(line.rstrip())

    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting development server: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return True

    return True

def main():
    """Main launcher function"""
    print("🎯 GST Grievance Resolution System - Frontend Launcher")
    print("=" * 60)

    # Change to project directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Install dependencies if needed
    if not install_dependencies():
        sys.exit(1)

    # Start the frontend server
    if not start_frontend():
        sys.exit(1)

if __name__ == "__main__":
    main()