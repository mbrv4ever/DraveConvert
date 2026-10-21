# -*- coding: utf-8 -*-
"""DraveConvert - lokale media- en bestandsconverter (Dravenlock).
Afbeeldingen via Pillow, audio/video via ffmpeg. Lokaal, offline, toegankelijk.
"""
import os
import sys
import json
import shutil
import zipfile
import urllib.request
import subprocess
import traceback

APP_NAAM = "DraveConvert"
APP_VERSIE = "0.1.1"
CONTACT = "service@dravenlock.nl"
DONATIE_URL = "https://paypal.me/roger076"

WINDOWS = sys.platform.startswith("win")
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


# ---- foutopvang naar bestand (naast de exe) ----
def _basis_map():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASIS = _basis_map()
DATA_MAP = os.path.join(BASIS, "DraveConvert-data")
FFMPEG_MAP = os.path.join(DATA_MAP, "ffmpeg")
CONFIG_BESTAND = os.path.join(DATA_MAP, "config.json")


def _excepthook(t, w, tb):
    try:
        os.makedirs(DATA_MAP, exist_ok=True)
        with open(os.path.join(DATA_MAP, "app-fout.txt"), "w", encoding="utf-8") as f:
            f.write("".join(traceback.format_exception(t, w, tb)))
    except Exception:
        pass
    sys.__excepthook__(t, w, tb)


sys.excepthook = _excepthook

# ---- kleuren / huisstijl ----
BG = "#0e0e11"; PANEL = "#16161b"; PANEL2 = "#1c1c22"
TEXT = "#d4d4d4"; MUTED = "#8a8a94"; ACCENT = "#6fa3d6"
LINE = "#23232b"; WARN = "#d68a6f"; GOED = "#7fb069"

