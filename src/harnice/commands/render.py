import os
from harnice import harness_prechecker  # assuming you want to call into here

def run_harness():
    print("🔍 Searching for harness config...")
    for filename in ["harnice.yaml", "harness.yaml"]:
        if os.path.exists(filename):
            print(f"📂 Found {filename}")
            confirm = input("⚙️  Run harness precheck? [Y/n] ").strip().lower()
            if confirm in ("", "y", "yes"):
                harness_prechecker.run(filename)
                return
            else:
                print("❌ Cancelled.")
                return
    print("❌ No harness file found in CWD.")

def run_system():
    print("🧠 System-level rendering not yet implemented.")
