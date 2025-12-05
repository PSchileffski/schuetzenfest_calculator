# Schützenfest Kalkulator

Der **Schützenfest Kalkulator** ist eine spezialisierte Anwendung zur finanziellen Planung und Simulation von Vereinsfesten (insb. Schützenfeste). Das System ermöglicht die detaillierte Kalkulation von Kosten und Einnahmen basierend auf konfigurierbaren Modulen, Besucherzahlen und Verzehrverhalten.

## 🏗 Architektur

Das System folgt einer klaren Trennung zwischen Daten, Logik und Präsentation:

### 1. Datenhaltung (`config/`)
Die gesamte Konfiguration basiert auf JSON-Dateien, was eine einfache Versionierung und Anpassung ermöglicht:
*   **`modules.json`**: Definiert alle verfügbaren Bausteine (Musik, Sicherheit, Zelt, etc.) mit ihren Varianten und den zugehörigen Kosten-/Einnahmen-Positionen.
*   **`master_data.json`**: Enthält Stammdaten wie Produkte (Bier, Cola, etc.) mit Einkaufs-/Verkaufspreisen sowie "Personas" (Besuchergruppen) mit definiertem Konsumverhalten.
*   **`scenarios/*.json`**: Speichert konkrete Fest-Konfigurationen (ausgewählte Module pro Tag, Besucherzahlen).

### 2. Anwendungslogik (`src/`)
*   **`models.py`**: Pydantic-Modelle garantieren Typsicherheit und Validierung der JSON-Datenstrukturen.
*   **`calculator.py`**: Die Kern-Logik. Berechnet basierend auf einem Szenario die Gesamtkosten und -einnahmen. Berücksichtigt dabei:
    *   Fixkosten (z.B. Zeltmiete)
    *   Variable Kosten (z.B. Security pro Stunde)
    *   Besucherabhängige Kosten/Einnahmen (z.B. GEMA, Eintritt)
    *   Konsumabhängige Deckungsbeiträge (Getränkeverkauf basierend auf Personas).

### 3. Frontend (Streamlit)
Die Benutzeroberfläche ist als Multi-Page Streamlit App aufgebaut:
*   **`Kalkulator.py`**: Das Haupt-Dashboard zur Auswahl von Szenarien, Anpassung von Besucherzahlen und Visualisierung der Ergebnisse.
*   **`pages/1_⚙️_Einstellungen.py`**: Ein Editor für die `modules.json`, der es ermöglicht, ohne Code-Kenntnisse Preise anzupassen oder neue Varianten zu erstellen.

## 🚀 Installation & Start

### Voraussetzungen
*   Python 3.10 oder höher

### Setup
1.  Repository klonen:
    ```bash
    git clone <repository-url>
    cd schuetzenfest-calculator
    ```

2.  Abhängigkeiten installieren:
    ```bash
    pip install -r requirements.txt
    ```

3.  Anwendung starten:
    ```bash
    streamlit run 🧮_Rechner.py
    ```

## 📂 Projektstruktur

```
.
├── 🧮_Rechner.py               # Hauptanwendung (Einstiegspunkt)
├── APP_MANUAL.md               # Benutzerhandbuch (im Frontend eingebunden)
├── config/                     # Datenverzeichnis
│   ├── master_data.json        # Produkte & Personas
│   ├── modules.json            # Modul-Definitionen
│   └── scenarios/              # Gespeicherte Szenarien
├── pages/                      # Streamlit Unterseiten
│   ├── 1_⚙️_Einstellungen.py   # Modul-Editor
│   └── 2_📖_Anleitung.py       # Anzeige des Handbuchs
└── src/                        # Source Code
    ├── calculator.py           # Berechnungslogik
    └── models.py               # Datenmodelle
```
