import sys
import subprocess
from pathlib import Path

print("[1/3] Cleaning up V1 shadow files...")
shadow_files = [
    "src/gui/main_window.py",
    "src/gui_app.py",
    "src/app.py",
    "src/search_app.py",
    "src/watch_app.py",
    "src/run.py"
]

for f in shadow_files:
    p = Path(f)
    if p.exists():
        p.unlink()
        print(f"  Deleted: {f}")

print("\n[2/3] Fixing Qt6 enum in video_drop_zone.py...")
vz = Path("src/gui/components/video_drop_zone.py")
if vz.exists():
    text = vz.read_text(encoding="utf-8")
    if "SemiBold" in text:
        text = text.replace("QFont.Weight.SemiBold", "QFont.Weight.DemiBold")
        vz.write_text(text, encoding="utf-8")
        print("  Fixed QFont.Weight.SemiBold -> DemiBold")
    else:
        print("  Already fixed or not found.")
else:
    print("  video_drop_zone.py not found.")

print("\n[3/3] Launching DesktopAI V2...")
print("="*50)
subprocess.run([sys.executable, "src/main.py", "--mock-ai"])