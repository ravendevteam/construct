@echo off
set FileVersion=1.0.0.1
set ProductVersion=1.4.0.0

python -m nuitka --onefile --standalone --enable-plugins=pyqt5 --remove-output --windows-console-mode=disable --output-dir=dist --output-filename=Construct.exe --follow-imports --windows-icon-from-ico=ICON.ico --include-data-files=style.css=style.css --include-data-files=construct.png=construct.png --product-name="Construct" --company-name="Raven Development Team" --file-description="Simple, fast, and professional code editor." --file-version=%FileVersion% --product-version=%ProductVersion% --copyright="Copyright (c) 2025 Raven Development Team" --onefile-tempdir-spec="{CACHE_DIR}\RavenDevelopmentTeam\Construct\{VERSION}" construct.py
pause