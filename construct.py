import sys
import os
import requests
import validators
import chardet
import importlib.util
from functools import partial
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QAction,
                             QFileDialog, QMessageBox, QStatusBar, QDialog, QInputDialog,
                             QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QComboBox,
                             QDockWidget, QTreeView, QToolBar, QSizePolicy, QMenu, QWidget, QFileSystemModel, QStyle, QTabWidget, QTextEdit)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QSettings, QSignalBlocker, QSize
from PyQt5.QtGui import QIcon, QFont, QFontDatabase, QTextDocument
from PyQt5.Qsci import QsciScintilla, QsciScintillaBase
from PyQt5 import Qsci as _Qsci
import urllib.parse
try:
    import git as _gitpy
except Exception:
    _gitpy = None



def _qsci_get(*names):
    for n in names:
        try:
            return getattr(_Qsci, n)
        except Exception:
            continue
    return None



QsciLexerPython      = _qsci_get('QsciLexerPython')
QsciLexerHTML        = _qsci_get('QsciLexerHTML')
QsciLexerCPP         = _qsci_get('QsciLexerCPP')
QsciLexerASM         = _qsci_get('QsciLexerASM', 'QsciLexerAsm')
QsciLexerAVS         = _qsci_get('QsciLexerAVS')
QsciLexerBash        = _qsci_get('QsciLexerBash')
QsciLexerBatch       = _qsci_get('QsciLexerBatch')
QsciLexerCMake       = _qsci_get('QsciLexerCMake')
QsciLexerCoffeeScript= _qsci_get('QsciLexerCoffeeScript')
QsciLexerCSharp      = _qsci_get('QsciLexerCSharp')
QsciLexerCSS         = _qsci_get('QsciLexerCSS')
QsciLexerD           = _qsci_get('QsciLexerD')
QsciLexerDiff        = _qsci_get('QsciLexerDiff')
QsciLexerEDIFACT     = _qsci_get('QsciLexerEDIFACT', 'QsciLexerEdifact')
QsciLexerFortran     = _qsci_get('QsciLexerFortran')
QsciLexerFortran77   = _qsci_get('QsciLexerFortran77')
QsciLexerHex         = _qsci_get('QsciLexerHex')
QsciLexerIDL         = _qsci_get('QsciLexerIDL')
QsciLexerIntelHex    = _qsci_get('QsciLexerIntelHex')
QsciLexerJava        = _qsci_get('QsciLexerJava')
QsciLexerJavaScript  = _qsci_get('QsciLexerJavaScript')
QsciLexerJSON        = _qsci_get('QsciLexerJSON')
QsciLexerLua         = _qsci_get('QsciLexerLua')
QsciLexerMakefile    = _qsci_get('QsciLexerMakefile')
QsciLexerMarkdown    = _qsci_get('QsciLexerMarkdown')
QsciLexerMASM        = _qsci_get('QsciLexerMASM', 'QsciLexerMasm')
QsciLexerMatlab      = _qsci_get('QsciLexerMatlab')
QsciLexerNASM        = _qsci_get('QsciLexerNASM', 'QsciLexerNasm')
QsciLexerOctave      = _qsci_get('QsciLexerOctave')
QsciLexerPascal      = _qsci_get('QsciLexerPascal')
QsciLexerPerl        = _qsci_get('QsciLexerPerl')
QsciLexerPO          = _qsci_get('QsciLexerPO')
QsciLexerPostScript  = _qsci_get('QsciLexerPostScript')
QsciLexerPOV         = _qsci_get('QsciLexerPOV')
QsciLexerProperties  = _qsci_get('QsciLexerProperties')
QsciLexerRuby        = _qsci_get('QsciLexerRuby')
QsciLexerSpice       = _qsci_get('QsciLexerSpice')
QsciLexerSQL         = _qsci_get('QsciLexerSQL')
QsciLexerSRec        = _qsci_get('QsciLexerSRec', 'QsciLexerSRecord')
QsciLexerTCL         = _qsci_get('QsciLexerTCL', 'QsciLexerTcl')
QsciLexerTekHex      = _qsci_get('QsciLexerTekHex')
QsciLexerTeX         = _qsci_get('QsciLexerTeX')
QsciLexerVerilog     = _qsci_get('QsciLexerVerilog')
QsciLexerVHDL        = _qsci_get('QsciLexerVHDL')
QsciLexerXML         = _qsci_get('QsciLexerXML')
QsciLexerYAML        = _qsci_get('QsciLexerYAML', 'QsciLexerYaml')



def detect_newline(sample: bytes) -> str:
    crlf = sample.count(b"\r\n")
    tmp = sample.replace(b"\r\n", b"")
    cr = tmp.count(b"\r")
    lf = tmp.count(b"\n")
    if crlf >= cr and crlf >= lf and crlf > 0:
        return "\r\n"
    if lf >= cr and lf > 0:
        return "\n"
    if cr > 0:
        return "\r"
    return "\r\n"



class FileHandler(QThread):
    file_content_loaded = pyqtSignal(str, str, object, object)
    file_load_started = pyqtSignal(str, object, object)
    file_chunk_loaded = pyqtSignal(str, str, bool)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
            detector = chardet.universaldetector.UniversalDetector()
            try:
                with open(self.file_path, 'rb') as file:
                    while chunk := file.read(1024):
                        detector.feed(chunk)
                        if detector.done:
                            break
                    detector.close()
                encoding = detector.result['encoding'] or 'utf-8'
                with open(self.file_path, 'rb') as fb:
                    sample = fb.read(64 * 1024)
                newline = detect_newline(sample)
                self.file_load_started.emit(self.file_path, encoding, newline)
                chunk_size = 1024 * 1024
                with open(self.file_path, 'r', encoding=encoding, errors='replace', newline=None) as file:
                    while True:
                        chunk = file.read(chunk_size)
                        if not chunk:
                            break
                        self.file_chunk_loaded.emit(self.file_path, chunk, False)
                self.file_chunk_loaded.emit(self.file_path, '', True)
            except Exception as e:
                self.file_content_loaded.emit(self.file_path, f"Error reading file: {e}", None, None)



class WebFetcher(QThread):
    completed = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, url, max_bytes=1_000_000, timeout=(5, 10), allow_redirects=False):
        super().__init__()
        self.url = url
        self.max_bytes = max_bytes
        self.timeout = timeout
        self.allow_redirects = allow_redirects

    def run(self):
        try:
            headers = {
                'User-Agent': 'Construct/1.0',
                'Accept': 'text/*, application/json'
            }
            with requests.get(
                self.url,
                timeout=self.timeout,
                allow_redirects=self.allow_redirects,
                stream=True,
                headers=headers
            ) as resp:
                if 300 <= resp.status_code < 400:
                    raise ValueError(f"Redirects not allowed (status {resp.status_code})")
                resp.raise_for_status()
                content_type = (resp.headers.get('Content-Type') or '').lower()
                if not (content_type.startswith('text/') or 'application/json' in content_type):
                    raise ValueError(f"Non-text content type: {content_type or 'unknown'}")
                cl = resp.headers.get('Content-Length')
                size_hint = None
                if cl is not None:
                    try:
                        size_hint = int(cl)
                    except (TypeError, ValueError):
                        size_hint = None
                if size_hint is not None and size_hint > self.max_bytes:
                    raise ValueError(f"Response too large (> {self.max_bytes} bytes)")
                chunks = []
                total = 0
                for chunk in resp.iter_content(chunk_size=65536):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > self.max_bytes:
                        raise ValueError(f"Response exceeded size limit ({self.max_bytes} bytes)")
                    chunks.append(chunk)
                data = b''.join(chunks)
                encoding = resp.encoding
                if not encoding:
                    detected = chardet.detect(data)
                    encoding = detected.get('encoding') or 'utf-8'
                text = data.decode(encoding, errors='replace')
                self.completed.emit(text)
        except Exception as e:
            self.failed.emit(f"Failed to fetch content: {e}")



def load_icon(icon_name):
    icon_path = os.path.join(os.path.dirname(__file__), icon_name)
    if getattr(sys, 'frozen', False):
        icon_path = os.path.join(sys._MEIPASS, icon_name)
    if os.path.exists(icon_path):
        return QIcon(icon_path)
    return None



def load_plugins(app_context):
    user_home = os.path.expanduser("~")
    plugins_dir = os.path.join(user_home, "spplugins")
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



def loadStyle():
    user_css_path = os.path.join(os.path.expanduser("~"), "spstyle.css")
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
        if getattr(sys, 'frozen', False):
            css_file_path = os.path.join(sys._MEIPASS, 'style.css')
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



def get_preferred_font():
    db = QFontDatabase()
    if "Cascadia Code" in db.families():
        family = "Cascadia Code"
    elif "Courier New" in db.families():
        family = "Courier New"
    elif "Courier" in db.families():
        family = "Courier"
    else:
        fallback = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        if fallback.pointSize() <= 0:
            fallback.setPointSize(10)
        return fallback
    return QFont(family, 10)



