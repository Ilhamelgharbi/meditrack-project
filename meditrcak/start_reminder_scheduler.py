#!/usr/bin/env python3
"""
Start the Automated Reminder Scheduler
This script starts the background reminder system that automatically:
- Generates reminders from schedules
- Processes and sends WhatsApp reminders
- Handles responses

Usage:
python start_reminder_scheduler.py
"""

import sys
import os
import subprocess
import signal
import time

def start_scheduler():
    """Start the automated reminder scheduler in the background"""
    print("🚀 Starting Automated Reminder Scheduler...")

    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    scheduler_script = os.path.join(script_dir, "automated_reminder_scheduler.py")

    try:
        # Start the scheduler as a background process
        process = subprocess.Popen(
            [sys.executable, scheduler_script],
            cwd=script_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        print(f"✅ Scheduler started with PID: {process.pid}")
        print("📱 WhatsApp reminders will now be sent automatically!")
        print("⏰ Reminders are generated daily and processed every 5 minutes")
        print("")
        print("Press Ctrl+C to stop the scheduler...")

        # Wait for the process
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping scheduler...")
            process.terminate()
            process.wait()
            print("✅ Scheduler stopped")

    except Exception as e:
        print(f"❌ Failed to start scheduler: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(start_scheduler())