#!/usr/bin/env python3
"""
OS-dependent setup script for Interview Analyzer.
Handles installation of platform-specific dependencies.
"""

import platform
import subprocess
import sys
import os
from pathlib import Path

def get_os_type():
    """Detect current operating system."""
    system = platform.system()
    if system == 'Windows':
        return 'windows'
    elif system == 'Darwin':
        return 'macos'
    elif system == 'Linux':
        return 'linux'
    else:
        return 'unknown'

def install_requirements(os_type):
    """Install OS-specific requirements."""
    base_requirements = Path(__file__).parent / 'requirements.txt'
    os_requirements = Path(__file__).parent / f'requirements-{os_type}.txt'
    
    print(f"[*] Detected OS: {os_type}")
    print(f"[*] Installing base requirements from {base_requirements}...")
    
    if base_requirements.exists():
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', str(base_requirements)
        ])
    
    if os_requirements.exists():
        print(f"[*] Installing {os_type}-specific requirements from {os_requirements}...")
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', str(os_requirements)
        ])
    else:
        print(f"[!] Warning: No OS-specific requirements file found for {os_type}")
        print(f"[!] Expected: {os_requirements}")

def setup_backend_env(os_type):
    """Setup backend environment variables and paths."""
    env_file = Path(__file__).parent / 'backend' / '.env'
    
    if not env_file.exists():
        print(f"[*] Creating backend .env file...")
        env_content = f"""# Interview Analyzer - Backend Configuration
# OS: {os_type}
# Auto-generated during setup

# LLM Providers (set your API keys)
OPENAI_API_KEY=your_key_here
CLAUDE_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
DEEPSEEK_API_KEY=your_key_here

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# Backend Configuration
BACKEND_PORT=8000
BACKEND_HOST=127.0.0.1

# Encoding (especially important for Windows)
PYTHONIOENCODING=utf-8
PYTHONUTF8=1

# Audio Configuration
AUDIO_DEVICE_INDEX=-1
SAMPLE_RATE=16000
"""
        env_file.write_text(env_content)
        print(f"[+] Created {env_file}")
    else:
        print(f"[*] .env file already exists: {env_file}")

def setup_frontend():
    """Setup frontend dependencies."""
    electron_dir = Path(__file__).parent / 'electron'
    
    if not (electron_dir / 'node_modules').exists():
        print(f"[*] Installing Node.js dependencies...")
        subprocess.check_call(['npm', 'install'], cwd=str(electron_dir))
    else:
        print(f"[*] Node modules already installed")

def build_frontend():
    """Build frontend for production."""
    electron_dir = Path(__file__).parent / 'electron'
    print(f"[*] Building frontend...")
    subprocess.check_call(['npx', 'vite', 'build'], cwd=str(electron_dir))

def main():
    """Main setup routine."""
    print("=" * 60)
    print("Interview Analyzer - Setup Script")
    print("=" * 60)
    
    os_type = get_os_type()
    
    if os_type == 'unknown':
        print("[!] Error: Unknown operating system")
        sys.exit(1)
    
    try:
        print("\n[STEP 1/4] Installing Python dependencies...")
        install_requirements(os_type)
        
        print("\n[STEP 2/4] Setting up backend environment...")
        setup_backend_env(os_type)
        
        print("\n[STEP 3/4] Installing frontend dependencies...")
        setup_frontend()
        
        print("\n[STEP 4/4] Building frontend...")
        build_frontend()
        
        print("\n" + "=" * 60)
        print("[+] Setup completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Configure your API keys in backend/.env")
        print("2. Start backend: python backend/main.py")
        print("3. In another terminal, start frontend: npm start (from electron/)")
        print("4. Or run the app directly with: npm run electron")
        
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Error during setup: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