# ---- formaten ----
CATEGORIEEN = ["afbeelding", "audio", "video"]
DOELFORMATEN = {
    "afbeelding": ["png", "jpg", "webp", "bmp", "gif", "tiff"],
    "audio": ["mp3", "wav", "flac", "aac", "ogg", "m4a"],
    "video": ["mp4", "webm", "mkv", "mov", "gif"],
}
INVOER_EXT = {
    "afbeelding": {"png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff", "tif",
                   "ico", "heic"},
    "audio": {"mp3", "wav", "flac", "aac", "ogg", "m4a", "wma", "opus", "aiff"},
    "video": {"mp4", "webm", "mkv", "mov", "avi", "flv", "wmv", "m4v", "mpg",
              "mpeg", "ts"},
}
# ffmpeg-opties per doelformaat (video/audio)
FF_OPTIES = {
    "mp3": ["-vn", "-b:a", "192k"],
    "m4a": ["-vn", "-c:a", "aac", "-b:a", "192k"],
    "aac": ["-vn", "-c:a", "aac", "-b:a", "192k"],
    "ogg": ["-vn", "-c:a", "libvorbis", "-q:a", "5"],
    "flac": ["-vn", "-c:a", "flac"],
    "wav": ["-vn"],
    "mp4": ["-c:v", "libx264", "-crf", "23", "-preset", "medium",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"],
    "webm": ["-c:v", "libvpx-vp9", "-crf", "32", "-b:v", "0",
             "-c:a", "libopus"],
    "mkv": ["-c:v", "libx264", "-crf", "23", "-preset", "medium", "-c:a", "aac"],
    "mov": ["-c:v", "libx264", "-crf", "23", "-preset", "medium", "-c:a", "aac"],
    "gif": ["-vf", "fps=12,scale=480:-1:flags=lanczos"],
}

# ffmpeg-download (Windows). Roger test live; auto-download op zijn pc.
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

STANDAARD_CONFIG = {
    "taal": "auto",
    "uitvoermap": "",          # leeg = naast het bronbestand
    "afb_kwaliteit": 90,
    "afb_maxbreedte": 0,       # 0 = origineel
    "overschrijven": False,
}


def laad_config():
    cfg = dict(STANDAARD_CONFIG)
    try:
        with open(CONFIG_BESTAND, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            cfg.update(data)
    except Exception:
        pass
    return cfg


def bewaar_config(cfg):
    try:
        os.makedirs(DATA_MAP, exist_ok=True)
        with open(CONFIG_BESTAND, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


# ---------- i18n ----------
TEKST = {
    "nl": {
        "ondertitel": "Lokale media- en bestandsconverter",
        "menu_help": "Help", "menu_snelgids": "Snelgids", "menu_over": "Over",
        "menu_instellingen": "Instellingen", "menu_taal": "Taal",
        "categorie": "Soort", "cat_afbeelding": "Afbeelding", "cat_audio": "Audio",
        "cat_video": "Video", "doelformaat": "Omzetten naar",
        "bestanden": "Bestanden", "toevoegen": "Bestanden toevoegen",
        "verwijderen": "Verwijderen", "wissen": "Lijst wissen",
        "sleep_hier": "Sleep hier je bestanden naartoe, of klik op \u2018Bestanden toevoegen\u2019.",
        "uitvoermap": "Uitvoermap", "uitvoermap_kies": "Kiezen\u2026",
        "uitvoermap_naast": "(leeg = naast het bronbestand)",
        "kwaliteit": "Kwaliteit", "maxbreedte": "Max. breedte (px, 0 = origineel)",
        "overschrijven": "Bestaande bestanden overschrijven",
        "converteren": "Converteren", "stoppen": "Stoppen",
        "klaar_n": "Klaar: {ok} gelukt, {fout} mislukt.",
        "bezig": "Bezig\u2026 {i}/{n}: {naam}",
        "geen_bestanden": "Voeg eerst bestanden toe.",
        "ffmpeg_kop": "ffmpeg (voor audio/video)",
        "ffmpeg_aanwezig": "ffmpeg gevonden: {pad}",
        "ffmpeg_mist": "ffmpeg niet gevonden \u2014 nodig voor audio en video.",
        "ffmpeg_download": "ffmpeg downloaden", "ffmpeg_zip": "ffmpeg-zip kiezen\u2026",
        "ffmpeg_nodig": "Voor audio/video is ffmpeg nodig. Download het hieronder of kies een zip.",
        "ffmpeg_bezig": "ffmpeg wordt gedownload\u2026 {mb}",
        "ffmpeg_klaar": "ffmpeg is ge\u00efnstalleerd.",
        "ffmpeg_mislukt": "Downloaden/uitpakken mislukt:\n\n{fout}",
        "open_map": "Uitvoermap openen",
        "donatie": "Donatie", "sluit": "Sluiten", "opslaan": "Opslaan",
        "annuleren": "Annuleren", "taal_auto": "Automatisch (computertaal)",
        "over_tekst": ("<b>{naam}</b> v{versie}<br><br>Een lokale, offline "
                       "converter voor afbeeldingen, audio en video. Geen cloud, "
                       "geen account \u2014 alles blijft op je eigen pc.<br><br>"
                       "Contact: {contact}<br>Donatie: {donatie}"),
        "fout_kop": "Er ging iets mis",
    },
    "en": {
        "ondertitel": "Local media and file converter",
        "menu_help": "Help", "menu_snelgids": "Quick guide", "menu_over": "About",
        "menu_instellingen": "Settings", "menu_taal": "Language",
        "categorie": "Type", "cat_afbeelding": "Image", "cat_audio": "Audio",
        "cat_video": "Video", "doelformaat": "Convert to",
        "bestanden": "Files", "toevoegen": "Add files",
        "verwijderen": "Remove", "wissen": "Clear list",
        "sleep_hier": "Drag your files here, or click \u2018Add files\u2019.",
        "uitvoermap": "Output folder", "uitvoermap_kies": "Choose\u2026",
        "uitvoermap_naast": "(empty = next to the source file)",
        "kwaliteit": "Quality", "maxbreedte": "Max. width (px, 0 = original)",
        "overschrijven": "Overwrite existing files",
        "converteren": "Convert", "stoppen": "Stop",
        "klaar_n": "Done: {ok} ok, {fout} failed.",
        "bezig": "Working\u2026 {i}/{n}: {naam}",
        "geen_bestanden": "Add files first.",
        "ffmpeg_kop": "ffmpeg (for audio/video)",
        "ffmpeg_aanwezig": "ffmpeg found: {pad}",
        "ffmpeg_mist": "ffmpeg not found \u2014 needed for audio and video.",
        "ffmpeg_download": "Download ffmpeg", "ffmpeg_zip": "Choose ffmpeg zip\u2026",
        "ffmpeg_nodig": "Audio/video needs ffmpeg. Download it below or pick a zip.",
        "ffmpeg_bezig": "Downloading ffmpeg\u2026 {mb}",
        "ffmpeg_klaar": "ffmpeg has been installed.",
        "ffmpeg_mislukt": "Download/extract failed:\n\n{fout}",
        "open_map": "Open output folder",
        "donatie": "Donate", "sluit": "Close", "opslaan": "Save",
        "annuleren": "Cancel", "taal_auto": "Automatic (system language)",
        "over_tekst": ("<b>{naam}</b> v{versie}<br><br>A local, offline converter "
                       "for images, audio and video. No cloud, no account \u2014 "
                       "everything stays on your own PC.<br><br>"
                       "Contact: {contact}<br>Donate: {donatie}"),
        "fout_kop": "Something went wrong",
    },
}


# ---------- Qt ----------
from PyQt6.QtCore import Qt, QUrl, QLocale, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QDesktopServices
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QComboBox, QListWidget, QListWidgetItem, QProgressBar,
    QFileDialog, QMessageBox, QDialog, QFormLayout, QDialogButtonBox,
    QSpinBox, QSlider, QCheckBox, QLineEdit, QPlainTextEdit, QStatusBar,
    QAbstractItemView)


def STIJL():
    return """
* { font-size: 15px; }
QMainWindow, QWidget, QDialog { background: %(bg)s; color: %(text)s; }
QLabel { color: %(text)s; }
QLabel#titel { font-size: 26px; font-weight: bold; }
QLabel#ondertitel { color: %(muted)s; }
QLabel#kop { font-size: 17px; font-weight: bold; }
QLabel#uitleg { color: %(muted)s; }
QLabel#info { background: %(panel2)s; color: %(text)s; border: 1px solid %(line)s;
    border-radius: 8px; padding: 8px 10px; }
QLabel#sleep { background: %(panel)s; color: %(muted)s; border: 2px dashed %(line)s;
    border-radius: 12px; padding: 22px; }
QPushButton { background: %(panel2)s; color: %(text)s; border: 1px solid %(line)s;
    border-radius: 8px; padding: 8px 14px; }
QPushButton:hover { border-color: %(accent)s; }
QPushButton:disabled { color: %(muted)s; }
QPushButton#primair { background: %(accent)s; color: #0e0e11; font-weight: bold; border: none; }
QPushButton#primair:hover { background: #84b4e0; }
QPushButton#stop { color: %(warn)s; }
QComboBox, QLineEdit, QSpinBox { background: %(panel2)s; color: %(text)s;
    border: 1px solid %(line)s; border-radius: 8px; padding: 7px 10px; }
QComboBox QAbstractItemView { background: %(panel2)s; color: %(text)s;
    selection-background-color: %(accent)s; selection-color: #0e0e11; }
QListWidget, QPlainTextEdit { background: %(panel)s; color: %(text)s;
    border: 1px solid %(line)s; border-radius: 8px; }
QListWidget::item:selected { background: %(accent)s; color: #0e0e11; }
QProgressBar { background: %(panel2)s; border: 1px solid %(line)s; border-radius: 8px;
    text-align: center; height: 18px; }
QProgressBar::chunk { background: %(accent)s; border-radius: 7px; }
QStatusBar { background: %(panel)s; color: %(muted)s; }
QMenuBar { background: %(bg)s; color: %(text)s; }
QMenuBar::item:selected { background: %(panel2)s; }
QMenu { background: %(panel)s; color: %(text)s; border: 1px solid %(line)s; }
QMenu::item:selected { background: %(accent)s; color: #0e0e11; }
QScrollBar:vertical { background: %(bg)s; width: 12px; }
QScrollBar::handle:vertical { background: %(panel2)s; border-radius: 6px; min-height: 24px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
""" % dict(bg=BG, panel=PANEL, panel2=PANEL2, text=TEXT, muted=MUTED,
           accent=ACCENT, line=LINE, warn=WARN, goed=GOED)


def _bundel_bestand(naam):
    """Pad naar een meegeleverd (read-only) bestand, werkt ook in de exe."""
    if getattr(sys, "frozen", False):
        p = os.path.join(getattr(sys, "_MEIPASS", BASIS), naam)
        if os.path.exists(p):
            return p
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), naam)


