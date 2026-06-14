"""
Build script for OpenSeismo Lite Desktop EXE
Creates a standalone Windows executable with PyInstaller
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and report status"""
    print(f"\n{'='*60}")
    print(f"[BUILD] {description}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"\n❌ Error: {description} failed")
        return False
    print(f"✅ {description} completed")
    return True

def main():
    print("\n" + "="*60)
    print("OpenSeismo Lite Desktop EXE Builder")
    print("="*60)
    
    # Get current directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Step 1: Install dependencies
    if not run_command(
        f'"{sys.executable}" -m pip install --upgrade pip',
        "Upgrading pip"
    ):
        return False
    
    if not run_command(
        f'"{sys.executable}" -m pip install -r requirements.txt',
        "Installing Python dependencies"
    ):
        return False
    
    if not run_command(
        f'"{sys.executable}" -m pip install pyinstaller',
        "Installing PyInstaller"
    ):
        return False
    
    # Step 2: Build EXE using PyInstaller
    if not run_command(
        f'"{sys.executable}" -m PyInstaller --onefile desktop_app.spec',
        "Building desktop application EXE"
    ):
        return False
    
    # Step 3: Check output
    exe_path = Path("dist") / "OpenSeismo Lite.exe"
    if exe_path.exists():
        exe_size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n✅ SUCCESS! Desktop EXE created: {exe_path}")
        print(f"   File size: {exe_size_mb:.1f} MB")
        print(f"\n🚀 To run: Double-click 'OpenSeismo Lite.exe' in the dist/ folder")
    else:
        print(f"\n❌ ERROR: EXE not found at {exe_path}")
        return False
    
    print("\n" + "="*60)
    print("Build Complete!")
    print("="*60)
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
