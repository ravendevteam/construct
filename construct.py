""" Import the necessary modules for the program to work """
import sys
import os
import importlib.util
import requests
import validators
import chardet
from chardet.universaldetector import UniversalDetector
import urllib.parse
import git

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QAction, QFileDialog, QMessageBox, QStatusBar,
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QInputDialog,
    QTextEdit, QDockWidget, QTreeView, QWidget, QTabWidget, QMenu
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QSettings, QModelIndex
from PyQt5.QtGui import QIcon, QFont, QFontMetrics, QColor, QFontDatabase
from PyQt5.Qsci import QsciScintilla, QsciLexerPython, QsciLexerHTML, QsciLexerCPP
try:
    from PyQt5.Qsci import QsciLexerJavaScript
except ImportError:
    QsciLexerJavaScript = None
try:
    from PyQt5.Qsci import QsciLexerCSS
except ImportError:
    QsciLexerCSS = None
try:
    from PyQt5.Qsci import QsciLexerJava
except ImportError:
    QsciLexerJava = None
try:
    from PyQt5.Qsci import QsciLexerSQL
except ImportError:
    QsciLexerSQL = None
try:
    from PyQt5.Qsci import QsciLexerLua
except ImportError:
    QsciLexerLua = None
try:
    from PyQt5.Qsci import QsciLexerMarkdown
except ImportError:
    QsciLexerMarkdown = None
try:
    from PyQt5.Qsci import QsciLexerRuby
except ImportError:
    QsciLexerRuby = None
try:
    from PyQt5.Qsci import QsciLexerXML
except ImportError:
    QsciLexerXML = None
try:
    from PyQt5.Qsci import QsciLexerBatch
except ImportError:
    QsciLexerBatch = None



""" Utility function to load plugins

This function checks for a "constructplugins" directory located in your user folder.
If the folder doesn't exist, it creates it. It then loads every Python file in the
folder (ignoring files starting with an underscore) and, if the module defines a
"register_plugin(app_context)" function, calls it. The app_context is a dictionary
containing a reference to the main window, so plugins can integrate with Construct
(e.g., by adding menu items). Plugins should be written in Python. They do not
require a separate Python installation.
"""
def load_plugins(app_context):
    import os
    import importlib.util
    user_home = os.path.expanduser("~")
    plugins_dir = os.path.join(user_home, "constructplugins")
    os.makedirs(plugins_dir, exist_ok=True)
    loaded_plugins = []
    for filename in os.listdir(plugins_dir):
        if filename.endswith(".py") and not filename.startswith("_"):
            plugin_path = os.path.join(plugins_dir, filename)
            mod_name = os.path.splitext(filename)[0]
            spec = importlib.util.spec_from_file_location(mod_name, plugin_path)
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
                if hasattr(module, "register_plugin"):
                    module.register_plugin(app_context)
                    loaded_plugins.append(mod_name)
                    print(f"Plugin '{mod_name}' loaded successfully from {plugins_dir}")
            except Exception as e:
                print(f"Failed to load plugin '{filename}' from {plugins_dir}: {e}")
    return loaded_plugins



""" Utility function to set the code editor font """
def get_preferred_font():
    db = QFontDatabase()
    if "Cascadia Code" in db.families():
        family = "Cascadia Code"
    elif "Courier New" in db.families():
        family = "Courier New"
    elif "Courier" in db.families():
        family = "Courier"
    else:
        family = "monospace"
    return QFont(family, 10)



""" Worker thread for fetching online content """
class WebFetcher(QThread):
    resultFetched = pyqtSignal(str, str)
    def __init__(self, url):
        super().__init__()
        self.url = url
    def run(self):
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            self.resultFetched.emit(response.text, "")
        except Exception as e:
            self.resultFetched.emit("", str(e))



""" File Handling Thread  """
class FileHandler(QThread):
    file_content_loaded = pyqtSignal(str, str, object)
    def __init__(self, file_path, tab):
        super().__init__()
        self.file_path = file_path
        self.tab = tab
    def run(self):
        detector = UniversalDetector()
        try:
            with open(self.file_path, 'rb') as file:
                while True:
                    chunk = file.read(1024)
                    if not chunk:
                        break
                    detector.feed(chunk)
                    if detector.done:
                        break
                detector.close()
            encoding = detector.result['encoding'] or 'utf-8'
            content = ""
            with open(self.file_path, 'r', encoding=encoding, errors='replace') as file:
                chunk_size = 1024 * 1024
                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break
                    content += chunk
            self.file_content_loaded.emit(content, encoding, self.tab)
        except Exception as e:
            self.file_content_loaded.emit(f"Error reading file: {e}", '', self.tab)