def app_icoon():
    for naam in ("app.ico", "logo.png"):
        p = _bundel_bestand(naam)
        if os.path.exists(p):
            ic = QIcon(p)
            if not ic.isNull():
                return ic
    return QIcon()


# ---------- ffmpeg ----------
def vind_ffmpeg():
    """Zoek ffmpeg: in DraveConvert-data, meegeleverd, of op het systeem."""
    naam = "ffmpeg.exe" if WINDOWS else "ffmpeg"
    # 1) in onze datamap (gedownload of uitgepakt)
    if os.path.isdir(FFMPEG_MAP):
        for wortel, _dirs, files in os.walk(FFMPEG_MAP):
            if naam in files:
                return os.path.join(wortel, naam)
    # 2) meegeleverd naast de exe
    p = _bundel_bestand(naam)
    if os.path.isfile(p):
        return p
    # 3) op het systeem (PATH)
    w = shutil.which("ffmpeg")
    if w:
        return w
    return ""


def pak_uit(zip_pad, doel):
    try:
        os.makedirs(doel, exist_ok=True)
        with zipfile.ZipFile(zip_pad) as z:
            z.extractall(doel)
        return True, ""
    except Exception as e:
        return False, str(e)


class DownloadThread(QThread):
    voortgang = pyqtSignal(int, int)
    klaar = pyqtSignal(bool, str)

    def __init__(self, url, zip_pad, doel):
        super().__init__()
        self.url = url; self.zip_pad = zip_pad; self.doel = doel

    def run(self):
        try:
            os.makedirs(os.path.dirname(self.zip_pad), exist_ok=True)
            req = urllib.request.Request(self.url, headers={"User-Agent": "DraveConvert"})
            with urllib.request.urlopen(req, timeout=60) as r:
                totaal = int(r.headers.get("Content-Length", 0))
                gedaan = 0
                with open(self.zip_pad, "wb") as f:
                    while True:
                        blok = r.read(65536)
                        if not blok:
                            break
                        f.write(blok); gedaan += len(blok)
                        self.voortgang.emit(gedaan, totaal)
            ok, fout = pak_uit(self.zip_pad, self.doel)
            try:
                os.remove(self.zip_pad)
            except Exception:
                pass
            self.klaar.emit(ok, fout)
        except Exception as e:
            self.klaar.emit(False, str(e))


