"""
    Written by TotallyNotK0
    Last updated: March 18, 2025

    This is an example plugin for Construct that allows you to run Python scripts
    within it. It was originally created to test the implementation of plugin
    support, as well as the capabilities and possibilities plugins have.

    Permission is granted to repurpose this script as a foundation to build your
    own, with or without credit.
"""

import sys
import os
import tempfile
from PyQt5.QtWidgets import QAction, QDialog, QVBoxLayout, QTextEdit, QPushButton, QMessageBox
from PyQt5.QtCore import QProcess

class OutputDialog(QDialog):
    def __init__(self, output, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Script Output")
        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setText(output)
        layout.addWidget(self.text_edit)
        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

def run_python_script():
    main_window = run_python_script.main_window
    editor = main_window.currentEditor()
    if not editor:
        QMessageBox.warning(main_window, "No Editor", "No active editor to run script from.")
        return
    code = editor.text()
    if not code.strip():
        QMessageBox.warning(main_window, "Empty Script", "The current script is empty.")
        return
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8")
    temp_file.write(code)
    temp_file.close()
    temp_path = temp_file.name
    process = QProcess(main_window)
    output_chunks = []

    def append_output():
        std_out = process.readAllStandardOutput().data().decode('utf-8')
        std_err = process.readAllStandardError().data().decode('utf-8')
        if std_out:
            output_chunks.append(std_out)
        if std_err:
            output_chunks.append(std_err)

    process.readyReadStandardOutput.connect(append_output)
    process.readyReadStandardError.connect(append_output)

    def on_finished(exitCode, exitStatus):
        try:
            os.unlink(temp_path)
        except Exception:
            pass
        full_output = "".join(output_chunks)
        OutputDialog(full_output, parent=main_window).exec_()
        if process in main_window.run_processes:
            main_window.run_processes.remove(process)

    process.finished.connect(on_finished)
    if not hasattr(main_window, "run_processes"):
        main_window.run_processes = []
    main_window.run_processes.append(process)
    process.start(sys.executable, [temp_path])
    if not process.waitForStarted(3000):
        QMessageBox.warning(main_window, "Execution Failed", "Failed to start the script process.")

def register_plugin(app_context):
    main_window = app_context.get("main_window")
    if not main_window:
        return
    run_python_script.main_window = main_window
    run_action = QAction("Run Python Script", main_window)
    run_action.setShortcut("Ctrl+Shift+R")
    run_action.triggered.connect(run_python_script)
    menubar = main_window.menuBar()
    run_menu = menubar.findChild(type(menubar), "RunMenu")
    if not run_menu:
        run_menu = menubar.addMenu("Run")
        run_menu.setObjectName("RunMenu")
    run_menu.addAction(run_action)