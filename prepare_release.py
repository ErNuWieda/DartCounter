# Dartcounter Deluxe
# Copyright (C) 2025 Martin Hehl (airnooweeda)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import sys
import re
from datetime import date
import pathlib

# Definiert die Dateipfade relativ zum Skript-Speicherort
SCRIPT_DIR = pathlib.Path(__file__).parent
VERSION_FILE = SCRIPT_DIR / "core" / "_version.py"
CHANGELOG_FILE = SCRIPT_DIR / "CHANGELOG.md"
RELEASE_CHECKLIST_FILE = SCRIPT_DIR / "RELEASE_CHECKLIST.md"
BUILD_FILE = SCRIPT_DIR / "build.py"
ISS_FILE = SCRIPT_DIR / "installer" / "create_installer.iss"


def update_version_file(new_version: str):
    """Aktualisiert den __version__-String in core/_version.py."""
    print(f"Aktualisiere {VERSION_FILE} auf Version {new_version}...")
    try:
        content = VERSION_FILE.read_text(encoding="utf-8")
        
        current_version_match = re.search(r"__version__\s*=\s*[\"'](.*?)[\"']", content)
        current_version = current_version_match.group(1) if current_version_match else None

        if current_version == new_version:
            print(f"  -> Info: Version in {VERSION_FILE} ist bereits {new_version}. Keine Änderung nötig.")
            return

        # Nutzt Regex, um den Versions-String zu finden und zu ersetzen
        new_content = re.sub(
            r"__version__\s*=\s*[\"'].*?[\"']",
            f'__version__ = "{new_version}"',
            content,
        )
        if new_content == content:
            print(f"  -> FEHLER: Versions-String in {VERSION_FILE} nicht gefunden oder konnte nicht ersetzt werden. Datei wurde nicht geändert.")
            sys.exit(1)

        VERSION_FILE.write_text(new_content, encoding="utf-8")
        print(f"  -> Erfolg: {VERSION_FILE} wurde aktualisiert.")
    except FileNotFoundError:
        print(f"  -> FEHLER: {VERSION_FILE} nicht gefunden.")
        sys.exit(1)


def update_changelog(new_version: str):
    """Aktualisiert CHANGELOG.md mit der neuen Version und einem frischen [Unreleased]-Abschnitt."""
    print(f"Aktualisiere {CHANGELOG_FILE} für Version {new_version}...")
    try:
        content = CHANGELOG_FILE.read_text(encoding="utf-8")
        today = date.today().isoformat()

        # Der neue Header für die gerade veröffentlichte Version
        new_version_header = f"## [{new_version}] - {today}"

        # Die neue Vorlage für zukünftige Änderungen
        unreleased_template = """## [Unreleased]

### ✨ Features & Verbesserungen

### 🐛 Bugfixes & Stabilität

---

"""
        # Prüfen, ob der [Unreleased]-Abschnitt existiert
        if "## [Unreleased]" not in content:
            print(f"  -> FEHLER: Abschnitt '## [Unreleased]' in {CHANGELOG_FILE} nicht gefunden.")
            sys.exit(1)

        # Ersetzt den bestehenden [Unreleased]-Header durch die neue Vorlage und den neuen Versions-Header
        new_content = content.replace(
            "## [Unreleased]",
            unreleased_template + new_version_header,
            1,  # Nur das erste Vorkommen ersetzen
        )

        CHANGELOG_FILE.write_text(new_content, encoding="utf-8")
        print(f"  -> Erfolg: {CHANGELOG_FILE} wurde aktualisiert.")
    except FileNotFoundError:
        print(f"  -> FEHLER: {CHANGELOG_FILE} nicht gefunden.")
        sys.exit(1)