# ---------- conversie ----------
def categorie_van(pad):
    ext = os.path.splitext(pad)[1].lower().lstrip(".")
    for cat, exts in INVOER_EXT.items():
        if ext in exts:
            return cat
    return ""


def converteer_afbeelding(src, dst, kwaliteit=90, maxbreedte=0):
    from PIL import Image
    im = Image.open(src)
    if maxbreedte and im.width > maxbreedte:
        h = int(im.height * maxbreedte / im.width)
        im = im.resize((maxbreedte, h), Image.LANCZOS)
    ext = os.path.splitext(dst)[1].lower()
    if ext in (".jpg", ".jpeg", ".bmp"):
        if im.mode in ("RGBA", "P", "LA"):
            fond = Image.new("RGB", im.size, (255, 255, 255))
            im2 = im.convert("RGBA")
            fond.paste(im2, mask=im2.split()[-1])
            im = fond
        else:
            im = im.convert("RGB")
    opts = {}
    if ext in (".jpg", ".jpeg"):
        opts = {"quality": int(kwaliteit), "optimize": True}
    elif ext == ".webp":
        opts = {"quality": int(kwaliteit)}
    im.save(dst, **opts)


def converteer_media(ffmpeg, src, dst, doel_ext):
    args = [ffmpeg, "-y", "-i", src] + FF_OPTIES.get(doel_ext, []) + [dst]
    r = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       creationflags=NO_WINDOW)
    if r.returncode != 0:
        uit = (r.stdout or b"").decode("utf-8", "replace")
        raise RuntimeError(uit[-500:] or "ffmpeg-fout")


class ConversieThread(QThread):
    voortgang = pyqtSignal(int, int, str)   # i, n, naam
    resultaat = pyqtSignal(str, bool, str)  # bestand, ok, fout
    klaar = pyqtSignal(int, int)            # ok, fout

    def __init__(self, taken, ffmpeg):
        super().__init__()
        self.taken = taken          # [(src, dst, categorie, doel_ext, kwal, maxb)]
        self.ffmpeg = ffmpeg
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        n = len(self.taken); ok = 0; fout = 0
        for i, (src, dst, cat, ext, kwal, maxb) in enumerate(self.taken, 1):
            if self._stop:
                break
            self.voortgang.emit(i, n, os.path.basename(src))
            try:
                os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
                if cat == "afbeelding":
                    converteer_afbeelding(src, dst, kwal, maxb)
                else:
                    converteer_media(self.ffmpeg, src, dst, ext)
                ok += 1
                self.resultaat.emit(os.path.basename(dst), True, "")
            except Exception as e:
                fout += 1
                self.resultaat.emit(os.path.basename(src), False, str(e))
        self.klaar.emit(ok, fout)


# ---------- dialogen ----------
class Dialoog(QDialog):
    """Maximaliseerbaar en gecentreerd op het hoofdvenster."""
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._gecentreerd = False
        try:
            self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
            self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, True)
        except Exception:
            pass

    def showEvent(self, e):
        super().showEvent(e)
        if self._gecentreerd:
            return
        self._gecentreerd = True
        try:
            par = self.parent()
            g = par.frameGeometry() if (par and par.isVisible()) \
                else self.screen().availableGeometry()
            self.move(g.center().x() - self.width() // 2,
                      g.center().y() - self.height() // 2)
        except Exception:
            pass


class OverDialoog(Dialoog):
    def __init__(self, v):
        super().__init__(v)
        self.setWindowTitle(v.t("menu_over"))
        self.resize(460, 240)
        lay = QVBoxLayout(self)
        lg = QLabel(); p = _bundel_bestand("logo.png")
        if os.path.exists(p):
            pm = QPixmap(p)
            if not pm.isNull():
                lg.setPixmap(pm.scaled(QSize(72, 72), Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation))
        lay.addWidget(lg)
        lab = QLabel(v.t("over_tekst").format(naam=APP_NAAM, versie=APP_VERSIE,
                                              contact=CONTACT, donatie=DONATIE_URL))
        lab.setWordWrap(True); lab.setOpenExternalLinks(True)
        lay.addWidget(lab)
        knop = QPushButton("\u2665 " + v.t("donatie")); knop.setObjectName("primair")
        knop.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(DONATIE_URL)))
        lay.addWidget(knop)


