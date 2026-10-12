# Konfiguration und Betrieb

## Voraussetzungen

- Home Assistant OS mit Apps/Add-ons.
- Eine feste IPv4-Adresse für Scanner und Home Assistant.
- Ein Brevo-Konto mit freigegebener Absenderadresse und SMTP-Schlüssel.
- Netzwerkzugriff vom Scanner auf Home Assistant, TCP 2525.
- DNS und ausgehendes TCP 587 von Home Assistant zu Brevo.

## Brevo-Zugangsdaten abrufen

Öffne nach der Anmeldung bei Brevo **Einstellungen → SMTP & API → SMTP**:

[https://app.brevo.com/settings/keys/smtp](https://app.brevo.com/settings/keys/smtp)

Auf dieser Seite werden unter **Deine SMTP-Einstellungen** Server, Port und **Anmeldung** angezeigt. Außerdem lassen sich dort SMTP-Schlüssel erstellen und verwalten.

| Angabe bei Brevo | Feld im Add-on |
|---|---|
| SMTP-Server | `relay_host` – üblicherweise `smtp-relay.brevo.com` |
| Port | `relay_port` – für dieses Add-on `587` |
| Anmeldung | `relay_username` – exakt den angezeigten Login übernehmen |
| Vollständiger Wert eines aktiven SMTP-Schlüssels | `relay_password` |

Für den Scanner kann ein eigener SMTP-Schlüssel mit einem erkennbaren Namen angelegt werden. Den vollständigen Schlüssel sicher speichern und im Add-on eintragen; die maskierte Anzeige bzw. nur die sichtbaren letzten Zeichen reichen nicht aus. Ein API-Schlüssel oder das Brevo-Kontopasswort ist kein Ersatz für den SMTP-Schlüssel.

Die Anmeldung ist unabhängig von der sichtbaren Absenderadresse. Für `sender_address` eine bei Brevo freigegebene Absenderadresse verwenden.

## Einstellungen

| Feld | Bedeutung |
|---|---|
| `allowed_client` | Einzige zugelassene Scanner-IPv4-Adresse, ohne Netzmaske. |
| `relay_host` | SMTP-Server, standardmäßig `smtp-relay.brevo.com`. |
| `relay_port` | SMTP-Port mit STARTTLS, bei Brevo `587`. Port 465 mit implizitem TLS ist nicht implementiert. |
| `relay_username` | SMTP-Login aus dem Brevo-Konto. |
| `relay_password` | Brevo-SMTP-Schlüssel, nicht API-Schlüssel oder Kontopasswort. |
| `sender_address` | Erlaubte SMTP-Absenderadresse, die auch am Scanner und bei Brevo eingerichtet sein muss. |
| `sender_name` | Optionaler sichtbarer Absendername, maximal 200 Zeichen. |

Nach jeder Änderung **speichern und das Add-on neu starten**. Der SMTP-Port auf dem Home-Assistant-Gerät ist unter **Netzwerk** konfigurierbar; standardmäßig wird Container-Port 2525 als Host-Port 2525 bereitgestellt.

## Absendername

Beispiel:

```yaml
sender_address: scanner@example.com
sender_name: Dokumentenscanner Büro
```

Empfänger sehen anschließend:

```text
Dokumentenscanner Büro <scanner@example.com>
```

Der Name wird als MIME-kodierter Anzeigename im ausgehenden `From`-Header eingesetzt. Umlaute, Anführungszeichen und andere Sonderzeichen werden kodiert. Steuerzeichen werden abgelehnt. Ein leeres Feld deaktiviert die Umschreibung und erhält den ursprünglichen `From`-Header des Scanners.

Die SMTP-Absenderadresse bleibt unverändert. Für eine neue Adresse sowohl `sender_address` im Add-on als auch die Geräte-E-Mail-Adresse am Scanner ändern und die Adresse bei Brevo freigeben. Eine Änderung des Anzeigenamens allein erfordert keine Änderung am Scanner.

Die Umschreibung findet beim SMTP-Versand statt. Daher erhalten auch noch wartende Nachrichten den dann aktuellen Anzeigenamen. Das Umschreiben eines bereits DKIM-signierten `From`-Headers kann eine vorhandene Signatur ungültig machen; vorgesehen ist das Add-on für nicht vorsignierte Scanner-E-Mails.

## Netzwerk und VLANs

Der Scanner muss die direkte Home-Assistant-IP auf TCP 2525 erreichen können. Bei getrennten VLANs eine gezielte Freigabe **Scanner-IP → Home-Assistant-IP, TCP-Zielport 2525** vor einer gegebenenfalls passenden Sperrregel anlegen. Keine Portweiterleitung aus dem Internet einrichten.

Die Freigabe im Add-on prüft die Quell-IP. Der Netzwerkweg muss die ursprüngliche Scanner-IP erhalten. Ein Proxy oder Source-NAT zwischen Scanner und Relay führt sonst zu einer Ablehnung. Weitere Geräte bleiben abgewiesen, auch wenn sie den Port erreichen können.

Home Assistant benötigt DNS-Zugriff und Zugriff auf den Brevo-Server auf TCP 587. Der Scanner selbst benötigt für diesen Versandweg keinen Zugang zu Brevo. Für die lokale SMTP-Verbindung ist keine Auflösung einer Home-Assistant-Webdomain notwendig.

## Versand überprüfen

1. Am Scanner die SMTP-Konfiguration testen.
2. Im Add-on unter **Protokoll** nach der Nachricht suchen.
3. `Verified TLS connection established` bestätigt den geprüften TLS-Verbindungsaufbau.
4. `status=sent` mit SMTP-Antwort `250` bestätigt die Annahme durch Brevo.
5. Den tatsächlichen Eingang beim Empfänger prüfen, gegebenenfalls auch im Spamordner oder in den Brevo-Transaktionsprotokollen.

Eine Erfolgsmeldung am Scanner bestätigt zunächst nur die Annahme durch das lokale Relay. Sie beweist noch nicht die spätere Zustellung.

## Warteschlange und Neustarts

Postfix speichert wartende Nachrichten im persistenten Add-on-Datenverzeichnis `/data/spool`. Bei vorübergehenden Fehlern werden sie erneut versucht; beim Start wird die Warteschlange zur erneuten Zustellung angestoßen. Dauerhafte Fehler können zu einer Unzustellbarkeitsnachricht führen, statt unbegrenzt erneut versucht zu werden.

**Beim Booten starten** aktivieren. Add-on-Daten vor einer Deinstallation sichern: Eine Deinstallation kann Warteschlange und Konfiguration löschen. Home-Assistant-Backups mit Add-on-Daten enthalten auch Zugangsdaten und Nachrichten; entsprechend geschützt aufbewahren.

## Fehlersuche

| Meldung oder Symptom | Prüfen |
|---|---|
| `Client host rejected: Access denied` | `allowed_client`, aktuelle Scanner-IP und gegebenenfalls Source-NAT. |
| Absender wird abgewiesen | Geräte-E-Mail-Adresse muss mit `sender_address` übereinstimmen. |
| `Please enter the Brevo SMTP key` | `relay_password` ausfüllen und neu starten. |
| `SASL authentication failed` | SMTP-Login und aktiven SMTP-Schlüssel in Brevo prüfen. |
| `status=deferred` | Die Erklärung dahinter lesen: DNS, Netzwerk, TLS oder temporärer Anbieterfehler. |
| TLS-/Zertifikatsfehler | Gerätezeit von Home Assistant, DNS und Netzwerkfilter prüfen; Zertifikatsprüfung bleibt zwingend aktiviert. |
| Scanner kann das Relay nicht erreichen | Direkte HA-IP, Portzuordnung, VLAN-Regeln und Add-on-Status prüfen. |
| Konfiguration gültig, Mail fehlt | Relay-Protokoll, Brevo-Protokoll und Spamordner prüfen. |
| Anlage zu groß | 25 MiB gelten für die gesamte kodierte Nachricht. Base64 vergrößert Anlagen ungefähr um ein Drittel; Brevo kann zusätzliche Grenzen haben. |