class FindReplaceDialog(QDialog):
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit
        self.setWindowTitle("Find and Replace")
        self.setWindowIcon(load_icon('construct.png'))
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
        self.setLayout(self.layout)
        self.current_index = 0

    def find_next(self):
        text_to_find = self.find_input.text().strip()
        if text_to_find:
            options = QTextDocument.FindFlags()
            found = self.text_edit.find(text_to_find, options)
            if not found:
                QMessageBox.information(self, "Not Found", "No more occurrences found.")
        else:
            QMessageBox.warning(self, "Empty Search", "Please enter text to find.")

    def replace(self):
        text_to_find = self.find_input.text()
        text_to_replace = self.replace_input.text()
        if text_to_find and text_to_replace:
            editor = self.text_edit
            found = editor.findFirst(text_to_find, False, False, False, True, True)
            if found:
                editor.replaceSelectedText(text_to_replace)

    def replace_all(self):
        text_to_find = self.find_input.text()
        text_to_replace = self.replace_input.text()
        if text_to_find and text_to_replace:
            editor = self.text_edit
            editor.setCursorPosition(0, 0)
            replaced = 0
            if editor.findFirst(text_to_find, False, False, False, True, True):
                while True:
                    editor.replaceSelectedText(text_to_replace)
                    replaced += 1
                    if not getattr(editor, 'findNext')():
                        break
            QMessageBox.information(self, "Replace All", f"Replaced {replaced} occurrence(s).")



class LanguageSelectDialog(QDialog):
    def __init__(self, parent, languages, current_language):
        super().__init__(parent)
        self.setWindowTitle("Select Language")
        self.setWindowIcon(load_icon('construct.png'))
        self._languages = list(languages)
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Language:")
        self.combo = QComboBox(self)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.combo)
        self.button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK", self)
        self.cancel_button = QPushButton("Cancel", self)
        self.button_layout.addWidget(self.ok_button)
        self.button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(self.button_layout)
        self.combo.addItems(self._languages)
        try:
            idx = self._languages.index(current_language) if current_language in self._languages else 0
            self.combo.setCurrentIndex(idx)
        except Exception:
            pass
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def selected_language(self):
        return self.combo.currentText() if hasattr(self.combo, 'currentText') else (self._languages[0] if self._languages else "Plain Text")



class ImportFromWebDialog(QDialog):
    def __init__(self, text_edit, app_context=None):
        super().__init__()
        self.text_edit = text_edit
        self.app_context = app_context
        self.setWindowTitle("Import From Web")
        self.setWindowIcon(load_icon('construct.png'))
        self.layout = QVBoxLayout(self)
        self.url_label = QLabel("Enter URL:")
        self.url_input = QLineEdit(self)
        self.layout.addWidget(self.url_label)
        self.layout.addWidget(self.url_input)
        self.fetch_button = QPushButton("Fetch", self)
        self.layout.addWidget(self.fetch_button)
        self.fetch_button.clicked.connect(self.fetch_from_web)
        self.setLayout(self.layout)
        self._fetcher = None

    def fetch_from_web(self):
        url = self.url_input.text().strip()
        if not self.is_valid_url(url):
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid HTTPS URL.")
            return
        if self._fetcher and self._fetcher.isRunning():
            QMessageBox.information(self, "In Progress", "A fetch is already in progress.")
            return
        self.fetch_button.setEnabled(False)
        self._fetcher = WebFetcher(url)
        self._fetcher.completed.connect(self._on_fetch_completed)
        self._fetcher.failed.connect(self._on_fetch_failed)
        self._fetcher.start()

    def _on_fetch_completed(self, text):
        try:
            self.text_edit.setPlainText(text)
            try:
                parsed = urllib.parse.urlparse(self.url_input.text().strip())
                path_like = parsed.path if parsed and parsed.path else None
                if path_like:
                    mw = self.app_context.get('main_window') if hasattr(self, 'app_context') and self.app_context else None
                    if mw and hasattr(mw, 'setLexerForFilePath'):
                        mw.setLexerForFilePath(path_like)
            except Exception:
                pass
            self.accept()
        finally:
            self.fetch_button.setEnabled(True)
            if self._fetcher:
                self._fetcher.deleteLater()
                self._fetcher = None

    def _on_fetch_failed(self, error_message):
        try:
            QMessageBox.critical(self, "Error", error_message)
        finally:
            self.fetch_button.setEnabled(True)
            if self._fetcher:
                self._fetcher.deleteLater()
                self._fetcher = None

    def is_valid_url(self, url):
        return validators.url(url) and url.startswith("https://")



class UnsavedWorkDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("Unsaved Changes")
        self.setWindowIcon(load_icon('construct.png'))
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
        self.setLayout(self.layout)

    def discard_changes(self):
        self.done(2)



class Editor(QsciScintilla):
    zoomChanged = pyqtSignal(int)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.preferred_font = get_preferred_font()
        self.setFont(self.preferred_font)
        self.setMarginsFont(self.preferred_font)
        self.setMarginWidth(0, 0)
        self.setMarginLineNumbers(1, False)
        self.setMarginWidth(1, 0)
        self.setWrapMode(QsciScintilla.WrapNone)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.adjust_scroll_bar_policy()
        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)
        self.setIndentationGuides(False)
        self.setTabWidth(4)
        self.setIndentationsUseTabs(False)
        try:
            self.setAutoIndent(True)
        except Exception:
            pass
        try:
            self.setTabIndents(True)
        except Exception:
            pass
        try:
            self.setBackspaceUnindents(True)
        except Exception:
            pass
        self.setEolMode(QsciScintilla.EolWindows)
        self._zoom = 0
        self.setUtf8(True) if hasattr(self, 'setUtf8') else None

    def append_text(self, text: str):
        try:
            data = text.encode('utf-8', errors='replace')
            self.SendScintilla(QsciScintillaBase.SCI_APPENDTEXT, len(data), data)
        except Exception:
            self.SendScintilla(QsciScintillaBase.SCI_DOCUMENTEND)
            try:
                self.insert(text)
            except Exception:
                self.setText(self.text() + text)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_scroll_bar_policy()

    def setPlainText(self, text):
        super().setText(text)

    def toPlainText(self):
        return super().text()

    def zoomTo(self, size):
        super().zoomTo(size)
        try:
            size = int(size)
        except Exception:
            pass
        if size != getattr(self, '_zoom', None):
            self._zoom = size
            self.zoomChanged.emit(size)

    def zoomIn(self):
        super().zoomIn()
        z = int(self.SendScintilla(QsciScintillaBase.SCI_GETZOOM))
        if z != self._zoom:
            self._zoom = z
            self.zoomChanged.emit(z)

    def zoomOut(self):
        super().zoomOut()
        z = int(self.SendScintilla(QsciScintillaBase.SCI_GETZOOM))
        if z != self._zoom:
            self._zoom = z
            self.zoomChanged.emit(z)

    def find(self, text, options):
        case_sensitive = bool(options & QTextDocument.FindCaseSensitively)
        backward = bool(options & QTextDocument.FindBackward)
        whole_word = bool(options & QTextDocument.FindWholeWords)
        return self.findFirst(text, False, case_sensitive, whole_word, True, not backward)

    def textCursor(self):
        line, index = self.getCursorPosition()
        class CursorWrapper:
            def __init__(self, line, index):
                self._line = line
                self._index = index
            def blockNumber(self):
                return self._line
            def columnNumber(self):
                return self._index
        return CursorWrapper(line, index)

    def adjust_scroll_bar_policy(self):
        text = self.text()
        if not text:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            return
        fm = self.fontMetrics()
        max_width = max(fm.horizontalAdvance(line) for line in text.split('\n'))
        if max_width > self.viewport().width():
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        else:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def wheelEvent(self, event):
        ctrl = bool(event.modifiers() & Qt.ControlModifier)
        super().wheelEvent(event)
        if ctrl:
            z = int(self.SendScintilla(QsciScintillaBase.SCI_GETZOOM))
            if z != self._zoom:
                self._zoom = z
                self.zoomChanged.emit(z)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.modifiers() & Qt.ControlModifier:
            z = int(self.SendScintilla(QsciScintillaBase.SCI_GETZOOM))
            if z != self._zoom:
                self._zoom = z
                self.zoomChanged.emit(z)