class InstellingenDialoog(Dialoog):
    def __init__(self, v):
        super().__init__(v)
        self.v = v
        self.setWindowTitle(v.t("menu_instellingen"))
        self.resize(440, 160)
        lay = QFormLayout(self)
        self.taal = QComboBox()
        self.taal.addItem(v.t("taal_auto"), "auto")
        self.taal.addItem("Nederlands", "nl")
        self.taal.addItem("English", "en")
        self.taal.setCurrentIndex({"auto": 0, "nl": 1, "en": 2}.get(
            v.cfg.get("taal", "auto"), 0))
        lay.addRow(v.t("menu_taal"), self.taal)
        self.chk_over = QCheckBox(v.t("overschrijven"))
        self.chk_over.setChecked(bool(v.cfg.get("overschrijven", False)))
        lay.addRow("", self.chk_over)
        kn = QDialogButtonBox(QDialogButtonBox.StandardButton.Save |
                              QDialogButtonBox.StandardButton.Cancel)
        kn.button(QDialogButtonBox.StandardButton.Save).setText(v.t("opslaan"))
        kn.button(QDialogButtonBox.StandardButton.Cancel).setText(v.t("annuleren"))
        kn.accepted.connect(self._ok); kn.rejected.connect(self.reject)
        lay.addRow(kn)

    def _ok(self):
        self.v.cfg["taal"] = self.taal.currentData()
        self.v.cfg["overschrijven"] = self.chk_over.isChecked()
        bewaar_config(self.v.cfg)
        self.accept()


class SnelgidsDialoog(Dialoog):
    def __init__(self, v):
        super().__init__(v)
        self.setWindowTitle(v.t("menu_snelgids"))
        self.resize(560, 460)
        lay = QVBoxLayout(self)
        txt = QPlainTextEdit(); txt.setReadOnly(True)
        if v.taal == "en":
            txt.setPlainText(
                "DraveConvert - quick guide\n\n"
                "1. Pick the type: Image, Audio or Video.\n"
                "2. Choose the target format.\n"
                "3. Add files (button or drag & drop). You can add many at once.\n"
                "4. Optionally set an output folder (empty = next to the source).\n"
                "5. For images you can set quality and a maximum width.\n"
                "6. Click Convert. Progress is shown at the bottom.\n\n"
                "Audio and video need ffmpeg. If it is missing, use the\n"
                "'Download ffmpeg' button (or pick a downloaded ffmpeg zip).\n\n"
                "Everything runs locally on your PC. No cloud, no account.")
        else:
            txt.setPlainText(
                "DraveConvert - snelgids\n\n"
                "1. Kies de soort: Afbeelding, Audio of Video.\n"
                "2. Kies het doelformaat (waarnaar je omzet).\n"
                "3. Voeg bestanden toe (knop of slepen-en-neerzetten). Meerdere mag.\n"
                "4. Stel eventueel een uitvoermap in (leeg = naast het bronbestand).\n"
                "5. Bij afbeeldingen kun je kwaliteit en een maximale breedte kiezen.\n"
                "6. Klik op Converteren. Onderaan zie je de voortgang.\n\n"
                "Audio en video hebben ffmpeg nodig. Ontbreekt het, gebruik dan de\n"
                "knop 'ffmpeg downloaden' (of kies een gedownloade ffmpeg-zip).\n\n"
                "Alles draait lokaal op je pc. Geen cloud, geen account.")
        lay.addWidget(txt)
        b = QPushButton(v.t("sluit")); b.setObjectName("primair"); b.clicked.connect(self.accept)
        lay.addWidget(b)


