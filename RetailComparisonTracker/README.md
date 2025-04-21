# Discord-Bot Monitor und Webinterface

Dieses Projekt enthält einen Discord-Bot mit einer Weboberfläche zur Überwachung und Kontrolle des Bots.

## Funktionen

### Bot-Funktionen
- `!liste` - Erstellt eine Teilnehmerliste mit Namen, die durch Kommas getrennt sind
- Reaktionen (✅/❌) zum Markieren der Anwesenheit
- Hinzufügen/Entfernen von Namen durch Bearbeiten der ursprünglichen Nachricht
- Täglicher Neustart um 6:00 Uhr für eine höhere Zuverlässigkeit

### Webinterface-Funktionen
- Überwachung des Bot-Status (Online/Offline)
- Anzeige von Uptime, letztem Neustart und Serverinformationen
- Anzeige der neuesten Log-Einträge
- Manuelle Neustartmöglichkeit über eine Schaltfläche

## Verwendung

1. Erstelle eine neue Teilnehmerliste:
   ```
   !liste Felix Westfield, Mirella Sterling, John Paul Jones
   ```

2. Ändere deinen Status mit den Reaktionen ✅ oder ❌.

3. Füge neue Namen hinzu oder entferne Namen, indem du deine ursprüngliche Liste-Nachricht bearbeitest.

## Benötigte Dateien

Die Hauptdateien für dieses Projekt sind:

- `reaktions_bot_vollversion.py` - Der komplette Bot-Code mit allen Funktionen
- `standalone_monitor.py` - Eine eigenständige Flask-Anwendung zur Überwachung des Bots

Du kannst den Bot direkt mit dem folgenden Befehl starten:

```bash
python reaktions_bot_vollversion.py
```

Oder starte die Flask-Anwendung mit dem Webinterface:

```bash
python standalone_monitor.py
```

## Anpassung

1. Gib deinen Discord-Bot-Token in der `reaktions_bot_vollversion.py` Datei ein:
   ```python
   TOKEN = os.environ.get("DISCORD_TOKEN", "DEIN_TOKEN_HIER_EINFÜGEN")
   ```

2. Oder setze die Umgebungsvariable:
   ```bash
   export DISCORD_TOKEN=dein_token_hier
   ```

## Zeitpläne

- Der Bot wird automatisch jeden Tag um 6:00 Uhr neu gestartet.
- Der Bot wird automatisch neu gestartet, wenn er offline geht oder abstürzt.

---

© 2025 Discord Bot Monitor