# Brother SMTP Relay for Home Assistant

Ein Home-Assistant-Add-on, das E-Mails von einem lokalen Scanner annimmt und über Brevo mit geprüfter TLS-Verbindung versendet. Der sichtbare Absendername ist frei konfigurierbar.

Entstanden für einen Brother ADS-2800W, dessen TLS-Verbindungsaufbau direkt mit Brevo scheiterte. Der Scanner verbindet sich stattdessen mit dem lokalen Relay; Postfix übernimmt die moderne TLS-Verbindung zum SMTP-Anbieter.

```text
Brother-Scanner ── SMTP, Port 2525 ──> Home Assistant
                                       │
                                       └── STARTTLS + SMTP-AUTH, Port 587 ──> Brevo ──> Empfänger
```

> Der Abschnitt Scanner → Relay ist unverschlüsselt und ohne Anmeldung. Das Add-on lässt ausschließlich die konfigurierte Scanner-IP und Absenderadresse zu. Nur in einem vertrauenswürdigen lokalen Netzwerk betreiben und Port 2525 nicht ins Internet freigeben.

## Installation

Home Assistant OS mit Apps/Add-ons wird benötigt.

1. **Einstellungen → Apps/Add-ons → Store → ⋮ → Repositories** öffnen.
2. Dieses Repository hinzufügen:

   ```text
   https://github.com/stefan-f-punkt/home-assistant-brother-smtp-relay
   ```

3. **Brother SMTP Relay** installieren. Das Container-Image wird auf dem Home-Assistant-Gerät gebaut; Internetzugriff auf die Container- und Paketquellen ist erforderlich.
4. Unter **Konfiguration** Scanner-IP, Brevo-Zugangsdaten und Absenderadresse eintragen.
5. Speichern und starten. **Beim Booten starten** aktivieren bzw. aktiviert lassen.

Das Repository kann unabhängig davon zunächst geklont und als lokales Add-on installiert werden. Es werden keine vorgebauten Container-Images veröffentlicht.

## Beispielkonfiguration

Alle Adressen und Zugangsdaten in diesem Beispiel sind Platzhalter:

```yaml
allowed_client: 192.0.2.10
relay_host: smtp-relay.brevo.com
relay_port: 587
relay_username: DEIN_BREVO_SMTP_LOGIN
relay_password: DEIN_BREVO_SMTP_SCHLUESSEL
sender_address: scanner@example.com
sender_name: Dokumentenscanner
```

Die Zugangsdaten findest du nach der Anmeldung unter **Einstellungen → SMTP & API → SMTP** auf der [Brevo-Seite für SMTP-Einstellungen und SMTP-Schlüssel](https://app.brevo.com/settings/keys/smtp). Dort kannst du SMTP-Schlüssel erstellen und verwalten. Den dort angezeigten Wert **Anmeldung** als `relay_username` und den vollständigen SMTP-Schlüssel als `relay_password` eintragen.

Den **SMTP-Login aus Brevo** und einen **SMTP-Schlüssel** verwenden. Der Login kann von der sichtbaren Absenderadresse abweichen. Die Absenderadresse muss bei Brevo freigegeben sein. SMTP-Schlüssel weder in Issues noch in Git veröffentlichen.

## Scanner konfigurieren

| Einstellung | Wert |
|---|---|
| SMTP-Server | Direkte lokale IP-Adresse des Home-Assistant-Geräts |
| Port | `2525` |
| Serverauthentifizierung | Keine |
| SSL/TLS | Keine |
| Geräte-E-Mail-Adresse | Derselbe Wert wie `sender_address` |

Für Home Assistant und Scanner feste DHCP-Zuordnungen verwenden. Ein HTTPS-Reverse-Proxy oder die Webadresse von Home Assistant ist kein SMTP-Endpunkt.

## Dokumentation

- [Konfiguration, Absendername, Netzwerk und Fehlersuche](brother_smtp_relay/DOCS.md)
- [Versionshistorie](brother_smtp_relay/CHANGELOG.md)
- [Sicherheitsmodell und Meldung von Problemen](SECURITY.md)
- [Entwicklung und Tests](CONTRIBUTING.md)

## Funktionsumfang und Grenzen

- Ein zugelassener Scanner und eine zugelassene SMTP-Absenderadresse.
- Sichtbarer Absendername mit Umlauten und Sonderzeichen; leer bedeutet keine Umschreibung.
- Brevo-Anmeldung und zwingend geprüfte TLS-Verbindung, mindestens TLS 1.2.
- Persistente Warteschlange für vorübergehend nicht zustellbare Nachrichten.
- Maximale SMTP-Nachrichtengröße: 25 MiB einschließlich MIME/Base64-Kodierung.
- `amd64` und `aarch64` sind im Add-on deklariert. Der praktische Betrieb wurde mit einem ADS-2800W auf `amd64` bestätigt; `aarch64` wurde nicht am Gerät geprüft.
- Andere SMTP-Anbieter mit STARTTLS können funktionieren, sind nicht praktisch validiert. Implizites TLS auf Port 465 wird vom Relay derzeit nicht unterstützt.

Dies ist ein unabhängiges Community-Projekt, kein offizielles Add-on von Brother, Brevo oder Home Assistant.

## Lizenz

[MIT](LICENSE). Die Lizenz gilt für den Code in diesem Repository. Postfix, Alpine Linux und weitere im Container installierte Pakete unterliegen ihren jeweiligen Lizenzen.
