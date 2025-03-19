"""
    Written by TotallyNotK0
    Last updated: March 18, 2025

    This is an example plugin for Construct that integrates an AI assistant as a
    dockable panel. It utilizes tgpt to send inputs and receive outputs. It was
    originally created to test the implementation of plugin support, as well as
    the capabilities and possibilities plugins have.

    Permission is granted to repurpose this script as a foundation to build your
    own, with or without credit.
"""

import os
import sys
import tempfile
import subprocess
import requests
from PyQt5.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QTextEdit, QShortcut, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QKeySequence

TGPT_URL = "https://github.com/aandrew-me/tgpt/releases/download/v2.9.1/tgpt-amd64.exe"

class DownloadWorker(QThread):
    downloadFinished = pyqtSignal(str, str)

    def run(self):
        try:
            temp_dir = tempfile.gettempdir()
            tgpt_path = os.path.join(temp_dir, "tgpt-amd64.exe")
            if not os.path.exists(tgpt_path):
                r = requests.get(TGPT_URL, stream=True)
                r.raise_for_status()
                with open(tgpt_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            self.downloadFinished.emit(tgpt_path, "")
        except Exception as e:
            self.downloadFinished.emit("", str(e))

class TgptWorker(QThread):
    outputReady = pyqtSignal(str)

    def __init__(self, tgpt_path, prompt, parent=None):
        super().__init__(parent)
        self.tgpt_path = tgpt_path
        self.prompt = prompt

    def run(self):
        try:
            cmd = [self.tgpt_path, "--provider", "duckduckgo", "--quiet", f'"""{self.prompt}"""']
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode != 0:
                output = f"Error: {result.stderr}"
            else:
                output = result.stdout
            self.outputReady.emit(output)
        except Exception as e:
            self.outputReady.emit(f"Exception: {str(e)}")

class AIInputField(QTextEdit):
    sendSignal = pyqtSignal()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
            self.sendSignal.emit()
        else:
            super().keyPressEvent(event)

class AIPanel(QWidget):
    def __init__(self, tgpt_path, parent=None):
        super().__init__(parent)
        self.tgpt_path = tgpt_path
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.outputText = QTextEdit(self)
        self.outputText.setReadOnly(True)
        self.inputField = AIInputField(self)
        self.inputField.setPlaceholderText("Type your prompt here then hit Enter to send")
        self.layout.addWidget(self.outputText)
        self.layout.addWidget(self.inputField)
        self.setLayout(self.layout)
        self.inputField.sendSignal.connect(self.handleSend)

    def handleSend(self):
        prompt = self.inputField.toPlainText().strip()
        if prompt:
            self.outputText.append(">> " + prompt)
            self.inputField.clear()
            self.worker = TgptWorker(self.tgpt_path, prompt)
            self.worker.outputReady.connect(self.displayOutput)
            self.worker.start()

    def displayOutput(self, output):
        self.outputText.append(output)

def register_plugin(app_context):
    main_window = app_context.get("main_window")
    if main_window is None:
        return
    ai_menu = main_window.menuBar().addMenu("AI Assistant")
    open_action = ai_menu.addAction("Open AI Assistant")
    open_action.setShortcut("Ctrl+Shift+A")
    shortcut = QShortcut(QKeySequence("Ctrl+Shift+A"), main_window)

    def open_ai_panel():
        if hasattr(main_window, "ai_dock") and main_window.ai_dock is not None:
            main_window.ai_dock.show()
            main_window.ai_dock.raise_()
        else:
            def on_download_finished(tgpt_path, error):
                if error:
                    QMessageBox.critical(main_window, "Download Error", f"Failed to download tgpt:\n{error}")
                else:
                    ai_panel = AIPanel(tgpt_path, parent=main_window)
                    dock = QDockWidget("AI Assistant", main_window)
                    dock.setWidget(ai_panel)
                    dock.setAllowedAreas(Qt.RightDockWidgetArea)
                    main_window.addDockWidget(Qt.RightDockWidgetArea, dock)
                    main_window.ai_dock = dock
                    main_window.tgpt_downloader = None

            downloader = DownloadWorker()
            main_window.tgpt_downloader = downloader
            downloader.downloadFinished.connect(on_download_finished)
            downloader.start()

    open_action.triggered.connect(open_ai_panel)
    shortcut.activated.connect(open_ai_panel)
