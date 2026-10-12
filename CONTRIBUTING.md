# Entwicklung

Das Add-on liegt im Verzeichnis `brother_smtp_relay`. Es verwendet Alpine Linux, Postfix und Python aus den Alpine-Paketquellen. Das Image wird lokal gebaut; kein Zugriff auf echte SMTP-Zugangsdaten ist für Tests erforderlich.

## Unit-Tests

```sh
python3 -m unittest discover -s tests -v
```

## Container- und Integrationstest

Auf einem Linux-Rechner mit Docker, Python 3 und OpenSSL:

```sh
docker build -t brother-smtp-relay:test brother_smtp_relay
python3 tests/integration.py
```

Der Integrationstest verwendet einen lokalen SMTP-Testserver mit selbst erzeugter CA, STARTTLS und Testzugangsdaten. Er prüft Client-IP-Beschränkung, Absenderbeschränkung, TLS-Zertifikatsprüfung, SMTP-Anmeldung, Anzeigenamen sowie unveränderte Nachricht und Anlage. Es werden keine E-Mails ins Internet gesendet. Die lokalen Ports 2525 und 2526 müssen frei sein. Der Test verwendet Docker-Host-Networking und ist für Linux vorgesehen.

GitHub Actions führt beide Prüfungen bei Pushes und Pull Requests aus. Die Architektur `aarch64` ist im Add-on deklariert, wird durch diesen Workflow aber nicht gebaut oder am Gerät validiert.

## Änderungen

Keine echten Adressen, internen Netzwerkdaten, Schlüssel, Backups oder Paketmitschnitte einchecken. Konfigurationsänderungen dokumentieren, Versionsnummer und Changelog bei Releases aktualisieren. Änderungen am SMTP-Verhalten müssen die Zugriffsbeschränkung und zwingende TLS-Prüfung erhalten.