""" Code Editor widget  """
class CodeEditor(QsciScintilla):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.preferred_font = get_preferred_font()
        self.setFont(self.preferred_font)
        self.setMarginsFont(self.preferred_font)
        self._margin_font = QFont(self.preferred_font)
        self._margin_font.setBold(False)
        self.setMarginsFont(self._margin_font)
        self.marginPadding = 6
        fm = QFontMetrics(self._margin_font)
        self.setMarginWidth(0, fm.width("9") + self.marginPadding)
        self.setMarginType(0, QsciScintilla.NumberMargin)
        self.setMarginsBackgroundColor(QColor("#F0F0F0"))
        self.setWrapMode(QsciScintilla.WrapNone)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.adjust_scroll_bar_policy()
        self.setAutoCompletionThreshold(1)
        self.setAutoCompletionSource(QsciScintilla.AcsAll)
        self.setAutoCompletionCaseSensitivity(True)
        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)
        self.setIndentationGuides(True)
        self.setTabWidth(4)
        self.setIndentationsUseTabs(False)
        self.lexer = None
        self.textChanged.connect(self.update_line_number_margin)
        self.textChanged.connect(self.adjust_scroll_bar_policy)
        self.setEolMode(QsciScintilla.EolUnix)

    def update_line_number_margin(self):
        total_lines = self.lines()
        digits = len(str(total_lines if total_lines > 0 else 1))
        fm = QFontMetrics(self._margin_font)
        new_width = fm.width("9" * digits) + self.marginPadding
        self.setMarginWidth(0, new_width)

    def adjust_scroll_bar_policy(self):
        if self.text() == "":
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        else:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def setLexerForFile(self, file_name):
        ext = os.path.splitext(file_name)[1].lower()
        lexer = None
        if ext == ".py":
            lexer = QsciLexerPython()
        elif ext in [".html", ".htm"]:
            lexer = QsciLexerHTML()
        elif ext in [".cpp", ".c", ".h", ".hpp"]:
            lexer = QsciLexerCPP()
        elif ext == ".js" and QsciLexerJavaScript:
            lexer = QsciLexerJavaScript()
        elif ext == ".css" and QsciLexerCSS:
            lexer = QsciLexerCSS()
        elif ext == ".java" and QsciLexerJava:
            lexer = QsciLexerJava()
        elif ext == ".sql" and QsciLexerSQL:
            lexer = QsciLexerSQL()
        elif ext == ".lua" and QsciLexerLua:
            lexer = QsciLexerLua()
        elif ext == ".md":
            if QsciLexerMarkdown is not None:
                lexer = QsciLexerMarkdown()
            else:
                lexer = QsciLexerCPP()
        elif ext == ".rb":
            if QsciLexerRuby is not None:
                lexer = QsciLexerRuby()
            else:
                lexer = QsciLexerCPP()
        elif ext == ".xml":
            if QsciLexerXML is not None:
                lexer = QsciLexerXML()
            else:
                lexer = QsciLexerCPP()
        elif ext in [".bat", ".cmd"]:
            if QsciLexerBatch is not None:
                lexer = QsciLexerBatch()
            else:
                lexer = QsciLexerCPP()
        else:
            lexer = QsciLexerCPP()
        if lexer:
            lexer.setDefaultFont(self.preferred_font)
            try:
                count = lexer.styleCount()
            except AttributeError:
                count = None
            if count is not None:
                for style in range(count):
                    lexer.setFont(self.preferred_font, style)
            else:
                for style in range(128):
                    try:
                        lexer.setFont(self.preferred_font, style)
                    except Exception:
                        break
            self.setLexer(lexer)
            self.lexer = lexer
        else:
            self.setLexer(None)
        return lexer

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_A and event.modifiers() == Qt.ControlModifier:
            self.selectAll()
            return
        super().keyPressEvent(event)

    def select_all_text(self):
        self.selectAll()



""" Create a widget that represents a single editor tab """
class EditorTab(QWidget):
    def __init__(self, file_path=None):
        super().__init__()
        self.file_path = file_path
        self.encoding = "UTF-8"
        self.unsaved_changes = False
        self.file_handler = None
        self.editor = CodeEditor(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.editor)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.editor.textChanged.connect(self.on_text_changed)

    def on_text_changed(self):
        self.editor.setModified(True)
        self.unsaved_changes = True
        self.window().updateStatusBar()

    def setContent(self, content, encoding):
        self.editor.setText(content)
        self.editor.setModified(False)
        self.encoding = encoding
        self.unsaved_changes = False

    def setLexerForCurrentFile(self):
        if self.file_path:
            self.editor.setLexerForFile(self.file_path)



