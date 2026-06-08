# Zu Easy SCSModManager beitragen

<p align="center">
  <a href="CONTRIBUTING.md">
    <img src="https://img.shields.io/badge/🇬🇧_Read_in_English-E67E22?style=for-the-badge&labelColor=000000" alt="Read in English" height="35">
  </a>
</p>

Danke, dass du dir die Zeit nimmst zu helfen. Dieses Projekt ist ein
plattformübergreifender Mod- und Profil-Manager für Euro Truck Simulator 2 und
American Truck Simulator, in Python mit PyQt6 geschrieben. Fehlerberichte,
Übersetzungen und Pull Requests sind alle willkommen.

Mit deiner Teilnahme stimmst du unserem
[Verhaltenskodex](CODE_OF_CONDUCT_DE.md) zu.

## Einrichten

Du brauchst Python 3.13 oder neuer. Nimm den Weg, der dir lieber ist.

### Klassisches venv

```bash
git clone https://github.com/Switch-Bros/easy-scsmodmanager.git
cd easy-scsmodmanager
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### uv

[uv](https://docs.astral.sh/uv/) ist ein schneller Ersatz für pip/venv. Eine
committete `uv.lock` pinnt für jeden Mitwirkenden eine identische Umgebung.

```bash
git clone https://github.com/Switch-Bros/easy-scsmodmanager.git
cd easy-scsmodmanager
uv sync                            # erstellt .venv und installiert aus dem Lock
# oder, ohne Lock:
uv venv && uv pip install -e ".[dev]"
```

Starte die App mit `python -m easy_scsmodmanager`.

## Tests ausführen

Die Suite nutzt pytest und pytest-qt. Qt läuft headless, also setz die
Offscreen-Plattform:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest -q
```

Installier die pre-commit-Hooks einmal, damit Formatierung und Typprüfung bei
jedem Commit laufen:

```bash
pre-commit install
```

## Code-Standards

- **Formatierung und Linting:** `black`, `ruff` und `mypy` müssen alle
  durchlaufen. Die pre-commit-Hooks erzwingen das; im Zweifel
  `pre-commit run --all-files`.
- **Tests zuerst (TDD):** schreib einen fehlschlagenden Test, dann den Code, der
  ihn bestehen lässt. Neues Verhalten kommt mit Tests.
- **Internationalisierung ist Pflicht:** keine hartkodierten
  Nutzer-Texte. Jedes Label, jede Meldung und jeder Tooltip geht durch
  `t("some.key")`, der Text lebt in `easy_scsmodmanager/resources/i18n/en/main.json`
  und `de/main.json`. Beide Sprachdateien müssen dieselben Schlüssel haben.
- **Keine verstreuten Pfade:** Dateisystem-Orte der Spiele leben nur in
  `easy_scsmodmanager/core/game_paths.py`. Pfade nirgends sonst hartkodieren.
- **Dateien klein halten:** eine Datei splitten, bevor sie unhandlich wird (klar
  unter 500 Zeilen).
- Vermeide Zeichen, die auf einer normalen Tastatur umständlich sind (kein
  Geviertstrich, keine typografischen Anführungszeichen, keine schicken Pfeile)
  in Code und Texten.

## Branches und Pull Requests

1. Forke das Repository und erstell einen Topic-Branch von `main`
   (`git checkout -b fix-workshop-detection`).
2. Mach fokussierte Commits - eine logische Änderung pro Commit, klare Nachricht.
3. Sorg dafür, dass die volle Test-Suite und die pre-commit-Hooks grün sind.
4. Öffne einen Pull Request gegen `main`, der beschreibt, was sich geändert hat
   und warum. Verlink ein zugehöriges Issue.

## Übersetzungen

Eine Übersetzung hinzuzufügen oder zu aktualisieren braucht kein Programmieren.
Die volle Anleitung steht im
[Übersetzungs-Abschnitt der README](README_DE.md#-übersetzungen): kopier den
`en/`-Sprachordner, übersetz die Werte (nie die Schlüssel) und öffne einen Pull
Request.

## Fehler melden

Öffne ein [GitHub-Issue](https://github.com/Switch-Bros/easy-scsmodmanager/issues).
Nenn dein Betriebssystem, wie du die App installiert hast (AppImage, Windows-exe,
deb, rpm, AUR, tar.gz oder aus dem Quellcode) und die relevanten Zeilen aus der
Logdatei (**Werkzeuge -> Log-Ordner öffnen**).
