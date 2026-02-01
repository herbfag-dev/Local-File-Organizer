#!/usr/bin/env python3
"""
Launcher script for the Local File Organizer Reflex GUI.
Run this script to start the web-based dashboard.
"""

import subprocess
import sys
import os

def main():
    """Launch the Reflex web application."""
    print("=" * 60)
    print("Local File Organizer - Reflex GUI Dashboard")
    print("=" * 60)
    print("\nStarting the web application...")
    print("The dashboard will open in your default web browser.")
    print("\nPress Ctrl+C to stop the application.\n")
    
    try:
        # Run reflex in the current directory
        subprocess.run([sys.executable, "-m", "reflex", "run"], check=True)
    except KeyboardInterrupt:
        print("\n\nShutting down the application...")
        print("Thank you for using Local File Organizer!")
    except Exception as e:
        print(f"\nError starting the application: {e}")
        print("\nPlease ensure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        sys.exit(1)

if __name__ == "__main__":
    main()
