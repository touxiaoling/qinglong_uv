import subprocess

subprocess.run(["pyside6-uic", "./qinglong_ui/main.ui", "-o", "./qinglong_ui/ui_main.py"])
#subprocess.run(["pyside6-uic", "./scrcpy_ui/main.ui", "-o", "./scrcpy_ui/ui_main.py"])
