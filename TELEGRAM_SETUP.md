# Telegram Bot Setup für K-Lab Mitgliederverwaltung

## 1. Telegram Bot erstellen

1. Öffnen Sie Telegram und suchen Sie nach `@BotFather`
2. Starten Sie eine Unterhaltung mit `/start`
3. Erstellen Sie einen neuen Bot mit `/newbot`
4. Folgen Sie den Anweisungen und wählen Sie einen Namen und Benutzernamen
5. **Wichtig**: Speichern Sie den Bot-Token, den Sie erhalten

## 2. Chat-ID ermitteln

### Methode 1: Über @userinfobot
1. Suchen Sie nach `@userinfobot` in Telegram
2. Starten Sie eine Unterhaltung und senden Sie `/start`
3. Der Bot zeigt Ihnen Ihre Chat-ID an

### Methode 2: Über Ihren eigenen Bot
1. Senden Sie eine Nachricht an Ihren erstellten Bot
2. Besuchen Sie: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Suchen Sie nach `"chat":{"id":` - die Zahl danach ist Ihre Chat-ID

## 3. Umgebungsvariablen setzen

### Windows (PowerShell):
```powershell
$env:TELEGRAM_BOT_TOKEN="ihr_bot_token_hier"
$env:TELEGRAM_CHAT_ID="ihre_chat_id_hier"
```

### Windows (CMD):
```cmd
set TELEGRAM_BOT_TOKEN=ihr_bot_token_hier
set TELEGRAM_CHAT_ID=ihre_chat_id_hier
```

### Linux/Mac:
```bash
export TELEGRAM_BOT_TOKEN="ihr_bot_token_hier"
export TELEGRAM_CHAT_ID="ihre_chat_id_hier"
```

## 4. Telefonnummern zuordnen

Bearbeiten Sie die Datei `telegram_config.py` und fügen Sie die Zuordnungen hinzu:

```python
PHONE_TO_TELEGRAM_MAPPING: Dict[str, str] = {
    "+491234567890": "123456789",  # Max Mustermann
    "+499876543210": "987654321",  # Erika Beispiel
    # ... weitere Mitglieder
}
```

## 5. Abhängigkeiten installieren

```bash
uv sync
```

## 6. Anwendung starten

```bash
streamlit run member_management.py
```

## Funktionen

- **Automatische Zahlungserinnerungen**: Sendet personalisierte Nachrichten an Mitglieder mit ausstehenden Beiträgen
- **Mitgliedsform-basierte Berechnung**: 
  - Aktiv: 50 CHF/Monat
  - Passiv: 25 CHF/Monat
  - Inaktiv: Keine Erinnerungen
- **Detaillierte Nachrichten**: Zeigt ausstehende Monate und Gesamtbetrag an
- **Versand-Status**: Zeigt Erfolg/Fehler für jeden Versand an

## Fehlerbehebung

1. **"Telegram Bot nicht konfiguriert"**: Überprüfen Sie die Umgebungsvariablen
2. **"No Telegram chat ID found"**: Überprüfen Sie die Telefonnummer-Zuordnung in `telegram_config.py`
3. **Versand-Fehler**: Überprüfen Sie die Logs in `member_management.log`