# ---------- hoofdvenster ----------
class Hoofdvenster(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cfg = laad_config()
        self.taal = self._taal()
        self.ffmpeg = vind_ffmpeg()
        self._thread = None
        self._dl = None
        self.setWindowTitle("%s v%s" % (APP_NAAM, APP_VERSIE))
        self.setWindowIcon(app_icoon())
        self.setAcceptDrops(True)
        self.resize(900, 680)
        self.setStyleSheet(STIJL())
        self._menu()
        self._bouw()
        self._cat_gewijzigd()
        self._ffmpeg_ververs()

    def _taal(self):
        t = self.cfg.get("taal", "auto")
        if t in ("nl", "en"):
            return t
        lc = QLocale.system().name().lower()
        return "nl" if lc.startswith("nl") else "en"

    def t(self, s):
        return TEKST.get(self.taal, TEKST["en"]).get(s, s)

    def _menu(self):
        bar = self.menuBar()
        m = bar.addMenu(self.t("menu_help"))
        a1 = m.addAction(self.t("menu_snelgids")); a1.triggered.connect(
            lambda: SnelgidsDialoog(self).exec())
        a2 = m.addAction(self.t("menu_instellingen")); a2.triggered.connect(self._instellingen)
        a3 = m.addAction(self.t("menu_over")); a3.triggered.connect(
            lambda: OverDialoog(self).exec())

    def _bouw(self):
        c = QWidget(); self.setCentralWidget(c)
        lay = QVBoxLayout(c)
        # kop
        kop = QHBoxLayout()
        logo = QLabel(); p = _bundel_bestand("logo.png")
        if os.path.exists(p):
            pm = QPixmap(p)
            if not pm.isNull():
                logo.setPixmap(pm.scaled(QSize(48, 48), Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation))
        kop.addWidget(logo)
        tt = QVBoxLayout()
        t1 = QLabel(APP_NAAM); t1.setObjectName("titel")
        t2 = QLabel(self.t("ondertitel")); t2.setObjectName("ondertitel")
        tt.addWidget(t1); tt.addWidget(t2)
        kop.addLayout(tt); kop.addStretch(1)
        lay.addLayout(kop)
        # keuze categorie + doelformaat
        rij = QHBoxLayout()
        rij.addWidget(QLabel(self.t("categorie")))
        self.cmb_cat = QComboBox()
        for cat in CATEGORIEEN:
            self.cmb_cat.addItem(self.t("cat_" + cat), cat)
        self.cmb_cat.currentIndexChanged.connect(self._cat_gewijzigd)
        rij.addWidget(self.cmb_cat)
        rij.addSpacing(16)
        rij.addWidget(QLabel(self.t("doelformaat")))
        self.cmb_doel = QComboBox()
        rij.addWidget(self.cmb_doel)
        rij.addStretch(1)
        lay.addLayout(rij)
        # ffmpeg-status
        self.lbl_ffmpeg = QLabel(""); self.lbl_ffmpeg.setObjectName("info")
        self.lbl_ffmpeg.setWordWrap(True)
        lay.addWidget(self.lbl_ffmpeg)
        rij_ff = QHBoxLayout()
        self.btn_ff_dl = QPushButton(self.t("ffmpeg_download"))
        self.btn_ff_dl.clicked.connect(self._ffmpeg_download)
        rij_ff.addWidget(self.btn_ff_dl)
        self.btn_ff_zip = QPushButton(self.t("ffmpeg_zip"))
        self.btn_ff_zip.clicked.connect(self._ffmpeg_zip)
        rij_ff.addWidget(self.btn_ff_zip)
        rij_ff.addStretch(1)
        lay.addLayout(rij_ff)
        # bestanden
        kb = QLabel(self.t("bestanden")); kb.setObjectName("kop")
        lay.addWidget(kb)
        self.lijst = QListWidget()
        self.lijst.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        lay.addWidget(self.lijst, 1)
        self.lbl_sleep = QLabel(self.t("sleep_hier")); self.lbl_sleep.setObjectName("sleep")
        self.lbl_sleep.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.lbl_sleep)
        rij_b = QHBoxLayout()
        b_add = QPushButton(self.t("toevoegen")); b_add.setObjectName("primair")
        b_add.clicked.connect(self._toevoegen)
        rij_b.addWidget(b_add)
        b_del = QPushButton(self.t("verwijderen")); b_del.clicked.connect(self._verwijderen)
        rij_b.addWidget(b_del)
        b_wis = QPushButton(self.t("wissen")); b_wis.clicked.connect(self._wissen)
        rij_b.addWidget(b_wis)
        rij_b.addStretch(1)
        lay.addLayout(rij_b)
        # uitvoer + opties
        rij_u = QHBoxLayout()
        rij_u.addWidget(QLabel(self.t("uitvoermap")))
        self.veld_uit = QLineEdit(self.cfg.get("uitvoermap", ""))
        self.veld_uit.setPlaceholderText(self.t("uitvoermap_naast"))
        rij_u.addWidget(self.veld_uit, 1)
        b_kies = QPushButton(self.t("uitvoermap_kies")); b_kies.clicked.connect(self._kies_uit)
        rij_u.addWidget(b_kies)
        b_open = QPushButton(self.t("open_map")); b_open.clicked.connect(self._open_uit)
        rij_u.addWidget(b_open)
        lay.addLayout(rij_u)
        self.rij_afb = QHBoxLayout()
        self.rij_afb.addWidget(QLabel(self.t("kwaliteit")))
        self.sld_kwal = QSlider(Qt.Orientation.Horizontal)
        self.sld_kwal.setRange(40, 100); self.sld_kwal.setValue(int(self.cfg.get("afb_kwaliteit", 90)))
        self.sld_kwal.setMaximumWidth(160)
        self.lbl_kwal = QLabel(str(self.sld_kwal.value()))
        self.sld_kwal.valueChanged.connect(lambda x: self.lbl_kwal.setText(str(x)))
        self.rij_afb.addWidget(self.sld_kwal); self.rij_afb.addWidget(self.lbl_kwal)
        self.rij_afb.addSpacing(16)
        self.rij_afb.addWidget(QLabel(self.t("maxbreedte")))
        self.spin_breedte = QSpinBox(); self.spin_breedte.setRange(0, 10000)
        self.spin_breedte.setSingleStep(50); self.spin_breedte.setValue(int(self.cfg.get("afb_maxbreedte", 0)))
        self.rij_afb.addWidget(self.spin_breedte)
        self.rij_afb.addStretch(1)
        self.afb_widget = QWidget(); self.afb_widget.setLayout(self.rij_afb)
        lay.addWidget(self.afb_widget)
        # converteren
        rij_c = QHBoxLayout()
        self.btn_go = QPushButton(self.t("converteren")); self.btn_go.setObjectName("primair")
        self.btn_go.clicked.connect(self._start)
        rij_c.addWidget(self.btn_go)
        self.btn_stop = QPushButton(self.t("stoppen")); self.btn_stop.setObjectName("stop")
        self.btn_stop.clicked.connect(self._stop); self.btn_stop.setEnabled(False)
        rij_c.addWidget(self.btn_stop)
        rij_c.addStretch(1)
        lay.addLayout(rij_c)
        self.balk = QProgressBar(); self.balk.setVisible(False)
        lay.addWidget(self.balk)
        self.lbl_status = QLabel(""); self.lbl_status.setObjectName("uitleg")
        lay.addWidget(self.lbl_status)
        # statusbalk met donatie
        sb = QStatusBar(); self.setStatusBar(sb)
        bd = QPushButton(" \u2665 " + self.t("donatie")); bd.setObjectName("primair")
        bd.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(DONATIE_URL)))
        sb.addPermanentWidget(bd)

    # ---- categorie / formaat ----
    def _cat(self):
        return self.cmb_cat.currentData()

    def _cat_gewijzigd(self):
        cat = self._cat()
        self.cmb_doel.blockSignals(True); self.cmb_doel.clear()
        for ext in DOELFORMATEN[cat]:
            self.cmb_doel.addItem(ext.upper(), ext)
        self.cmb_doel.blockSignals(False)
        if hasattr(self, "afb_widget"):
            self.afb_widget.setVisible(cat == "afbeelding")
        self._ffmpeg_ververs()

    # ---- ffmpeg ----
    def _ffmpeg_ververs(self):
        self.ffmpeg = vind_ffmpeg()
        nodig = self._cat() in ("audio", "video")
        if self.ffmpeg:
            self.lbl_ffmpeg.setText(self.t("ffmpeg_aanwezig").format(pad=self.ffmpeg))
        else:
            self.lbl_ffmpeg.setText(self.t("ffmpeg_mist"))
        # rij alleen tonen als relevant of ontbrekend
        toon = nodig and not self.ffmpeg
        self.lbl_ffmpeg.setVisible(nodig or not self.ffmpeg)
        self.btn_ff_dl.setVisible(toon or (nodig and not self.ffmpeg))
        self.btn_ff_zip.setVisible(toon or (nodig and not self.ffmpeg))
        if not nodig and self.ffmpeg:
            self.lbl_ffmpeg.setVisible(False)
            self.btn_ff_dl.setVisible(False); self.btn_ff_zip.setVisible(False)

    def _ffmpeg_download(self):
        self.btn_ff_dl.setEnabled(False); self.btn_ff_zip.setEnabled(False)
        self.balk.setVisible(True); self.balk.setRange(0, 0)
        self.lbl_status.setText(self.t("ffmpeg_bezig").format(mb="?"))
        zip_pad = os.path.join(DATA_MAP, "ffmpeg-download.zip")
        self._dl = DownloadThread(FFMPEG_URL, zip_pad, FFMPEG_MAP)
        self._dl.voortgang.connect(self._dl_voortgang)
        self._dl.klaar.connect(self._dl_klaar)
        self._dl.start()

    def _ffmpeg_zip(self):
        p, _ = QFileDialog.getOpenFileName(self, self.t("ffmpeg_zip"), BASIS, "Zip (*.zip)")
        if not p:
            return
        ok, fout = pak_uit(p, FFMPEG_MAP)
        if not ok:
            QMessageBox.warning(self, APP_NAAM, self.t("ffmpeg_mislukt").format(fout=fout))
            return
        self._ffmpeg_ververs()
        if self.ffmpeg:
            QMessageBox.information(self, APP_NAAM, self.t("ffmpeg_klaar"))

    def _dl_voortgang(self, gedaan, totaal):
        if totaal > 0:
            self.balk.setRange(0, 100); self.balk.setValue(int(gedaan * 100 / totaal))
            mb = "%.0f / %.0f MB" % (gedaan / 1048576.0, totaal / 1048576.0)
        else:
            mb = "%.0f MB" % (gedaan / 1048576.0)
        self.lbl_status.setText(self.t("ffmpeg_bezig").format(mb=mb))

    def _dl_klaar(self, ok, fout):
        self.balk.setVisible(False); self.balk.setRange(0, 100)
        self.btn_ff_dl.setEnabled(True); self.btn_ff_zip.setEnabled(True)
        self.lbl_status.setText("")
        if not ok:
            QMessageBox.warning(self, APP_NAAM, self.t("ffmpeg_mislukt").format(fout=fout))
            return
        self._ffmpeg_ververs()
        if self.ffmpeg:
            QMessageBox.information(self, APP_NAAM, self.t("ffmpeg_klaar"))

    # ---- bestanden ----
    def _toevoegen(self):
        cat = self._cat()
        exts = " ".join("*." + e for e in sorted(INVOER_EXT[cat]))
        paden, _ = QFileDialog.getOpenFileNames(
            self, self.t("toevoegen"), BASIS,
            "%s (%s);;%s (*.*)" % (self.t("cat_" + cat), exts, self.t("bestanden")))
        for p in paden:
            self._voeg_toe(p)

    def _voeg_toe(self, pad):
        if not os.path.isfile(pad):
            return
        for i in range(self.lijst.count()):
            if self.lijst.item(i).data(Qt.ItemDataRole.UserRole) == pad:
                return
        it = QListWidgetItem(os.path.basename(pad))
        it.setData(Qt.ItemDataRole.UserRole, pad)
        it.setToolTip(pad)
        self.lijst.addItem(it)
        self.lbl_sleep.setVisible(self.lijst.count() == 0)

    def _verwijderen(self):
        for it in self.lijst.selectedItems():
            self.lijst.takeItem(self.lijst.row(it))
        self.lbl_sleep.setVisible(self.lijst.count() == 0)

    def _wissen(self):
        self.lijst.clear()
        self.lbl_sleep.setVisible(True)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        for url in e.mimeData().urls():
            p = url.toLocalFile()
            if p and os.path.isfile(p):
                self._voeg_toe(p)

    # ---- uitvoermap ----
    def _kies_uit(self):
        d = QFileDialog.getExistingDirectory(self, self.t("uitvoermap"),
                                             self.veld_uit.text() or BASIS)
        if d:
            self.veld_uit.setText(d)

    def _open_uit(self):
        d = self.veld_uit.text().strip()
        if not d or not os.path.isdir(d):
            d = BASIS
        QDesktopServices.openUrl(QUrl.fromLocalFile(d))

    # ---- converteren ----
    def _doelpad(self, src, ext, uitmap):
        stam = os.path.splitext(os.path.basename(src))[0]
        mapnaam = uitmap if uitmap else os.path.dirname(src)
        dst = os.path.join(mapnaam, stam + "." + ext)
        if os.path.abspath(dst) == os.path.abspath(src):
            dst = os.path.join(mapnaam, stam + "_omgezet." + ext)
        if not self.cfg.get("overschrijven", False):
            n = 1; basis_dst = dst
            while os.path.exists(dst):
                root, e = os.path.splitext(basis_dst)
                dst = "%s (%d)%s" % (root, n, e); n += 1
        return dst

    def _start(self):
        n = self.lijst.count()
        if n == 0:
            QMessageBox.information(self, APP_NAAM, self.t("geen_bestanden"))
            return
        cat = self._cat(); ext = self.cmb_doel.currentData()
        if cat in ("audio", "video") and not self.ffmpeg:
            QMessageBox.warning(self, APP_NAAM, self.t("ffmpeg_nodig"))
            return
        # instellingen bewaren
        self.cfg["uitvoermap"] = self.veld_uit.text().strip()
        self.cfg["afb_kwaliteit"] = self.sld_kwal.value()
        self.cfg["afb_maxbreedte"] = self.spin_breedte.value()
        bewaar_config(self.cfg)
        uitmap = self.veld_uit.text().strip()
        kwal = self.sld_kwal.value(); maxb = self.spin_breedte.value()
        taken = []
        for i in range(n):
            src = self.lijst.item(i).data(Qt.ItemDataRole.UserRole)
            dst = self._doelpad(src, ext, uitmap)
            taken.append((src, dst, cat, ext, kwal, maxb))
        self.btn_go.setEnabled(False); self.btn_stop.setEnabled(True)
        self.balk.setVisible(True); self.balk.setRange(0, n); self.balk.setValue(0)
        self._thread = ConversieThread(taken, self.ffmpeg)
        self._thread.voortgang.connect(self._c_voortgang)
        self._thread.resultaat.connect(self._c_resultaat)
        self._thread.klaar.connect(self._c_klaar)
        self._thread.start()

    def _stop(self):
        if self._thread:
            self._thread.stop()
        self.btn_stop.setEnabled(False)

    def _c_voortgang(self, i, n, naam):
        self.balk.setValue(i)
        self.lbl_status.setText(self.t("bezig").format(i=i, n=n, naam=naam))

    def _c_resultaat(self, naam, ok, fout):
        if not ok:
            print("Conversie mislukt:", naam, fout)

    def _c_klaar(self, ok, fout):
        self.btn_go.setEnabled(True); self.btn_stop.setEnabled(False)
        self.balk.setVisible(False)
        self.lbl_status.setText(self.t("klaar_n").format(ok=ok, fout=fout))
        self._thread = None

    def _instellingen(self):
        if InstellingenDialoog(self).exec():
            nieuw = self._taal()
            if nieuw != self.taal:
                QMessageBox.information(self, APP_NAAM,
                    "Herstart DraveConvert om de taal toe te passen."
                    if self.taal == "nl" else
                    "Restart DraveConvert to apply the language.")

    def closeEvent(self, e):
        if self._thread and self._thread.isRunning():
            self._thread.stop(); self._thread.wait(3000)
        super().closeEvent(e)


def main():
    if WINDOWS:
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "Dravenlock.DraveConvert")
        except Exception:
            pass
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAAM)
    app.setWindowIcon(app_icoon())
    v = Hoofdvenster()
    v.show()
    try:  # Dravenlock: stille update-check (uit te zetten; Ctrl+Shift+U = met de hand)
        import drave_update
        drave_update.start(v, 'DraveConvert', APP_VERSIE)
    except Exception:
        pass
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