class Construct(QMainWindow):
    def __init__(self, file_to_open=None):
        super().__init__()
        self.current_file = file_to_open
        self.file_handler = None
        self._open_generation = 0
        self.unsaved_changes = False
        self._lexer = None
        self.fileTreeDock = None
        self.fileModel = None
        self.fileTreeView = None
        self.current_folder = None
        self.repo = None
        self.loadRecentFiles()
        self.initUI()
        if file_to_open:
            self.load_file_on_startup(file_to_open)
        self.app_context = {"main_window": self}
        self.plugins = load_plugins(self.app_context)

    def _available_language_lexers(self):
        mapping = {"Plain Text": None}
        if QsciLexerPython: mapping["Python"] = QsciLexerPython
        if QsciLexerCPP: mapping["C++"] = QsciLexerCPP
        if QsciLexerCSharp: mapping["C#"] = QsciLexerCSharp
        if QsciLexerJava: mapping["Java"] = QsciLexerJava
        if QsciLexerJavaScript: mapping["JavaScript"] = QsciLexerJavaScript
        if QsciLexerJSON or QsciLexerJavaScript: mapping["JSON"] = QsciLexerJSON or QsciLexerJavaScript
        if QsciLexerHTML: mapping["HTML"] = QsciLexerHTML
        if QsciLexerCSS: mapping["CSS"] = QsciLexerCSS
        if QsciLexerLua: mapping["Lua"] = QsciLexerLua
        if QsciLexerSQL: mapping["SQL"] = QsciLexerSQL
        if QsciLexerRuby: mapping["Ruby"] = QsciLexerRuby
        if QsciLexerPascal: mapping["Pascal"] = QsciLexerPascal
        if QsciLexerPerl: mapping["Perl"] = QsciLexerPerl
        if QsciLexerMakefile: mapping["Makefile"] = QsciLexerMakefile
        if QsciLexerCMake: mapping["CMake"] = QsciLexerCMake
        if QsciLexerMarkdown: mapping["Markdown"] = QsciLexerMarkdown
        if QsciLexerBash: mapping["Bash"] = QsciLexerBash
        if QsciLexerBatch: mapping["Batch"] = QsciLexerBatch
        if QsciLexerDiff: mapping["Diff"] = QsciLexerDiff
        if QsciLexerASM: mapping["ASM"] = QsciLexerASM
        if QsciLexerMASM: mapping["MASM"] = QsciLexerMASM
        if QsciLexerNASM: mapping["NASM"] = QsciLexerNASM
        if QsciLexerAVS: mapping["AVS"] = QsciLexerAVS
        if QsciLexerCoffeeScript: mapping["CoffeeScript"] = QsciLexerCoffeeScript
        if QsciLexerD: mapping["D"] = QsciLexerD
        if QsciLexerEDIFACT: mapping["EDIFACT"] = QsciLexerEDIFACT
        if QsciLexerFortran: mapping["Fortran"] = QsciLexerFortran
        if QsciLexerFortran77: mapping["Fortran77"] = QsciLexerFortran77
        if QsciLexerHex: mapping["Hex"] = QsciLexerHex
        if QsciLexerIntelHex: mapping["Intel Hex"] = QsciLexerIntelHex
        if QsciLexerSRec: mapping["S-Record"] = QsciLexerSRec
        if QsciLexerTekHex: mapping["Tektronix Hex"] = QsciLexerTekHex
        if QsciLexerIDL: mapping["IDL"] = QsciLexerIDL
        if QsciLexerOctave: mapping["Octave"] = QsciLexerOctave
        if QsciLexerMatlab: mapping["Matlab"] = QsciLexerMatlab
        if QsciLexerPO: mapping["PO"] = QsciLexerPO
        if QsciLexerPOV: mapping["POV"] = QsciLexerPOV
        if QsciLexerPostScript: mapping["PostScript"] = QsciLexerPostScript
        if QsciLexerProperties: mapping["Properties"] = QsciLexerProperties
        if QsciLexerSpice: mapping["Spice"] = QsciLexerSpice
        if QsciLexerTCL: mapping["TCL"] = QsciLexerTCL
        if QsciLexerTeX: mapping["TeX"] = QsciLexerTeX
        if QsciLexerVerilog: mapping["Verilog"] = QsciLexerVerilog
        if QsciLexerVHDL: mapping["VHDL"] = QsciLexerVHDL
        if QsciLexerXML: mapping["XML"] = QsciLexerXML
        if QsciLexerYAML: mapping["YAML"] = QsciLexerYAML
        return mapping

    def _current_language_name(self):
        if not self._lexer:
            return "Plain Text"
        mapping = self._available_language_lexers()
        for name, cls in mapping.items():
            if not cls:
                continue
            try:
                if isinstance(self._lexer, cls):
                    return name
            except Exception:
                continue
        return "Plain Text"

    def setLexerByLanguageName(self, language_name):
        ed = self.currentEditor()
        if ed is None:
            return False
        if not language_name or language_name == "Plain Text":
            ed.setLexer(None)
            self._lexer = None
            return True
        mapping = self._available_language_lexers()
        cls = mapping.get(language_name)
        if not cls:
            return False
        try:
            lexer = cls(ed)
            self._apply_uniform_lexer_font(lexer)
            ed.setLexer(lexer)
            self._lexer = lexer
            return True
        except Exception:
            return False

    def _applySavedSyntaxOrDetect(self, path_like):
        base = os.path.realpath(path_like).replace('\\','/') if path_like else None
        if base:
            key = f"syntax/overrides/{base}"
            saved = self.settings.value(key, None, type=str)
            if saved and self.setLexerByLanguageName(saved):
                return
        self.setLexerForFilePath(path_like)

    def setLexerForFilePath(self, path_like):
        ed = self.currentEditor()
        if ed is None:
            return
        base = os.path.basename(path_like) if path_like else ""
        base_lower = base.lower()
        ext = os.path.splitext(base_lower)[1].lower() if base_lower else ""
        lexer = None
        if base_lower in {"cmakelists.txt"} and QsciLexerCMake:
            lexer = QsciLexerCMake(ed)
        elif base_lower in {"makefile", "gnumakefile"} and QsciLexerMakefile:
            lexer = QsciLexerMakefile(ed)
        elif ext in {".py", ".pyw"} and QsciLexerPython:
            lexer = QsciLexerPython(ed)
        elif ext in {".c", ".h", ".cpp", ".hpp", ".cc", ".cxx", ".hh", ".hxx"} and QsciLexerCPP:
            lexer = QsciLexerCPP(ed)
        elif ext in {".cs"} and QsciLexerCSharp:
            lexer = QsciLexerCSharp(ed)
        elif ext in {".js", ".jsx", ".ts", ".tsx"} and QsciLexerJavaScript:
            lexer = QsciLexerJavaScript(ed)
        elif ext in {".json"}:
            if QsciLexerJSON:
                lexer = QsciLexerJSON(ed)
            elif QsciLexerJavaScript:
                lexer = QsciLexerJavaScript(ed)
        elif ext in {".css"} and QsciLexerCSS:
            lexer = QsciLexerCSS(ed)
        elif ext in {".html", ".htm"} and QsciLexerHTML:
            lexer = QsciLexerHTML(ed)
        elif ext in {".java"} and QsciLexerJava:
            lexer = QsciLexerJava(ed)
        elif ext in {".asm"} and QsciLexerASM:
            lexer = QsciLexerASM(ed)
        elif ext in {".avs"} and QsciLexerAVS:
            lexer = QsciLexerAVS(ed)
        elif ext in {".sh", ".bash", ".zsh"} and QsciLexerBash:
            lexer = QsciLexerBash(ed)
        elif ext in {".bat", ".cmd"} and QsciLexerBatch:
            lexer = QsciLexerBatch(ed)
        elif ext in {".cmake"} and QsciLexerCMake:
            lexer = QsciLexerCMake(ed)
        elif ext in {".coffee"} and QsciLexerCoffeeScript:
            lexer = QsciLexerCoffeeScript(ed)
        elif ext in {".d"} and QsciLexerD:
            lexer = QsciLexerD(ed)
        elif ext in {".diff", ".patch"} and QsciLexerDiff:
            lexer = QsciLexerDiff(ed)
        elif ext in {".edi", ".edifact"} and QsciLexerEDIFACT:
            lexer = QsciLexerEDIFACT(ed)
        elif ext in {".f90", ".f95", ".f03", ".f08"} and QsciLexerFortran:
            lexer = QsciLexerFortran(ed)
        elif ext in {".f", ".for", ".f77"} and (QsciLexerFortran77 or QsciLexerFortran):
            lexer = (QsciLexerFortran77 or QsciLexerFortran)(ed)
        elif ext in {".hex"} and QsciLexerHex:
            lexer = QsciLexerHex(ed)
        elif ext in {".idl"} and QsciLexerIDL:
            lexer = QsciLexerIDL(ed)
        elif ext in {".ihex", ".ihx"} and QsciLexerIntelHex:
            lexer = QsciLexerIntelHex(ed)
        elif ext in {".xml"} and QsciLexerXML:
            lexer = QsciLexerXML(ed)
        elif ext in {".md", ".markdown"} and QsciLexerMarkdown:
            lexer = QsciLexerMarkdown(ed)
        elif ext in {".rb"} and QsciLexerRuby:
            lexer = QsciLexerRuby(ed)
        elif ext in {".sql"} and QsciLexerSQL:
            lexer = QsciLexerSQL(ed)
        elif ext in {".lua"} and QsciLexerLua:
            lexer = QsciLexerLua(ed)
        elif ext in {".mak"} and QsciLexerMakefile:
            lexer = QsciLexerMakefile(ed)
        elif ext in {".masm"} and QsciLexerMASM:
            lexer = QsciLexerMASM(ed)
        elif ext in {".matlab"} and QsciLexerMatlab:
            lexer = QsciLexerMatlab(ed)
        elif ext in {".nasm"} and QsciLexerNASM:
            lexer = QsciLexerNASM(ed)
        elif ext in {".m"} and (QsciLexerMatlab or QsciLexerOctave):
            preferred = QsciLexerMatlab or QsciLexerOctave
            lexer = preferred(ed)
        elif ext in {".octave"} and QsciLexerOctave:
            lexer = QsciLexerOctave(ed)
        elif ext in {".pas", ".pp"} and QsciLexerPascal:
            lexer = QsciLexerPascal(ed)
        elif ext in {".pl", ".pm", ".t"} and QsciLexerPerl:
            lexer = QsciLexerPerl(ed)
        elif ext in {".po"} and QsciLexerPO:
            lexer = QsciLexerPO(ed)
        elif ext in {".ps", ".eps"} and QsciLexerPostScript:
            lexer = QsciLexerPostScript(ed)
        elif ext in {".pov"} and QsciLexerPOV:
            lexer = QsciLexerPOV(ed)
        elif ext in {".properties"} and QsciLexerProperties:
            lexer = QsciLexerProperties(ed)
        elif ext in {".sp", ".cir", ".ckt", ".spice"} and QsciLexerSpice:
            lexer = QsciLexerSpice(ed)
        elif ext in {".srec", ".s19", ".s28", ".s37"} and QsciLexerSRec:
            lexer = QsciLexerSRec(ed)
        elif ext in {".tek", ".tekhex"} and QsciLexerTekHex:
            lexer = QsciLexerTekHex(ed)
        elif ext in {".tcl"} and QsciLexerTCL:
            lexer = QsciLexerTCL(ed)
        elif ext in {".tex"} and QsciLexerTeX:
            lexer = QsciLexerTeX(ed)
        elif ext in {".v", ".sv"} and QsciLexerVerilog:
            lexer = QsciLexerVerilog(ed)
        elif ext in {".vhd", ".vhdl"} and QsciLexerVHDL:
            lexer = QsciLexerVHDL(ed)
        elif ext in {".yaml", ".yml"} and QsciLexerYAML:
            lexer = QsciLexerYAML(ed)
        if lexer is not None:
            self._apply_uniform_lexer_font(lexer)
            ed.setLexer(lexer)
            self._lexer = lexer
        else:
            ed.setLexer(None)
            self._lexer = None

    def _apply_uniform_lexer_font(self, lexer):
        ed = self.currentEditor()
        base = None
        if ed is not None:
            base = getattr(ed, 'preferred_font', None) or ed.font()
        if base is None:
            try:
                base = QFontDatabase.systemFont(QFontDatabase.FixedFont)
            except Exception:
                base = QFont('monospace', 10)
        font = QFont(base)
        try:
            font.setBold(False)
        except Exception:
            pass
        try:
            font.setItalic(False)
        except Exception:
            pass
        try:
            if hasattr(lexer, 'setDefaultFont'):
                lexer.setDefaultFont(font)
        except Exception:
            pass
        try:
            bits = int(lexer.styleBitsNeeded()) if hasattr(lexer, 'styleBitsNeeded') else 7
            max_styles = (1 << bits) if bits and bits > 0 else 128
        except Exception:
            max_styles = 128
        for style in range(max_styles):
            try:
                desc = None
                try:
                    desc = lexer.description(style)
                except Exception:
                    desc = None
                if desc is not None:
                    lexer.setFont(font, style)
            except Exception:
                continue

    def load_file_on_startup(self, file_path):
        if os.path.exists(file_path):
            ed = self.currentEditor()
            reuse = False
            if ed is not None:
                idx = self.tabWidget.indexOf(ed)
                try:
                    title = self.tabWidget.tabText(idx) if idx != -1 else ""
                except Exception:
                    title = ""
                is_untitled = (title.strip().lower() == 'untitled') and not getattr(ed, 'file_path', None)
                try:
                    empty = not bool(ed.text())
                except Exception:
                    empty = True
                reuse = is_untitled and empty
            if not reuse:
                ed = Editor(self)
                ed.setEolMode(QsciScintilla.EolWindows)
                self._attach_editor(ed, os.path.basename(file_path))
            self._start_file_load(ed, file_path)
        else:
            QMessageBox.critical(self, "Error", f"File does not exist: {file_path}")

    def closeEvent(self, event):
        ed = self.currentEditor()
        unsaved = getattr(ed, 'unsaved_changes', False) if ed else False
        if unsaved:
            dialog = UnsavedWorkDialog(self)
            result = dialog.exec_()
            if result == QDialog.Accepted:
                success = self.saveFile()
                if success:
                    self._safe_wait_for_handler()
                    event.accept()
                else:
                    event.ignore()
            elif result == QDialog.Rejected:
                event.ignore()
            elif result == 2:
                self._safe_wait_for_handler()
                event.accept()
            else:
                self._safe_wait_for_handler()
                event.accept()
        else:
            self._safe_wait_for_handler()
            event.accept()

    def initUI(self):
        self.setWindowTitle('Construct - Unnamed')
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(load_icon('construct.png'))
        self.tabWidget = QTabWidget(self)
        self.tabWidget.setTabsClosable(True)
        try:
            self.tabWidget.setMovable(True)
        except Exception:
            pass
        self.tabWidget.tabCloseRequested.connect(self.closeTab)
        self.tabWidget.currentChanged.connect(self._on_tab_changed)
        self.setCentralWidget(self.tabWidget)
        self.statusBar = QStatusBar(self)
        self.setStatusBar(self.statusBar)
        self.line = 1
        self.column = 1
        self.char_count = 0
        self.createMenu()
        self.newFile()

    def on_text_changed(self):
        ed = self.currentEditor()
        if ed is not None:
            setattr(ed, 'unsaved_changes', True)
        self.updateStatusBar()

    def currentEditor(self):
        try:
            return self.tabWidget.currentWidget()
        except Exception:
            return None

    def _attach_editor(self, ed: 'Editor', title: str):
        setattr(ed, 'file_path', None)
        setattr(ed, 'encoding', 'UTF-8')
        setattr(ed, 'newline', '\r\n')
        setattr(ed, 'unsaved_changes', False)
        setattr(ed, 'file_handler', None)
        setattr(ed, 'open_generation', 0)
        wrapEnabled = self.settings.value("wordWrap", False, type=bool)
        ed.setWrapMode(QsciScintilla.WrapWord if wrapEnabled else QsciScintilla.WrapNone)
        self.zoom_level = self.settings.value("view/zoom", 0, type=int)
        try:
            ed.zoomTo(int(self.zoom_level))
        except Exception:
            pass
        ed.cursorPositionChanged.connect(self.updateStatusBar)
        ed.zoomChanged.connect(self._on_zoom_changed)
        ed.textChanged.connect(self.on_text_changed)
        idx = self.tabWidget.addTab(ed, title)
        self.tabWidget.setCurrentIndex(idx)
        self.textEdit = ed
        self.encoding = 'UTF-8'
        self.newline = '\r\n'
        self.unsaved_changes = False
        self.updateStatusBar(after_save=True)

    def _on_tab_changed(self, index):
        ed = self.currentEditor()
        if not ed:
            return
        self.textEdit = ed
        self.current_file = getattr(ed, 'file_path', None)
        self.encoding = getattr(ed, 'encoding', 'UTF-8')
        self.newline = getattr(ed, 'newline', '\r\n')
        self.unsaved_changes = getattr(ed, 'unsaved_changes', False)
        title = os.path.basename(self.current_file) if self.current_file else 'Unnamed'
        self.setWindowTitle(f'Construct - {title}')
        self.updateStatusBar(after_save=True)

    def createMenu(self):
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        self.createFileActions(fileMenu)
        editMenu = menubar.addMenu('&Edit')
        self.createEditActions(editMenu)
        viewMenu = menubar.addMenu('&View')
        self.createViewActions(viewMenu)
        gitMenu = menubar.addMenu('&Git')
        self.createGitActions(gitMenu)

    def createFileActions(self, menu):
        self.actions = {}
        newAction = QAction('New', self)
        newAction.setShortcut('Ctrl+N')
        newAction.triggered.connect(self.newFile)
        menu.addAction(newAction)
        self.actions['new'] = newAction
        openAction = QAction('Open...', self)
        openAction.setShortcut('Ctrl+O')
        openAction.triggered.connect(self.openFile)
        menu.addAction(openAction)
        self.actions['open'] = openAction
        openFolderAction = QAction('Open Folder...', self)
        openFolderAction.setShortcut('Ctrl+Shift+O')
        openFolderAction.triggered.connect(self.openFolder)
        menu.addAction(openFolderAction)
        self.actions['openfolder'] = openFolderAction
        saveAction = QAction('Save', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.triggered.connect(self.saveFile)
        menu.addAction(saveAction)
        self.actions['save'] = saveAction
        saveAsAction = QAction('Save As...', self)
        saveAsAction.setShortcut('Ctrl+Shift+S')
        saveAsAction.triggered.connect(self.saveFileAs)
        menu.addAction(saveAsAction)
        self.actions['saveas'] = saveAsAction
        importFromWebAction = QAction('Import From Web...', self)
        importFromWebAction.setShortcut('Ctrl+I')
        importFromWebAction.triggered.connect(self.importFromWeb)
        menu.addAction(importFromWebAction)
        self.actions['importfromweb'] = importFromWebAction
        exitAction = QAction('Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(self.close)
        menu.addAction(exitAction)
        self.actions['exit'] = exitAction
        menu.addSeparator()
        self.recentFilesMenu = menu.addMenu('Recently Opened Files')
        self.recentFilesMenu.aboutToShow.connect(self.updateRecentFilesMenu)
        self.updateRecentFilesMenu()
        
    def createEditActions(self, menu):
        undoAction = QAction('Undo', self)
        undoAction.setShortcut('Ctrl+Z')
        undoAction.triggered.connect(lambda: self.currentEditor() and self.currentEditor().undo())
        menu.addAction(undoAction)
        self.actions['undo'] = undoAction
        redoAction = QAction('Redo', self)
        if sys.platform != 'darwin':
            redoAction.setShortcuts(['Ctrl+Y', 'Ctrl+Shift+Z'])
        else:
            redoAction.setShortcuts(['Ctrl+Shift+Z', 'Ctrl+Y'])
        redoAction.triggered.connect(lambda: self.currentEditor() and self.currentEditor().redo())
        menu.addAction(redoAction)
        self.actions['redo'] = redoAction
        cutAction = QAction('Cut', self)
        cutAction.setShortcut('Ctrl+X')
        cutAction.triggered.connect(lambda: self.currentEditor() and self.currentEditor().cut())
        menu.addAction(cutAction)
        self.actions['cut'] = cutAction
        copyAction = QAction('Copy', self)
        copyAction.setShortcut('Ctrl+C')
        copyAction.triggered.connect(lambda: self.currentEditor() and self.currentEditor().copy())
        menu.addAction(copyAction)
        self.actions['copy'] = copyAction
        pasteAction = QAction('Paste', self)
        pasteAction.setShortcut('Ctrl+V')
        pasteAction.triggered.connect(lambda: self.currentEditor() and self.currentEditor().paste())
        menu.addAction(pasteAction)
        self.actions['paste'] = pasteAction
        selectAllAction = QAction('Select All', self)
        selectAllAction.setShortcut('Ctrl+A')
        selectAllAction.triggered.connect(lambda: self.currentEditor() and self.currentEditor().selectAll())
        menu.addAction(selectAllAction)
        self.actions['selectall'] = selectAllAction
        findReplaceAction = QAction('Find and Replace...', self)
        findReplaceAction.triggered.connect(self.openFindReplaceDialog)
        findReplaceAction.setShortcut('Ctrl+F')
        menu.addAction(findReplaceAction)
        self.actions['findreplace'] = findReplaceAction

    def createGitActions(self, menu):
        openRepoAction = QAction('Open Repository...', self)
        openRepoAction.setShortcut('Ctrl+Alt+R')
        openRepoAction.triggered.connect(self.openRepository)
        menu.addAction(openRepoAction)

        statusAction = QAction('Status', self)
        statusAction.setShortcut('Ctrl+Alt+S')
        statusAction.triggered.connect(self.gitStatus)
        menu.addAction(statusAction)

        stageCurrentAction = QAction('Stage Current File', self)
        stageCurrentAction.setShortcut('Ctrl+Alt+F')
        stageCurrentAction.triggered.connect(self.stageCurrentFile)
        menu.addAction(stageCurrentAction)

        stageAllAction = QAction('Stage All Changes', self)
        stageAllAction.setShortcut('Ctrl+Alt+A')
        stageAllAction.triggered.connect(self.stageAllChanges)
        menu.addAction(stageAllAction)

        commitAction = QAction('Commit...', self)
        commitAction.setShortcut('Ctrl+Alt+C')
        commitAction.triggered.connect(self.commitChanges)
        menu.addAction(commitAction)

        fetchAction = QAction('Fetch', self)
        fetchAction.setShortcut('Ctrl+Alt+F5')
        fetchAction.triggered.connect(self.fetchChanges)
        menu.addAction(fetchAction)

        pullAction = QAction('Pull', self)
        pullAction.setShortcut('Ctrl+Alt+L')
        pullAction.triggered.connect(self.pullChanges)
        menu.addAction(pullAction)

        pushAction = QAction('Push', self)
        pushAction.setShortcut('Ctrl+Alt+P')
        pushAction.triggered.connect(self.pushChanges)
        menu.addAction(pushAction)

        branchAction = QAction('Switch Branch...', self)
        branchAction.setShortcut('Ctrl+Alt+B')
        branchAction.triggered.connect(self.switchBranch)
        menu.addAction(branchAction)

        newBranchAction = QAction('Create Branch...', self)
        newBranchAction.setShortcut('Ctrl+Alt+N')
        newBranchAction.triggered.connect(self.createBranch)
        menu.addAction(newBranchAction)

        logAction = QAction('Show Log', self)
        logAction.setShortcut('Ctrl+Alt+O')
        logAction.triggered.connect(self.showLog)
        menu.addAction(logAction)

        diffFileAction = QAction('Diff Current File', self)
        diffFileAction.setShortcut('Ctrl+Alt+D')
        diffFileAction.triggered.connect(self.diffCurrentFile)
        menu.addAction(diffFileAction)

        discardFileAction = QAction('Discard Current File Changes', self)
        discardFileAction.setShortcut('Ctrl+Alt+K')
        discardFileAction.triggered.connect(self.discardCurrentFileChanges)
        menu.addAction(discardFileAction)

    def createViewActions(self, menu):
        wrapEnabled = self.settings.value("wordWrap", False, type=bool)
        ed = self.currentEditor()
        if ed:
            ed.setWrapMode(QsciScintilla.WrapWord if wrapEnabled else QsciScintilla.WrapNone)
        wordWrapAction = QAction('Word Wrap', self)
        wordWrapAction.setShortcut('Ctrl+W')
        wordWrapAction.setCheckable(True)
        wordWrapAction.setChecked(wrapEnabled)
        wordWrapAction.toggled.connect(lambda checked: (self.currentEditor() and self.currentEditor().setWrapMode(QsciScintilla.WrapWord if checked else QsciScintilla.WrapNone), self.settings.setValue("wordWrap", checked)))
        menu.addAction(wordWrapAction)
        self.actions['wordwrap'] = wordWrapAction
        selectLangAction = QAction('Select Language...', self)
        selectLangAction.setShortcut('Ctrl+L')
        selectLangAction.triggered.connect(self.openLanguageSelector)
        menu.addAction(selectLangAction)
        self.actions['selectlanguage'] = selectLangAction
        zoomInAction = QAction('Zoom In', self)
        zoomInAction.setShortcut('Ctrl+=')
        zoomInAction.triggered.connect(lambda: self._zoom_delta(1))
        menu.addAction(zoomInAction)
        self.actions['zoomin'] = zoomInAction
        zoomOutAction = QAction('Zoom Out', self)
        zoomOutAction.setShortcut('Ctrl+-')
        zoomOutAction.triggered.connect(lambda: self._zoom_delta(-1))
        menu.addAction(zoomOutAction)
        self.actions['zoomout'] = zoomOutAction
        resetZoomAction = QAction('Reset Zoom', self)
        resetZoomAction.setShortcut('Ctrl+0')
        resetZoomAction.triggered.connect(lambda: self._set_zoom(0))
        menu.addAction(resetZoomAction)
        self.actions['resetzoom'] = resetZoomAction

    def _safe_wait_for_handler(self, timeout_ms=None):
        ed = self.currentEditor()
        handler = getattr(ed, 'file_handler', None) if ed is not None else None
        if not handler:
            return
        try:
            running = handler.isRunning()
        except RuntimeError:
            if ed is not None:
                setattr(ed, 'file_handler', None)
            return
        if running:
            try:
                if timeout_ms is None:
                    handler.wait()
                else:
                    handler.wait(timeout_ms)
            except RuntimeError:
                if ed is not None:
                    setattr(ed, 'file_handler', None)

    def _on_handler_finished(self, editor_obj, handler_obj):
        if getattr(editor_obj, 'file_handler', None) is handler_obj:
            setattr(editor_obj, 'file_handler', None)

    def _on_handler_destroyed(self, editor_obj, handler_obj, destroyed_obj=None):
        if getattr(editor_obj, 'file_handler', None) is handler_obj:
            setattr(editor_obj, 'file_handler', None)

    def _zoom_delta(self, delta):
        try:
            current = int(getattr(self, 'zoom_level', 0))
        except Exception:
            current = 0
        new_level = current + int(delta)
        new_level = max(-10, min(20, new_level))
        ed = self.currentEditor()
        if ed:
            ed.zoomTo(new_level)
            actual = int(ed.SendScintilla(QsciScintillaBase.SCI_GETZOOM))
        else:
            actual = new_level
        self.zoom_level = actual
        self.settings.setValue("view/zoom", actual)

    def _set_zoom(self, level):
        level = int(level)
        level = max(-10, min(20, level))
        ed = self.currentEditor()
        if ed:
            ed.zoomTo(level)
            actual = int(ed.SendScintilla(QsciScintillaBase.SCI_GETZOOM))
        else:
            actual = level
        self.zoom_level = actual
        self.settings.setValue("view/zoom", actual)

    def _on_zoom_changed(self, level):
        try:
            self.zoom_level = int(level)
        except Exception:
            self.zoom_level = 0
        self.settings.setValue("view/zoom", self.zoom_level)

    def openFindReplaceDialog(self):
        ed = self.currentEditor()
        dialog = FindReplaceDialog(ed) if ed else FindReplaceDialog(Editor(self))
        dialog.exec_()

    def openLanguageSelector(self):
        languages_map = self._available_language_lexers()
        names = [n for n in languages_map.keys()]
        if 'Plain Text' in names:
            names.remove('Plain Text')
            names = ['Plain Text'] + sorted(names)
        else:
            names = sorted(names)
        current = self._current_language_name()
        dialog = LanguageSelectDialog(self, names, current)
        if dialog.exec_() == QDialog.Accepted:
            chosen = dialog.selected_language()
            if self.setLexerByLanguageName(chosen):
                if self.current_file:
                    real = os.path.realpath(self.current_file).replace('\\','/')
                    self.settings.setValue(f"syntax/overrides/{real}", chosen)
            else:
                QMessageBox.warning(self, 'Language', f'Failed to apply language: {chosen}')

    def importFromWeb(self):
        ed = self.currentEditor()
        if ed is None:
            ed = Editor(self)
            ed.setEolMode(QsciScintilla.EolWindows)
            self._attach_editor(ed, "Untitled")
        dialog = ImportFromWebDialog(ed, app_context=self.app_context)
        dialog.exec_()

    def closeTab(self, index):
        ed = self.tabWidget.widget(index)
        if not ed:
            return
        unsaved = getattr(ed, 'unsaved_changes', False)
        if unsaved:
            dialog = UnsavedWorkDialog(self)
            result = dialog.exec_()
            if result == QDialog.Accepted:
                self.tabWidget.setCurrentIndex(index)
                if not self.saveFile():
                    return
            elif result == QDialog.Rejected:
                return
        handler = getattr(ed, 'file_handler', None)
        if handler:
            try:
                if handler.isRunning():
                    handler.wait()
            except RuntimeError:
                pass
            setattr(ed, 'file_handler', None)
        self.tabWidget.removeTab(index)
        if self.tabWidget.count() == 0:
            self.newFile()

    def _start_file_load(self, ed, file_path):
        setattr(ed, 'file_path', file_path)
        self._applySavedSyntaxOrDetect(file_path)
        gen = int(getattr(ed, 'open_generation', 0)) + 1
        setattr(ed, 'open_generation', gen)
        prev = getattr(ed, 'file_handler', None)
        if prev is not None:
            try:
                prev.file_content_loaded.disconnect()
            except Exception:
                pass
        handler = FileHandler(file_path)
        handler.file_load_started.connect(lambda path, encoding, newline, ed=ed, gen=gen: self._on_file_load_started(ed, gen, path, encoding, newline))
        handler.file_chunk_loaded.connect(lambda path, chunk, is_last, ed=ed, gen=gen: self._on_file_chunk_loaded(ed, gen, path, chunk, is_last))
        handler.file_content_loaded.connect(lambda path, content, encoding, newline, ed=ed, gen=gen: self._on_file_content_loaded(ed, gen, path, content, encoding, newline))
        handler.finished.connect(handler.deleteLater)
        handler.finished.connect(partial(self._on_handler_finished, ed, handler))
        try:
            handler.destroyed.connect(partial(self._on_handler_destroyed, ed, handler))
        except Exception:
            pass
        handler.start()
        setattr(ed, 'file_handler', handler)

    def _require_git(self):
        if _gitpy is None:
            QMessageBox.critical(self, 'Git', 'Git is not installed. Please install Git to use Git features.')
            return False
        return True

    def _require_repo(self):
        if not self._require_git():
            return None
        if self.repo is None:
            QMessageBox.warning(self, 'Git', 'No repository is currently open. Use Git > Open Repository...')
            return None
        return self.repo

    def openRepository(self):
        if not self._require_git():
            return
        repo_path = QFileDialog.getExistingDirectory(self, 'Select Git Repository')
        if not repo_path:
            return
        try:
            self.repo = _gitpy.Repo(repo_path)
            self.current_folder = repo_path
            if self.fileTreeDock is None:
                self.createFileExplorer(repo_path)
            else:
                try:
                    self.fileModel.setRootPath(repo_path)
                    self.fileTreeView.setRootIndex(self.fileModel.index(repo_path))
                except Exception:
                    pass
                self.fileTreeDock.show()
            try:
                self.setWindowTitle(f"Construct - {os.path.basename(repo_path)}")
            except Exception:
                pass
        except Exception as e:
            QMessageBox.critical(self, 'Git', f'Failed to open repository: {e}')

    def gitStatus(self):
        repo = self._require_repo()
        if not repo:
            return
        try:
            status = repo.git.status()
        except Exception as e:
            QMessageBox.critical(self, 'Git', f'Failed to get status: {e}')
            return
        dlg = QDialog(self)
        dlg.setWindowTitle('Git Status')
        layout = QVBoxLayout(dlg)
        te = QTextEdit(dlg)
        te.setReadOnly(True)
        te.setPlainText(status)
        layout.addWidget(te)
        dlg.resize(700, 500)
        dlg.exec_()

    def stageCurrentFile(self):
        repo = self._require_repo()
        if not repo:
            return
        ed = self.currentEditor()
        path = getattr(ed, 'file_path', None) if ed else None
        if not path:
            QMessageBox.information(self, 'Git', 'No file to stage in the current tab.')
            return
        try:
            repo.git.add(path)
            QMessageBox.information(self, 'Git', f'Staged: {os.path.basename(path)}')
        except Exception as e:
            QMessageBox.critical(self, 'Git', f'Failed to stage file: {e}')

    def stageAllChanges(self):
        repo = self._require_repo()
        if not repo:
            return
        try:
            repo.git.add('--all')
            QMessageBox.information(self, 'Git', 'All changes staged.')
        except Exception as e:
            QMessageBox.critical(self, 'Git', f'Failed to stage changes: {e}')

    def commitChanges(self):
        repo = self._require_repo()
        if not repo:
            return
        message, ok = QInputDialog.getText(self, 'Git Commit', 'Enter commit message:')
        if not ok or not message:
            return
        try:
            repo.index.commit(message)
            QMessageBox.information(self, 'Git', 'Changes committed.')
        except Exception as e:
            QMessageBox.critical(self, 'Git', f'Failed to commit: {e}')

    def fetchChanges(self):
        repo = self._require_repo()
        if not repo:
            return
        try:
            repo.remotes.origin.fetch()
            QMessageBox.information(self, 'Git', 'Fetched from origin.')
        except Exception as e:
            QMessageBox.critical(self, 'Git', f'Failed to fetch: {e}')

    def pullChanges(self):
        repo = self._require_repo()
        if not repo:
            return
        try:
            repo.remotes.origin.pull()
            QMessageBox.information(self, 'Git', 'Pulled latest changes.')
        except Exception as e:
            QMessageBox.critical(self, 'Git', f'Failed to pull: {e}')

    def pushChanges(self):
        repo = self._require_repo()
        if not repo:
            return
        try:
            repo.remotes.origin.push()
            QMessageBox.information(self, 'Git', 'Pushed to origin.')
        except Exception as e:
            QMessageBox.critical(self, 'Git', f'Failed to push: {e}')

    def switchBranch(self):
        repo = self._require_repo()
        if not repo:
            return
        try:
            branches = [b.name for b in repo.branches]
        except Exception as e:
            QMessageBox.critical(self, 'Git', f'Failed to list branches: {e}')
            return
        if not branches:
            QMessageBox.information(self, 'Git', 'No branches found.')
            return
        branch, ok = QInputDialog.getItem(self, 'Switch Branch', 'Select branch:', branches, 0, False)
        if not ok or not branch:
            return
        try:
            repo.git.checkout(branch)
            QMessageBox.information(self, 'Git', f'Switched to {branch}.')
        except Exception as e:
            QMessageBox.critical(self, 'Git', f'Failed to switch branch: {e}')

    def createBranch(self):
        repo = self._require_repo()
        if not repo:
            return
        name, ok = QInputDialog.getText(self, 'Create Branch', 'New branch name:')
        if not ok or not name:
            return
        try:
            repo.git.checkout('-b', name)
            QMessageBox.information(self, 'Git', f'Created and switched to {name}.')
        except Exception as e:
            QMessageBox.critical(self, 'Git', f'Failed to create branch: {e}')

    def showLog(self):
        repo = self._require_repo()
        if not repo:
            return
        try:
            log = repo.git.log('--oneline', '--graph', '--decorate', '-n', '200')
        except Exception as e:
            QMessageBox.critical(self, 'Git', f'Failed to get log: {e}')
            return
        dlg = QDialog(self)
        dlg.setWindowTitle('Git Log')
        layout = QVBoxLayout(dlg)
        te = QTextEdit(dlg)
        te.setReadOnly(True)
        te.setPlainText(log)
        layout.addWidget(te)
        dlg.resize(800, 600)
        dlg.exec_()

    def diffCurrentFile(self):
        repo = self._require_repo()
        if not repo:
            return
        ed = self.currentEditor()
        path = getattr(ed, 'file_path', None) if ed else None
        if not path:
            QMessageBox.information(self, 'Git', 'No file in the current tab.')
            return
        try:
            diff = repo.git.diff('HEAD', '--', path)
            if not diff:
                diff = repo.git.diff('--', path)
        except Exception as e:
            QMessageBox.critical(self, 'Git', f'Failed to diff: {e}')
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(f'Diff: {os.path.basename(path)}')
        layout = QVBoxLayout(dlg)
        te = QTextEdit(dlg)
        te.setReadOnly(True)
        te.setPlainText(diff or 'No differences.')
        layout.addWidget(te)
        dlg.resize(900, 600)
        dlg.exec_()

    def discardCurrentFileChanges(self):
        repo = self._require_repo()
        if not repo:
            return
        ed = self.currentEditor()
        path = getattr(ed, 'file_path', None) if ed else None
        if not path:
            QMessageBox.information(self, 'Git', 'No file in the current tab.')
            return
        reply = QMessageBox.question(self, 'Discard Changes', f'Discard uncommitted changes to "{os.path.basename(path)}"?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        try:
            repo.git.checkout('--', path)
            QMessageBox.information(self, 'Git', 'Changes discarded.')
        except Exception as e:
            QMessageBox.critical(self, 'Git', f'Failed to discard changes: {e}')

    def openFolder(self):
        folder = QFileDialog.getExistingDirectory(self, "Open Folder")
        if not folder:
            return
        self.current_folder = folder
        if _gitpy is not None:
            try:
                self.repo = _gitpy.Repo(folder)
            except Exception:
                self.repo = None
        if self.fileTreeDock is None:
            self.createFileExplorer(folder)
        else:
            try:
                self.fileModel.setRootPath(folder)
                self.fileTreeView.setRootIndex(self.fileModel.index(folder))
            except Exception:
                pass
            self.fileTreeDock.show()

    def createFileExplorer(self, root_path):
        self.fileTreeDock = QDockWidget("File Explorer", self)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        toolbar.setStyleSheet("QToolBar { border: none; padding: 0px; margin: 0px; }")
        toolbar.setContentsMargins(0, 0, 5, 0)
        toolbar.setFixedHeight(28)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        refreshAction = QAction("Refresh", self)
        refreshAction.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        refreshAction.setToolTip("Refresh File Explorer")
        refreshAction.triggered.connect(self.refreshFileExplorer)
        toolbar.addAction(refreshAction)
        newFileAction = QAction("New File", self)
        newFileAction.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        newFileAction.setToolTip("Create New File")
        newFileAction.triggered.connect(lambda: self.createNewFile(root_path))
        toolbar.addAction(newFileAction)
        newFolderAction = QAction("New Folder", self)
        newFolderAction.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        newFolderAction.setToolTip("Create New Folder")
        newFolderAction.triggered.connect(lambda: self.createNewDirectory(root_path))
        toolbar.addAction(newFolderAction)
        layout.addWidget(toolbar)
        self.fileTreeView = QTreeView(container)
        self.fileModel = QFileSystemModel()
        self.fileModel.setRootPath(root_path)
        self.fileTreeView.setModel(self.fileModel)
        try:
            self.fileTreeView.setRootIndex(self.fileModel.index(root_path))
        except Exception:
            pass
        self.fileTreeView.doubleClicked.connect(self.onFileTreeDoubleClicked)
        self.setupFileTreeContextMenu()
        layout.addWidget(self.fileTreeView)
        self.fileTreeDock.setWidget(container)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.fileTreeDock)

    def openFileByPath(self, file_path):
        if not (file_path and os.path.isfile(file_path)):
            return
        ed = self.currentEditor()
        reuse = False
        if ed is not None:
            idx = self.tabWidget.indexOf(ed)
            try:
                title = self.tabWidget.tabText(idx) if idx != -1 else ""
            except Exception:
                title = ""
            is_untitled = (title.strip().lower() == 'untitled') and not getattr(ed, 'file_path', None)
            try:
                empty = not bool(ed.text())
            except Exception:
                empty = True
            reuse = is_untitled and empty
        if not reuse:
            ed = Editor(self)
            ed.setEolMode(QsciScintilla.EolWindows)
            self._attach_editor(ed, os.path.basename(file_path))
        self._start_file_load(ed, file_path)

    def onFileTreeDoubleClicked(self, index):
        try:
            file_path = self.fileModel.filePath(index)
        except Exception:
            return
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
            context_menu.addSeparator()
            create_submenu = QMenu("Create", context_menu)
            new_file_action = QAction("New File", self)
            new_file_action.triggered.connect(lambda: self.createNewFile(file_path))
            create_submenu.addAction(new_file_action)
            new_dir_action = QAction("New Directory", self)
            new_dir_action.triggered.connect(lambda: self.createNewDirectory(file_path))
            create_submenu.addAction(new_dir_action)
            context_menu.addMenu(create_submenu)
            rename_action = QAction("Rename", self)
            rename_action.triggered.connect(lambda: self.renameFileOrDir(file_path))
            context_menu.addAction(rename_action)
            delete_action = QAction("Delete" + (" Directory" if os.path.isdir(file_path) else ""), self)
            delete_action.triggered.connect(lambda: self.deleteFileOrDir(file_path))
            context_menu.addAction(delete_action)
            context_menu.addSeparator()
            cut_action = QAction("Cut", self)
            cut_action.triggered.connect(lambda: self.cutFileOrDir(file_path))
            context_menu.addAction(cut_action)
            copy_action = QAction("Copy", self)
            copy_action.triggered.connect(lambda: self.copyFileOrDir(file_path))
            context_menu.addAction(copy_action)
            if hasattr(self, 'copied_file_path') and self.copied_file_path:
                paste_action = QAction("Paste", self)
                paste_action.triggered.connect(lambda: self.pasteFileOrDir(file_path))
                context_menu.addAction(paste_action)
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
            if hasattr(self, 'copied_file_path') and self.copied_file_path:
                paste_action = QAction("Paste", self)
                paste_action.triggered.connect(lambda: self.pasteFileOrDir(root_path))
                context_menu.addAction(paste_action)
        context_menu.exec_(self.fileTreeView.viewport().mapToGlobal(position))

    def createNewFile(self, path):
        directory = os.path.dirname(path) if os.path.isfile(path) else path
        file_name, ok = QInputDialog.getText(self, "New File", "Enter file name:")
        if ok and file_name:
            file_path = os.path.join(directory, file_name)
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create file: {e}")

    def createNewDirectory(self, path):
        directory = os.path.dirname(path) if os.path.isfile(path) else path
        dir_name, ok = QInputDialog.getText(self, "New Directory", "Enter directory name:")
        if ok and dir_name:
            dir_path = os.path.join(directory, dir_name)
            try:
                os.makedirs(dir_path, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create directory: {e}")

    def renameFileOrDir(self, path):
        old_name = os.path.basename(path)
        new_name, ok = QInputDialog.getText(self, "Rename", "Enter new name:", text=old_name)
        if ok and new_name and new_name != old_name:
            new_path = os.path.join(os.path.dirname(path), new_name)
            try:
                if self.current_file and os.path.realpath(self.current_file) == os.path.realpath(path):
                    self.current_file = new_path
                os.rename(path, new_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to rename: {e}")

    def deleteFileOrDir(self, path):
        name = os.path.basename(path)
        if os.path.isdir(path):
            msg = f"Are you sure you want to delete the directory '{name}' and all its contents?"
        else:
            msg = f"Are you sure you want to delete '{name}'?"
        reply = QMessageBox.question(self, "Confirm Delete", msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            if self.current_file and os.path.realpath(self.current_file).startswith(os.path.realpath(path)):
                self.newFile()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete: {e}")

    def copyFileOrDir(self, path):
        self.copied_file_path = path
        self.is_cut_operation = False

    def cutFileOrDir(self, path):
        self.copied_file_path = path
        self.is_cut_operation = True

    def pasteFileOrDir(self, dest_path):
        if not getattr(self, 'copied_file_path', None):
            return
        if os.path.isfile(dest_path):
            dest_path = os.path.dirname(dest_path)
        source_path = self.copied_file_path
        source_name = os.path.basename(source_path)
        target_path = os.path.join(dest_path, source_name)
        is_cut = getattr(self, 'is_cut_operation', False)
        if is_cut and os.path.normpath(os.path.dirname(source_path)) == os.path.normpath(dest_path):
            return
        if os.path.isdir(source_path) and os.path.realpath(dest_path).startswith(os.path.realpath(source_path)):
            return
        if os.path.exists(target_path):
            reply = QMessageBox.question(self, "File Exists", f"'{source_name}' already exists in destination. Overwrite?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
        try:
            if is_cut:
                if os.path.exists(target_path):
                    if os.path.isdir(target_path):
                        shutil.rmtree(target_path)
                    else:
                        os.remove(target_path)
                shutil.move(source_path, target_path)
                self.copied_file_path = None
                self.is_cut_operation = False
            else:
                if os.path.isdir(source_path):
                    if os.path.exists(target_path):
                        shutil.rmtree(target_path)
                    shutil.copytree(source_path, target_path)
                else:
                    shutil.copy2(source_path, target_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to paste: {e}")

    def refreshFileExplorer(self):
        if getattr(self, 'fileModel', None):
            current_path = self.fileModel.rootPath()
            try:
                self.fileModel.setRootPath("")
                self.fileModel.setRootPath(current_path)
            except Exception:
                pass

    def newFile(self):
        ed = Editor(self)
        ed.setEolMode(QsciScintilla.EolWindows)
        self._attach_editor(ed, "Untitled")
        self.setLexerForFilePath(None)

    def openFile(self):
        options = QFileDialog.Options()
        try:
            file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Text Files (*.txt);;All Files (*)", options=options)
            if file_name:
                ed = self.currentEditor()
                reuse = False
                if ed is not None:
                    idx = self.tabWidget.indexOf(ed)
                    try:
                        title = self.tabWidget.tabText(idx) if idx != -1 else ""
                    except Exception:
                        title = ""
                    is_untitled = (title.strip().lower() == 'untitled') and not getattr(ed, 'file_path', None)
                    try:
                        empty = not bool(ed.text())
                    except Exception:
                        empty = True
                    reuse = is_untitled and empty
                if not reuse:
                    ed = Editor(self)
                    ed.setEolMode(QsciScintilla.EolWindows)
                    self._attach_editor(ed, os.path.basename(file_name))
                self._start_file_load(ed, file_name)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open file: {e}")

    def _on_file_content_loaded(self, gen, path, content, encoding, newline):
        if gen != self._open_generation:
            return
        self.loadFileContent(path, content, encoding, newline)

    def _on_file_load_started(self, ed, gen, path, encoding, newline):
        if gen != getattr(ed, 'open_generation', 0):
            return
        if getattr(ed, 'file_path', None) is None or os.path.realpath(path) != os.path.realpath(getattr(ed, 'file_path')):
            return
        self._applySavedSyntaxOrDetect(path)
        if encoding:
            setattr(ed, 'encoding', encoding)
        if newline:
            setattr(ed, 'newline', newline)
            if newline == "\r\n":
                ed.setEolMode(QsciScintilla.EolWindows)
            elif newline == "\r":
                ed.setEolMode(QsciScintilla.EolMac)
            else:
                ed.setEolMode(QsciScintilla.EolUnix)
        with QSignalBlocker(ed):
            ed.setText("")
        title = os.path.basename(getattr(ed, 'file_path'))
        idx = self.tabWidget.indexOf(ed)
        if idx != -1:
            self.tabWidget.setTabText(idx, title)
        self.addToRecentFiles(getattr(ed, 'file_path'))
        setattr(ed, 'unsaved_changes', False)
        if ed is self.currentEditor():
            self.updateStatusBar(after_save=True)

    def _on_file_chunk_loaded(self, ed, gen, path, chunk, is_last):
        if gen != getattr(ed, 'open_generation', 0):
            return
        if getattr(ed, 'file_path', None) is None or os.path.realpath(path) != os.path.realpath(getattr(ed, 'file_path')):
            return
        if chunk:
            with QSignalBlocker(ed):
                ed.append_text(chunk)
        if is_last:
            setattr(ed, 'unsaved_changes', False)
            if ed is self.currentEditor():
                self.updateStatusBar(after_save=True)

    def _on_file_content_loaded(self, ed, gen, path, content, encoding, newline):
        if gen != getattr(ed, 'open_generation', 0):
            return
        if getattr(ed, 'file_path', None) is None or os.path.realpath(path) != os.path.realpath(getattr(ed, 'file_path')):
            return
        if encoding is None:
            QMessageBox.critical(self, "Error", content)
            return
        self._applySavedSyntaxOrDetect(path)
        if encoding:
            setattr(ed, 'encoding', encoding)
        if newline:
            setattr(ed, 'newline', newline)
            if newline == "\r\n":
                ed.setEolMode(QsciScintilla.EolWindows)
            elif newline == "\r":
                ed.setEolMode(QsciScintilla.EolMac)
            else:
                ed.setEolMode(QsciScintilla.EolUnix)
        with QSignalBlocker(ed):
            ed.setPlainText(content)
        title = os.path.basename(getattr(ed, 'file_path'))
        idx = self.tabWidget.indexOf(ed)
        if idx != -1:
            self.tabWidget.setTabText(idx, title)
        self.addToRecentFiles(getattr(ed, 'file_path'))
        setattr(ed, 'unsaved_changes', False)
        if ed is self.currentEditor():
            self.updateStatusBar(after_save=True)

    def saveFile(self):
        ed = self.currentEditor()
        if not ed:
            return False
        content = ed.toPlainText()
        enc = getattr(ed, 'encoding', None) or 'utf-8'
        try:
            content.encode(enc)
        except UnicodeEncodeError:
            return self.promptForEncoding(content)
        if getattr(ed, 'file_path', None):
            return self.saveFileWithEncoding(content, enc)
        else:
            return self.saveFileAs(content)

    def promptForEncoding(self, content):
        encoding, ok = QInputDialog.getItem(self, "Choose Encoding", "Select Encoding", 
                                             ["UTF-8", "ISO-8859-1", "Windows-1252", "UTF-16"], 0, False)
        if ok:
            return self.saveFileWithEncoding(content, encoding)
        return False
    
    def saveFileWithEncoding(self, content, encoding):
        ed = self.currentEditor()
        if ed and getattr(ed, 'file_path', None):
            try:
                with open(getattr(ed, 'file_path'), 'w', encoding=encoding, newline=getattr(ed, 'newline', '\r\n')) as file:
                    file.write(content)
                setattr(ed, 'encoding', encoding)
                setattr(ed, 'unsaved_changes', False)
                self.updateStatusBar(after_save=True)
                return True
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save file with encoding '{encoding}': {e}")
                return False
        return False

    def saveFileAs(self, content=None):
        options = QFileDialog.Options()
        try:
            file_name, _ = QFileDialog.getSaveFileName(self, "Save File As", "", "Text Files (*.txt);;All Files (*)", options=options)
            if file_name:
                ed = self.currentEditor()
                if not ed:
                    return False
                setattr(ed, 'file_path', file_name)
                self._applySavedSyntaxOrDetect(file_name)
                if content is None:
                    content = ed.toPlainText()
                enc = getattr(ed, 'encoding', None) or 'utf-8'
                idx = self.tabWidget.indexOf(ed)
                if idx != -1:
                    self.tabWidget.setTabText(idx, os.path.basename(file_name))
                return self.saveFileWithEncoding(content, enc)
            return False
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save file: {e}")
            return False

    def updateStatusBar(self, after_save=False):
        ed = self.currentEditor()
        if not ed:
            self.statusBar.clearMessage()
            return
        try:
            cursor = ed.textCursor()
            self.line = cursor.blockNumber() + 1
            self.column = cursor.columnNumber() + 1
        except Exception:
            self.line, self.column = 1, 1
        try:
            self.char_count = ed.length()
        except Exception:
            try:
                self.char_count = ed.textLength()
            except Exception:
                self.char_count = len(ed.text())
        unsaved = getattr(ed, 'unsaved_changes', False)
        encoding = getattr(ed, 'encoding', 'UTF-8')
        asterisk = "" if after_save else ("*" if unsaved else "")
        self.statusBar.showMessage(f"Line: {self.line} | Column: {self.column} | Characters: {self.char_count} | Encoding: {encoding} {asterisk}")
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
        filtered = []
        seen = set()
        for p in self.recent_files:
            real = os.path.realpath(p)
            if not (os.path.exists(real) and os.access(real, os.R_OK)):
                continue
            if real in seen:
                continue
            seen.add(real)
            filtered.append(real)
        filtered = filtered[:5]
        if filtered != self.recent_files:
            self.recent_files = filtered
            self.settings.setValue("recentFiles", self.recent_files)
        if not self.recent_files:
            self.recentFilesMenu.setEnabled(False)
        else:
            self.recentFilesMenu.setEnabled(True)
            for path in self.recent_files:
                file_name = os.path.basename(path)
                action = QAction(file_name, self)
                action.triggered.connect(lambda checked, p=path: self.openRecentFile(p))
                action.setToolTip(path)
                self.recentFilesMenu.addAction(action)
            self.recentFilesMenu.addSeparator()
            clearAction = QAction("Clear Recently Opened Files", self)
            clearAction.triggered.connect(self.clearRecentFiles)
            self.recentFilesMenu.addAction(clearAction)

    def openRecentFile(self, file_path):
        if os.path.exists(file_path):
            ed = self.currentEditor()
            reuse = False
            if ed is not None:
                idx = self.tabWidget.indexOf(ed)
                try:
                    title = self.tabWidget.tabText(idx) if idx != -1 else ""
                except Exception:
                    title = ""
                is_untitled = (title.strip().lower() == 'untitled') and not getattr(ed, 'file_path', None)
                try:
                    empty = not bool(ed.text())
                except Exception:
                    empty = True
                reuse = is_untitled and empty
            if not reuse:
                ed = Editor(self)
                ed.setEolMode(QsciScintilla.EolWindows)
                self._attach_editor(ed, os.path.basename(file_path))
            self._start_file_load(ed, file_path)
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
        


if __name__ == '__main__':
    app = QApplication(sys.argv)
    loadStyle()
    file_to_open = None
    if len(sys.argv) > 1:
        file_to_open = sys.argv[1]
    construct = Construct(file_to_open)
    construct.show()
    sys.exit(app.exec_())