""" Create a class for the find and replace dialog """
class FindReplaceDialog(QDialog):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.setWindowTitle("Find and Replace")
        self.layout = QVBoxLayout(self)
        self.find_label = QLabel("Find:")
        self.find_input = QLineEdit(self)
        self.layout.addWidget(self.find_label)
        self.layout.addWidget(self.find_input)
        self.replace_label = QLabel("Replace with:")
        self.replace_input = QLineEdit(self)
        self.layout.addWidget(self.replace_label)
        self.layout.addWidget(self.replace_input)
        self.button_layout = QHBoxLayout()
        self.find_button = QPushButton("Find Next", self)
        self.replace_button = QPushButton("Replace", self)
        self.replace_all_button = QPushButton("Replace All", self)
        self.button_layout.addWidget(self.find_button)
        self.button_layout.addWidget(self.replace_button)
        self.button_layout.addWidget(self.replace_all_button)
        self.layout.addLayout(self.button_layout)
        self.find_button.clicked.connect(self.find_next)
        self.replace_button.clicked.connect(self.replace)
        self.replace_all_button.clicked.connect(self.replace_all)

    def find_next(self):
        search_text = self.find_input.text().strip()
        if search_text:
            found = self.editor.findFirst(search_text, False, False, False, True)
            if not found:
                QMessageBox.information(self, "Not Found", "No more occurrences found.")
        else:
            QMessageBox.warning(self, "Empty Search", "Please enter text to find.")

    def replace(self):
        search_text = self.find_input.text()
        replace_text = self.replace_input.text()
        if search_text:
            if self.editor.hasSelectedText() and self.editor.selectedText() == search_text:
                self.editor.replaceSelectedText(replace_text)
            else:
                found = self.editor.findFirst(search_text, False, False, False, True)
                if found:
                    self.editor.replaceSelectedText(replace_text)
                else:
                    QMessageBox.information(self, "Not Found", "Text not found.")
        else:
            QMessageBox.warning(self, "Empty Search", "Please enter text to find.")

    def replace_all(self):
        search_text = self.find_input.text()
        replace_text = self.replace_input.text()
        if search_text:
            content = self.editor.text()
            new_content = content.replace(search_text, replace_text)
            self.editor.setText(new_content)
        else:
            QMessageBox.warning(self, "Empty Search", "Please enter text to find.")



""" Create a class for the import From web dialog """
class ImportFromWebDialog(QDialog):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.setWindowTitle("Import From Web")
        self.layout = QVBoxLayout(self)
        self.url_label = QLabel("Enter URL:")
        self.url_input = QLineEdit(self)
        self.layout.addWidget(self.url_label)
        self.layout.addWidget(self.url_input)
        self.fetch_button = QPushButton("Fetch", self)
        self.layout.addWidget(self.fetch_button)
        self.fetch_button.clicked.connect(self.fetch_from_web)
        self.fetcher = None

    def fetch_from_web(self):
        url = self.url_input.text().strip()
        if self.is_valid_url(url):
            self.fetch_button.setEnabled(False)
            self.fetcher = WebFetcher(url)
            self.fetcher.resultFetched.connect(self.handleFetchResult)
            self.fetcher.start()
        else:
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid HTTPS URL.")

    def handleFetchResult(self, content, error):
        self.fetch_button.setEnabled(True)
        if error:
            QMessageBox.critical(self, "Error", f"Failed to fetch content: {error}")
        else:
            self.editor.setText(content)
            parsed = urllib.parse.urlparse(self.url_input.text().strip())
            if parsed.path:
                self.editor.setLexerForFile(parsed.path)
            self.accept()

    def is_valid_url(self, url):
        return validators.url(url) and url.startswith("https://")



""" Create a class for the unsaved changes dialog """
class UnsavedWorkDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("Unsaved Changes")
        self.layout = QVBoxLayout(self)
        self.message_label = QLabel("You have unsaved changes. What would you like to do?")
        self.layout.addWidget(self.message_label)
        self.button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Changes", self)
        self.cancel_button = QPushButton("Cancel", self)
        self.discard_button = QPushButton("Discard Changes", self)
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.discard_button)
        self.layout.addLayout(self.button_layout)
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.discard_button.clicked.connect(self.discard_changes)

    def discard_changes(self):
        self.done(2)



