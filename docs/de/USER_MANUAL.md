# 📖 Easy SCSModManager - Handbuch

**Plattform:** Linux (AppImage, deb, rpm, AUR, tar.gz) und Windows (.exe)
**Spiele:** Euro Truck Simulator 2 und American Truck Simulator

---

## Inhaltsverzeichnis

1. [Was es macht](#was-es-macht)
2. [Die zwei Bereiche](#die-zwei-bereiche)
3. [Profile](#profile)
4. [Mods aktivieren und sortieren](#mods-aktivieren-und-sortieren)
5. [Load-Order-Gruppen](#load-order-gruppen)
6. [Konflikte](#konflikte)
7. [Mods löschen](#mods-löschen)
8. [Backups](#backups)
9. [Spiel wechseln](#spiel-wechseln)
10. [Einstellungen](#einstellungen)
11. [Updates](#updates)

---

## Was es macht

Easy SCSModManager liest die Mods, die du schon besitzt (lokaler `mod/`-Ordner
**und** Steam Workshop), zeigt sie mit echten Namen und Icons und lässt dich die
aktive Ladereihenfolge für ein Profil bauen - und schreibt sie dann im Klartext
direkt in die `profile.sii` des Spiels, damit das Spiel genau mit deiner
Reihenfolge startet.

Es bearbeitet nur deine eigene `profile.sii` und liest deine eigenen
installierten Mods. Es steht in keiner Verbindung zu SCS Software oder Valve.

## Die zwei Bereiche

- **Links - die Mod-Bibliothek:** jeder installierte Mod als Karte mit Icon,
  Name, Autor und Kategorie. Suchen, sortieren und filtern über die Leiste oben.
- **Rechts - die Aktiv-Liste:** die Ladereihenfolge des gewählten Profils, in
  Load-Order-Gruppen unterteilt, oben nach unten (oben = höchste Priorität).

Zieh die Trennlinie zum Anpassen. Maximierst du das Fenster, füllt das Raster
den Platz mit mehr Spalten.

## Profile

Das Profil-Dropdown im Aktiv-Listen-Kopf zeigt alle Profile des aktuellen
Spiels. Wähl eins, um seine aktiven Mods zu laden. **Speichern** schreibt deine
Änderungen zurück in die `profile.sii` - das Spiel muss dabei geschlossen sein,
sonst überschreibt es die Datei beim Beenden.

## Mods aktivieren und sortieren

- **Doppelklick** auf eine Mod-Karte aktiviert sie. Sie landet am Ende des
  Blocks ihrer eigenen Load-Order-Gruppe und wird ausgewählt.
- **Ziehen** einer Karte aus der Bibliothek in die Aktiv-Liste setzt sie an eine
  genaue Position. In einen Abschnitt gezogen, übernimmt sie auch dessen Gruppe.
- **Ziehen** von Zeilen in der Aktiv-Liste sortiert um. **Doppelklick** auf eine
  Zeile in der Aktiv-Liste entfernt sie.

## Load-Order-Gruppen

Die Aktiv-Liste ist in Gruppen unterteilt (Finanzen, Sound, Physik, Trucks,
Trailer, Maps usw.) mit Überschriften, damit ein Mod bei seinesgleichen sitzt.
Die Gruppen-Reihenfolge folgt der Lade-Reihenfolge des Spiels.

- Ein Mod in der falschen Gruppe bekommt einen **orangen linken Rand**.
  Rechtsklick, **Verschieben nach** -> eine Gruppe, um ihn dort zu pinnen, oder
  **Automatisch (eigene Kategorie)**, um ihn in seine natürliche Gruppe
  zurückzuschicken.
- **Verschieben nach** wirkt auf deine ganze Auswahl.
- Ein Mod in einen Abschnitt gezogen wird dort gepinnt; zurück in seinen
  Heimat-Abschnitt gezogen, löst sich der Pin.

## Konflikte

Zwei aktive Mods kollidieren, wenn sie dieselbe `def/`-Datei ändern - der höhere
in der Liste gewinnt. Konflikte sind ein Hinweis, kein Fehler (bei Maps ist eine
Überschneidung oft Absicht).

Ein kollidierender Mod bekommt einen Glyph vor dem Namen:

- **⚠ gelbes Dreieck - teilweise überschrieben:** einige Dateien verlieren gegen
  Mods darüber.
- **⊘ roter durchgestrichener Kreis - komplett überschrieben:** alle Dateien
  verlieren - der Mod bewirkt an seiner Stelle effektiv nichts.
- **Kein Glyph:** er gewinnt alle geteilten Dateien.

Fahr mit der Maus über den Mod für die volle Liste der überschriebenen Dateien
samt Gewinner. Eine Legende erscheint unten im Panel, solange ein Konflikt
existiert.

## Mods löschen

Rechtsklick auf einen Mod (oder mehrere auswählen, oder **Entf** drücken) und
**Löschen...** verschiebt lokale Mods in den System-Papierkorb - von dort
wiederherstellbar. Workshop-Mods bleiben bei Steam (Eintrag sichtbar, aber
deaktiviert). Nutzt ein gespeichertes Profil den Mod noch, nennt die Bestätigung
die betroffenen Profile zuerst.

Tipp: Setz den **Quelle**-Filter auf **Lokal**, drück **Strg+A**, um alle
sichtbaren Mods zu wählen, dann löschen - schnelles Aufräumen.

## Backups

Der Profil-Kopf hat **Sichern** und **Wiederherstellen**. Ein Backup ist ein Zip
des Profils, außerhalb des Spiel-Baums gespeichert, damit das Spiel es nie
anfasst. Wiederherstellen holt ein früheres Backup zurück.

## Spiel wechseln

Das **Spiel**-Menü wechselt zwischen ETS2 und ATS (nur installierte Spiele
wählbar). Deine Wahl wird für den nächsten Start gemerkt.

## Einstellungen

**Datei -> Einstellungen** umfasst die Oberflächen-Sprache, manuelle
Pfad-Overrides (falls die Auto-Erkennung einen Install verfehlt), die
Map-Basis-Begriffsliste und Verhaltens-Schalter (Klick springt zur Aktiv-Liste,
beim Start nach Updates suchen).

## Updates

**Hilfe -> Nach Updates suchen** fragt GitHub nach einer neueren Version. Die
AppImage- und Windows-Builds können ein verifiziertes Update herunterladen und
installieren; Paket-Installationen (deb/rpm/AUR/tar.gz) bekommen einen Hinweis
und aktualisieren über ihren Paketmanager.