def update_release_checklist(new_version: str):
    """Aktualisiert die Platzhalter in RELEASE_CHECKLIST.md mit der neuen Version."""
    print(f"Aktualisiere {RELEASE_CHECKLIST_FILE} für Version {new_version}...")
    try:
        content = RELEASE_CHECKLIST_FILE.read_text(encoding="utf-8")

        # Ersetze die Platzhalter. Wir ersetzen zuerst den spezifischeren 'vX.Y.Z',
        # dann den allgemeineren 'X.Y.Z', um korrekte Ersetzungen sicherzustellen.
        new_content = content.replace("vX.Y.Z", f"v{new_version}")
        new_content = new_content.replace("X.Y.Z", new_version)

        if new_content == content:  # pragma: no cover
            msg = f"  -> WARNUNG: Keine Platzhalter in {RELEASE_CHECKLIST_FILE} gefunden. Datei wurde nicht geändert."
            print(msg)
            return

        RELEASE_CHECKLIST_FILE.write_text(new_content, encoding="utf-8")
        print(f"  -> Erfolg: {RELEASE_CHECKLIST_FILE} wurde aktualisiert.")

    except FileNotFoundError:
        print(f"  -> FEHLER: {RELEASE_CHECKLIST_FILE} nicht gefunden.")
        # Wir brechen hier nicht ab, da die Checkliste optional sein könnte.
        # Ein Fehler in der Versions- oder Changelog-Datei ist kritischer.


def update_build_file():
    """Stellt sicher, dass build.py die Version dynamisch aus _version.py liest."""
    print(f"Überprüfe {BUILD_FILE} auf dynamische Versionierung...")
    if not BUILD_FILE.exists():
        print(f"  -> Hinweis: {BUILD_FILE} nicht gefunden. Überspringe.")
        return
    try:
        content = BUILD_FILE.read_text(encoding="utf-8")
        
        # 1. Sicherstellen, dass der Import von __version__ vorhanden ist
        import_line = "from core._version import __version__"
        if import_line not in content:
            # Fügt den Import am Anfang nach dem Header-Kommentar ein
            content = re.sub(r"^(#.*?\n)*", rf"\g<0>{import_line}\n", content, count=1)
        
        # 2. Ersetze harte Zuweisung VERSION = "1.x.x" durch VERSION = __version__
        new_content = re.sub(
            r'VERSION\s*=\s*["\'][0-9.]+["\']',
            'VERSION = __version__',
            content
        )
        
        if new_content != content:
            BUILD_FILE.write_text(new_content, encoding="utf-8")
            print(f"  -> Erfolg: {BUILD_FILE} wurde auf dynamische Versionierung umgestellt.")
    except Exception as e:
        print(f"  -> FEHLER: Konnte {BUILD_FILE} nicht aktualisieren: {e}")


def update_iss_file(new_version: str):
    """Aktualisiert die AppVersion in der Inno Setup Datei (.iss)."""
    print(f"Aktualisiere {ISS_FILE} für Version {new_version}...")
    if not ISS_FILE.exists():
        return
    try:
        content = ISS_FILE.read_text(encoding="utf-8")
        new_content = re.sub(
            r'(#define AppVersion\s*")([0-9.]+)"',
            rf'\1{new_version}"',
            content
        )
        if new_content != content:
            ISS_FILE.write_text(new_content, encoding="utf-8")
            print(f"  -> Erfolg: {ISS_FILE} wurde aktualisiert.")
    except Exception as e:
        print(f"  -> FEHLER: Konnte {ISS_FILE} nicht aktualisieren: {e}")


def main():
    """Hauptfunktion zur Orchestrierung des Versionssprungs."""
    if len(sys.argv) != 2 or not re.match(r"^\d+\.\d+\.\d+$", sys.argv[1]):
        print("Verwendung: python3 prepare_release.py <version>")
        print("Beispiel:  python3 prepare_release.py 1.3.0")
        sys.exit(1)

    new_version = sys.argv[1]

    print(f"🚀 Bereite neues Release vor: v{new_version}\n")
    update_version_file(new_version)
    update_changelog(new_version)
    update_release_checklist(new_version)
    update_build_file()
    update_iss_file(new_version)
    print("\n✅ Release-Vorbereitung abgeschlossen.")
    print("Bitte überprüfe die Änderungen in den modifizierten Dateien vor dem Commit.")


if __name__ == "__main__":
    main()