""" Create a class for the main window """
class ConstructWindow(QMainWindow):
    def __init__(self, file_to_open=None):
        super().__init__()
        self.current_folder = None
        self.repo = None
        self.plugins = []
        self.loadRecentFiles()
        self.fileTreeDock = None
        self.initUI()
        if file_to_open:
            self.load_file_on_startup(file_to_open)

    def initUI(self):
        self.setWindowTitle('Construct - Unnamed')
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon('construct.png'))
        self.tabWidget = QTabWidget(self)
        self.tabWidget.setTabsClosable(True)
        self.tabWidget.tabCloseRequested.connect(self.closeTab)
        self.setCentralWidget(self.tabWidget)
        self.tabWidget.currentChanged.connect(self.updateStatusBar)
        self.statusBar = QStatusBar(self)
        self.setStatusBar(self.statusBar)
        self.createMenu()
        self.newFile()

    def currentTab(self):
        return self.tabWidget.currentWidget()

    def currentEditor(self):
        tab = self.currentTab()
        if tab:
            return tab.editor
        return None

    def on_text_changed(self):
        tab = self.currentTab()
        if tab:
            tab.unsaved_changes = True
            self.updateStatusBar()

    def updateStatusBar(self, index=None):
        tab = self.currentTab()
        if tab and tab.editor:
            line, index = tab.editor.getCursorPosition()
            char_count = len(tab.editor.text())
            asterisk = "*" if tab.editor.isModified() else ""
            branch_info = ""
            if self.repo:
                try:
                    branch_info = f" | Branch: {self.repo.active_branch.name}"
                except Exception:
                    branch_info = ""
            self.statusBar.showMessage(
                f"Line: {line+1} | Column: {index+1} | Chars: {char_count} | Encoding: {tab.encoding}{branch_info} {asterisk}"
            )
            if tab.file_path:
                self.setWindowTitle(f"Construct - {os.path.basename(tab.file_path)}")
            else:
                self.setWindowTitle("Construct - Unnamed")
        else:
            self.statusBar.clearMessage()
            self.setWindowTitle("Construct - Unnamed")

    def createMenu(self):
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        self.createFileActions(fileMenu)
        editMenu = menubar.addMenu('&Edit')
        self.createEditActions(editMenu)
        gitMenu = menubar.addMenu('&Git')
        self.createGitActions(gitMenu)

    def createFileActions(self, menu):
        newAction = QAction('New', self)
        newAction.setShortcut('Ctrl+N')
        newAction.triggered.connect(self.newFile)
        menu.addAction(newAction)
        openAction = QAction('Open File...', self)
        openAction.setShortcut('Ctrl+O')
        openAction.triggered.connect(self.openFile)
        menu.addAction(openAction)
        openFolderAction = QAction('Open Folder...', self)
        openFolderAction.setShortcut('Ctrl+Shift+O')
        openFolderAction.triggered.connect(self.openFolder)
        menu.addAction(openFolderAction)
        saveAction = QAction('Save', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.triggered.connect(self.saveFile)
        menu.addAction(saveAction)
        saveAsAction = QAction('Save As...', self)
        saveAsAction.setShortcut('Ctrl+Shift+S')
        saveAsAction.triggered.connect(self.saveFileAs)
        menu.addAction(saveAsAction)
        importAction = QAction('Import From Web...', self)
        importAction.setShortcut('Ctrl+I')
        importAction.triggered.connect(self.importFromWeb)
        menu.addAction(importAction)
        exitAction = QAction('Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(self.close)
        menu.addAction(exitAction)
        menu.addSeparator()
        self.recentFilesMenu = menu.addMenu('Recently Opened Files')
        self.recentFilesMenu.aboutToShow.connect(self.updateRecentFilesMenu)
        self.updateRecentFilesMenu()

    def createEditActions(self, menu):
        undoAction = QAction('Undo', self)
        undoAction.setShortcut('Ctrl+Z')
        undoAction.triggered.connect(lambda: self.currentEditor() and self.currentEditor().undo())
        menu.addAction(undoAction)
        redoAction = QAction('Redo', self)
        redoAction.setShortcut('Ctrl+Y')
        redoAction.triggered.connect(lambda: self.currentEditor() and self.currentEditor().redo())
        menu.addAction(redoAction)
        cutAction = QAction('Cut', self)
        cutAction.setShortcut('Ctrl+X')
        cutAction.triggered.connect(lambda: self.currentEditor() and self.currentEditor().cut())
        menu.addAction(cutAction)
        copyAction = QAction('Copy', self)
        copyAction.setShortcut('Ctrl+C')
        copyAction.triggered.connect(lambda: self.currentEditor() and self.currentEditor().copy())
        menu.addAction(copyAction)
        pasteAction = QAction('Paste', self)
        pasteAction.setShortcut('Ctrl+V')
        pasteAction.triggered.connect(lambda: self.currentEditor() and self.currentEditor().paste())
        menu.addAction(pasteAction)
        selectAllAction = QAction('Select All', self)
        selectAllAction.setShortcut('Ctrl+A')
        selectAllAction.triggered.connect(lambda: self.currentEditor() and self.currentEditor().select_all_text())
        menu.addAction(selectAllAction)
        findReplaceAction = QAction('Find and Replace...', self)
        findReplaceAction.setShortcut('Ctrl+F')
        findReplaceAction.triggered.connect(self.openFindReplaceDialog)
        menu.addAction(findReplaceAction)

    def createGitActions(self, menu):
        openRepoAction = QAction("Open Repository...", self)
        openRepoAction.setShortcut("Ctrl+Alt+R")
        openRepoAction.triggered.connect(self.openRepository)
        menu.addAction(openRepoAction)
        statusAction = QAction("Status", self)
        statusAction.setShortcut("Ctrl+Alt+S")
        statusAction.triggered.connect(self.gitStatus)
        menu.addAction(statusAction)
        stageAction = QAction("Stage All Changes", self)
        stageAction.setShortcut("Ctrl+Alt+A")
        stageAction.triggered.connect(self.stageAllChanges)
        menu.addAction(stageAction)
        commitAction = QAction("Commit", self)
        commitAction.setShortcut("Ctrl+Alt+C")
        commitAction.triggered.connect(self.commitChanges)
        menu.addAction(commitAction)
        pushAction = QAction("Push", self)
        pushAction.setShortcut("Ctrl+Alt+P")
        pushAction.triggered.connect(self.pushChanges)
        menu.addAction(pushAction)
        pullAction = QAction("Pull", self)
        pullAction.setShortcut("Ctrl+Alt+L")
        pullAction.triggered.connect(self.pullChanges)
        menu.addAction(pullAction)
        branchAction = QAction("Switch Branch...", self)
        branchAction.setShortcut("Ctrl+Alt+B")
        branchAction.triggered.connect(self.switchBranch)
        menu.addAction(branchAction)

    def showLoadedPlugins(self):
        plugins_list = self.plugins if hasattr(self, "plugins") else []
        if plugins_list:
            plugins_str = "\n".join(plugins_list)
        else:
            plugins_str = "No plugins loaded."
        QMessageBox.information(self, "Loaded Plugins", plugins_str)

    def newFile(self):
        new_tab = EditorTab()
        self.tabWidget.addTab(new_tab, "Untitled")
        self.tabWidget.setCurrentWidget(new_tab)
        self.updateStatusBar()

    def openFolder(self):
        folder = QFileDialog.getExistingDirectory(self, "Open Folder")
        if folder:
            self.current_folder = folder
            git_dir = os.path.join(folder, ".git")
            if os.path.exists(git_dir):
                try:
                    self.repo = git.Repo(folder)
                    QMessageBox.information(self, "Repository Opened", f"Git repository detected in {folder}")
                    self.setWindowTitle(f"Construct - {os.path.basename(folder)}")
                except Exception as e:
                    QMessageBox.warning(self, "Git Error", f"Error opening Git repo: {e}")
            else:
                self.repo = None
            if self.fileTreeDock is None:
                self.createFileExplorer(folder)
            else:
                self.fileModel.setRootPath(folder)
                self.fileTreeView.setRootIndex(self.fileModel.index(folder))
                self.fileTreeDock.show()
    
    def createFileExplorer(self, root_path):
        self.fileTreeDock = QDockWidget("File Explorer", self)
        self.fileTreeView = QTreeView(self.fileTreeDock)
        from PyQt5.QtWidgets import QFileSystemModel
        self.fileModel = QFileSystemModel()
        self.fileModel.setRootPath(root_path)
        self.fileTreeView.setModel(self.fileModel)
        self.fileTreeView.setRootIndex(self.fileModel.index(root_path))
        self.fileTreeView.doubleClicked.connect(self.onFileTreeDoubleClicked)
        self.setupFileTreeContextMenu()
        self.fileTreeDock.setWidget(self.fileTreeView)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.fileTreeDock)

    def openFile(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "All Files (*);;Text Files (*.txt)", options=options
        )
        if file_name:
            self.openFileByPath(file_name)

    def openFileByPath(self, file_path):
        if file_path and os.path.isfile(file_path):
            new_tab = EditorTab(file_path)
            new_tab.setLexerForCurrentFile()
            self.tabWidget.addTab(new_tab, os.path.basename(file_path))
            self.tabWidget.setCurrentWidget(new_tab)
            handler = FileHandler(file_path, new_tab)
            new_tab.file_handler = handler
            handler.file_content_loaded.connect(self.loadFileContent)
            handler.finished.connect(handler.deleteLater)
            handler.start()

    def onFileTreeDoubleClicked(self, index: QModelIndex):
        file_path = self.fileModel.filePath(index)
        if os.path.isfile(file_path):
            self.openFileByPath(file_path)

    def setupFileTreeContextMenu(self):
        self.fileTreeView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.fileTreeView.customContextMenuRequested.connect(self.showFileTreeContextMenu)

    def showFileTreeContextMenu(self, position):
        index = self.fileTreeView.indexAt(position)

        context_menu = QMenu(self)

        if index.isValid():
            file_path = self.fileModel.filePath(index)
            
            open_action = QAction("Open", self)
            open_action.triggered.connect(lambda: self.onFileTreeDoubleClicked(index))
            context_menu.addAction(open_action)

            create_submenu = QMenu("Create", context_menu)
            
            new_file_action = QAction("New File", self)
            new_file_action.triggered.connect(lambda: self.createNewFile(file_path))
            create_submenu.addAction(new_file_action)
            
            new_dir_action = QAction("New Directory", self)
            new_dir_action.triggered.connect(lambda: self.createNewDirectory(file_path))
            create_submenu.addAction(new_dir_action)
            
            context_menu.addMenu(create_submenu)
        else:
            root_path = self.fileModel.rootPath()

            create_submenu = QMenu("Create", context_menu)
            
            new_file_action = QAction("New File", self)
            new_file_action.triggered.connect(lambda: self.createNewFile(root_path))
            create_submenu.addAction(new_file_action)
            
            new_dir_action = QAction("New Directory", self)
            new_dir_action.triggered.connect(lambda: self.createNewDirectory(root_path))
            create_submenu.addAction(new_dir_action)

            context_menu.addMenu(create_submenu)

        context_menu.exec_(self.fileTreeView.viewport().mapToGlobal(position))

    def createNewFile(self, path):
        if os.path.isfile(path):
            directory = os.path.dirname(path)
        else:
            directory = path
            
        file_name, ok = QInputDialog.getText(self, "New File", "Enter file name:")
        if ok and file_name:
            file_path = os.path.join(directory, file_name)
            try:
                with open(file_path, 'w') as f:
                    f.write("")
                self.openFileByPath(file_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create file: {e}")
    
    def createNewDirectory(self, path):
        if os.path.isfile(path):
            directory = os.path.dirname(path)
        else:
            directory = path
            
        dir_name, ok = QInputDialog.getText(self, "New Directory", "Enter directory name:")
        if ok and dir_name:
            dir_path = os.path.join(directory, dir_name)
            try:
                os.makedirs(dir_path, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create directory: {e}")

    def load_file_on_startup(self, file_path):
        if os.path.exists(file_path):
            new_tab = EditorTab(file_path)
            new_tab.setLexerForCurrentFile()
            self.tabWidget.addTab(new_tab, os.path.basename(file_path))
            self.tabWidget.setCurrentWidget(new_tab)
            handler = FileHandler(file_path, new_tab)
            new_tab.file_handler = handler
            handler.file_content_loaded.connect(self.loadFileContent)
            handler.finished.connect(handler.deleteLater)
            handler.start()
        else:
            QMessageBox.critical(self, "Error", f"File does not exist: {file_path}")

    def loadFileContent(self, content, encoding, tab):
        if encoding:
            tab.encoding = encoding
        if content.startswith("Error reading file"):
            QMessageBox.critical(self, "Error", content)
        else:
            tab.setContent(content, encoding)
            tab.setLexerForCurrentFile()
            if tab.file_path:
                index = self.tabWidget.indexOf(tab)
                self.tabWidget.setTabText(index, os.path.basename(tab.file_path))
            self.addToRecentFiles(tab.file_path)
        self.updateStatusBar()

    def saveFile(self):
        tab = self.currentTab()
        if not tab:
            return
        content = tab.editor.text()
        if tab.encoding is None:
            tab.encoding = 'utf-8'
        try:
            content.encode(tab.encoding)
            if tab.file_path:
                self.saveFileWithEncoding(tab, content, tab.encoding)
                tab.unsaved_changes = False
                self.updateStatusBar()
            else:
                self.saveFileAs()
        except UnicodeEncodeError:
            self.promptForEncoding(tab, content)

    def promptForEncoding(self, tab, content):
        encoding, ok = QInputDialog.getItem(
            self, "Choose Encoding", "Select Encoding:",
            ["UTF-8", "ISO-8859-1", "Windows-1252", "UTF-16"], 0, False
        )
        if ok:
            self.saveFileWithEncoding(tab, content, encoding)

    def saveFileWithEncoding(self, tab, content, encoding):
        if tab.file_path:
            try:
                content = content.replace('\r\n', '\n')
                with open(tab.file_path, 'w', encoding=encoding, newline='') as file:
                    file.write(content)
                tab.unsaved_changes = False
                tab.editor.setModified(False)
                tab.encoding = encoding
                self.updateStatusBar()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save file with encoding '{encoding}': {e}")

    def saveFileAs(self):
        tab = self.currentTab()
        if not tab:
            return
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save File As", "", "All Files (*);;Text Files (*.txt)", options=options
        )
        if file_name:
            tab.file_path = file_name
            tab.setLexerForCurrentFile()
            index = self.tabWidget.currentIndex()
            self.tabWidget.setTabText(index, os.path.basename(file_name))
            self.saveFile()

    def importFromWeb(self):
        editor = self.currentEditor()
        if editor:
            dialog = ImportFromWebDialog(editor)
            dialog.exec_()

    def openRepository(self):
        repo_path = QFileDialog.getExistingDirectory(self, "Select Git Repository")
        if repo_path:
            try:
                self.repo = git.Repo(repo_path)
                self.setWindowTitle(f"Construct - {os.path.basename(repo_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open repository: {e}")
            self.current_folder = repo_path
            if self.fileTreeDock is None:
                self.createFileExplorer(repo_path)
            else:
                self.fileModel.setRootPath(repo_path)
                self.fileTreeView.setRootIndex(self.fileModel.index(repo_path))
                self.fileTreeDock.show()

    def gitStatus(self):
        if not self.repo:
            QMessageBox.warning(self, "No Repository", "No repository is currently open.")
            return
        try:
            status = self.repo.git.status()
            statusDialog = QDialog(self)
            statusDialog.setWindowTitle("Git Status")
            layout = QVBoxLayout(statusDialog)
            textEdit = QTextEdit(statusDialog)
            textEdit.setReadOnly(True)
            textEdit.setPlainText(status)
            layout.addWidget(textEdit)
            statusDialog.resize(600, 400)
            statusDialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to get status: {e}")

    def stageAllChanges(self):
        if not self.repo:
            QMessageBox.warning(self, "No Repository", "No repository is currently open.")
            return
        try:
            self.repo.git.add('--all')
            QMessageBox.information(self, "Staged", "All changes have been staged.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to stage changes: {e}")

    def commitChanges(self):
        if not self.repo:
            QMessageBox.warning(self, "No Repository", "No repository is currently open.")
            return
        message, ok = QInputDialog.getText(self, "Commit Changes", "Enter commit message:")
        if ok and message:
            try:
                self.repo.index.commit(message)
                QMessageBox.information(self, "Committed", "Changes committed successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to commit changes: {e}")

    def pushChanges(self):
        if not self.repo:
            QMessageBox.warning(self, "No Repository", "No repository is currently open.")
            return
        try:
            origin = self.repo.remotes.origin
            origin.push()
            QMessageBox.information(self, "Pushed", "Changes pushed to remote.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to push changes: {e}")

    def pullChanges(self):
        if not self.repo:
            QMessageBox.warning(self, "No Repository", "No repository is currently open.")
            return
        try:
            origin = self.repo.remotes.origin
            origin.pull()
            QMessageBox.information(self, "Pulled", "Latest changes pulled from remote.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to pull changes: {e}")

    def switchBranch(self):
        if not self.repo:
            QMessageBox.warning(self, "No Repository", "No repository is currently open.")
            return
        try:
            branches = [b.name for b in self.repo.branches]
            if not branches:
                QMessageBox.information(self, "No Branches", "No branches found.")
                return
            branch, ok = QInputDialog.getItem(self, "Switch Branch", "Select branch:", branches, 0, False)
            if ok and branch:
                self.repo.git.checkout(branch)
                QMessageBox.information(self, "Switched", f"Switched to branch {branch}.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to switch branch: {e}")

    def openFindReplaceDialog(self):
        editor = self.currentEditor()
        if editor:
            dialog = FindReplaceDialog(editor)
            dialog.exec_()

    def closeTab(self, index):
        tab = self.tabWidget.widget(index)
        if tab:
            if tab.file_handler is not None:
                try:
                    if tab.file_handler.isRunning():
                        tab.file_handler.wait()
                except RuntimeError:
                    pass
                finally:
                    tab.file_handler = None
            if tab.unsaved_changes:
                dialog = UnsavedWorkDialog(self)
                result = dialog.exec_()
                if result == QDialog.Accepted:
                    self.tabWidget.setCurrentIndex(index)
                    self.saveFile()
                elif result == QDialog.Rejected:
                    return
                elif result == 2:
                    pass
            self.tabWidget.removeTab(index)
            if self.tabWidget.count() == 0:
                self.newFile()

    def closeEvent(self, event):
        unsaved = False
        for i in range(self.tabWidget.count()):
            tab = self.tabWidget.widget(i)
            if tab and tab.unsaved_changes:
                unsaved = True
                break
        if unsaved:
            dialog = UnsavedWorkDialog(self)
            result = dialog.exec_()
            if result == QDialog.Accepted:
                self.saveFile()
                event.accept()
            elif result == QDialog.Rejected:
                event.ignore()
            elif result == 2:
                event.accept()
        else:
            event.accept()

    def loadRecentFiles(self):
        self.settings = QSettings("Construct", "ConstructApp")
        self.recent_files = self.settings.value("recentFiles", [], type=list)

    def addToRecentFiles(self, file_path):
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        self.recent_files.insert(0, file_path)
        self.recent_files = self.recent_files[:5]
        self.settings.setValue("recentFiles", self.recent_files)
        self.updateRecentFilesMenu()

    def updateRecentFilesMenu(self):
        self.recentFilesMenu.clear()
        if not self.recent_files:
            self.recentFilesMenu.setEnabled(False)
        else:
            self.recentFilesMenu.setEnabled(True)
            for file in self.recent_files:
                file_name = os.path.basename(file)
                action = QAction(file_name, self)
                action.triggered.connect(lambda checked, path=file: self.openRecentFile(path))
                action.setToolTip(file)
                self.recentFilesMenu.addAction(action)
            self.recentFilesMenu.addSeparator()
            clearAction = QAction("Clear Recently Opened Files", self)
            clearAction.triggered.connect(self.clearRecentFiles)
            self.recentFilesMenu.addAction(clearAction)

    def openRecentFile(self, file_path):
        if os.path.exists(file_path):
            self.openFileByPath(file_path)
        else:
            QMessageBox.warning(self, "File Not Found", f"File not found: {file_path}")
            if file_path in self.recent_files:
                self.recent_files.remove(file_path)
                self.settings.setValue("recentFiles", self.recent_files)
                self.updateRecentFilesMenu()

    def clearRecentFiles(self):
        self.recent_files = []
        self.settings.setValue("recentFiles", self.recent_files)
        self.updateRecentFilesMenu()



""" Utility function to load the stylesheet """
def loadStyle():
    user_css_path = os.path.join(os.path.expanduser("~"), "ctstyle.css")
    stylesheet = None
    if os.path.exists(user_css_path):
        try:
            with open(user_css_path, 'r') as css_file:
                stylesheet = css_file.read()
            print(f"Loaded user CSS style from: {user_css_path}")
        except Exception as e:
            print(f"Error loading user CSS: {e}")
    else:
        css_file_path = os.path.join(os.path.dirname(__file__), 'style.css')
        try:
            with open(css_file_path, 'r') as css_file:
                stylesheet = css_file.read()
        except FileNotFoundError:
            print(f"Default CSS file not found: {css_file_path}")
    if stylesheet:
        app = QApplication.instance()
        if app:
            app.setStyleSheet(stylesheet)
        else:
            print("No QApplication instance found. Stylesheet not applied.")



""" Start the program """
if __name__ == '__main__':
    import subprocess
    try:
        subprocess.run(
            ["git", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    except Exception:
        from PyQt5.QtWidgets import QApplication, QMessageBox
        app = QApplication(sys.argv)
        QMessageBox.critical(None, "Git Not Found", 
            "Git is not installed on your system.\n\nPlease install Git to run this program.")
        sys.exit(1)
    app = QApplication(sys.argv)
    loadStyle()
    file_to_open = None
    if len(sys.argv) > 1:
        file_to_open = sys.argv[1]
    window = ConstructWindow(file_to_open)
    window.show()
    app_context = {"main_window": window}
    window.plugins = load_plugins(app_context)
    sys.exit(app.exec_())
