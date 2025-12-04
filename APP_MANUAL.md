# 📖 Benutzerhandbuch: Schützenfest Kalkulator

Willkommen im Schützenfest Kalkulator. Dieses Tool unterstützt Sie bei der finanziellen Planung Ihres Festes. Es ermöglicht Ihnen, verschiedene Szenarien durchzuspielen ("Was wäre wenn wir eine teurere Band buchen?", "Was wenn am Freitag 100 Besucher weniger kommen?") und die Auswirkungen direkt zu sehen.

---

## 1. Der Kalkulator (Dashboard)

Dies ist die Startseite der Anwendung. Hier führen Sie die eigentliche Planung durch.

### 🔄 Szenario-Auswahl
In der linken Seitenleiste (Sidebar) wählen Sie unter **"Szenario wählen"** eine gespeicherte Planung aus (z.B. "Letztes Jahr" oder "Planung 2025").
*   **Tipp:** Nutzen Sie den Button `🔄 Szenarien neu laden`, wenn Sie Änderungen in den Einstellungen vorgenommen haben, diese aber noch nicht sichtbar sind.

### 🏗 Globale Bausteine
Hier definieren Sie die Rahmenbedingungen, die für das gesamte Fest gelten (nicht tagesabhängig):
*   **Zelt & Location:** Welches Zelt wird benötigt?
*   **Infrastruktur:** Toilettenwagen, Strom, Wasser.
*   **Verwaltung:** Werbung, Versicherungen, Genehmigungen.

Wählen Sie für jeden Bereich die passende Variante aus. Der Preis wird direkt angezeigt.

### 📅 Tages-Planung
Für jeden Festtag (z.B. Freitag, Samstag, Sonntag) können Sie individuelle Einstellungen vornehmen:

#### Bausteine (pro Tag)
Wählen Sie die tagesabhängigen Module:
*   **Musik:** DJ, Live-Band oder Kapelle?
*   **Sicherheit:** Wie viel Security wird benötigt?
*   **Eintritt:** Eintrittspreis festlegen (z.B. "10 € Eintritt").

#### Besucher & Konsum
Hier simulieren Sie die Einnahmen. Geben Sie an, wie viele Personen welcher **Besuchergruppe** erwartet werden:
*   **Schützen:** Trinken viel Bier.
*   **Dorfjugend:** Trinkt wenige Mixgetränke/Bier, kommt spät und glüht vor.
*   **Besucher:** Der normale Besucher, der ein paar Getränke konsumiert.
*   **Zuschauer:** Kommt nur für ein, zwei Getränke.

*Der Kalkulator berechnet automatisch den Getränkeumsatz basierend auf dem hinterlegten Konsumverhalten der Gruppen.*

### 📊 Ergebnisse & Analyse
Im Hauptbereich sehen Sie sofort die Auswirkungen Ihrer Eingaben:
*   **KPIs:** Gesamtkosten, Gesamteinnahmen, Gewinn/Verlust.
*   **Dashboard:** Grafische Gegenüberstellung von Kosten und Einnahmen pro Tag.
*   **Kosten-Details:** Detaillierte Auflistung aller Ausgabenposten.
*   **Einnahmen-Details:** Woher kommt das Geld? (Eintritt, Thekenumsatz, Sponsoring).

### 💾 Speichern
Im Reiter **"Szenario speichern"** können Sie Ihre aktuelle Planung unter einem neuen Namen sichern, um sie später wieder aufzurufen oder verschiedene Varianten zu vergleichen.

---

## 2. Einstellungen (Modul-Editor)

Über das Menü links erreichen Sie die Seite **"⚙️ Einstellungen"**. Hier pflegen Sie die "Datenbank" des Kalkulators.

### Wozu dient der Editor?
Hier definieren Sie die Preise und Varianten, die im Kalkulator zur Auswahl stehen.
*   *Beispiel:* Die GEMA-Gebühren sind gestiegen? Ändern Sie den Preis hier einmalig, und er wird in allen zukünftigen Berechnungen korrekt verwendet.

### Bedienung
1.  **Modul auswählen:** Wählen Sie oben das Modul, das Sie bearbeiten möchten (z.B. "Musik & Unterhaltung").
2.  **Variante wählen:** Wählen Sie eine bestehende Variante (z.B. "Top Live-Band") oder erstellen Sie eine neue.
3.  **Kosten bearbeiten:**
    *   In der Tabelle können Sie Positionen hinzufügen, löschen oder Preise ändern.
    *   **Fixkosten:** Einmaliger Betrag (z.B. Gage).
    *   **Pro Besucher:** Kosten steigen mit Besucherzahl (z.B. GEMA-Anteil, Eintrittsbändchen).
4.  **Einnahmen bearbeiten:**
    *   Hier definieren Sie, ob das Modul selbst Geld einbringt (z.B. Eintrittsgelder).
    *   *Hinweis:* Der Getränkeumsatz wird separat über die Besuchergruppen berechnet und muss hier nicht eingetragen werden.
5.  **Speichern:** Klicken Sie unten auf `💾 Änderungen speichern`, um die Daten in die `modules.json` zu schreiben.

---

## 3. Häufige Fragen

**Wie lege ich ein komplett neues Szenario an?**
Laden Sie ein bestehendes Szenario, passen Sie alles nach Wunsch an und speichern Sie es unter einem *neuen Namen* im Reiter "Szenario speichern".

**Woher kommen die Getränkepreise?**
Die Preise für Bier, Cola etc. sind in den Stammdaten (`master_data.json`) hinterlegt. Aktuell können diese nur direkt in der Datei bearbeitet werden.

**Was bedeutet "Pro Besucher" bei den Kosten?**
Diese Kosten fallen für jeden Gast an, den Sie im Dashboard eintragen. Beispiel: Wenn ein Eintrittsbändchen 0,30 € kostet und Sie 1000 Besucher eintragen, entstehen automatisch 300 € Kosten.
