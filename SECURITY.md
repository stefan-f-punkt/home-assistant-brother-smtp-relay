# Sicherheitsmodell

- Der lokale SMTP-Empfang ist unverschlüsselt und ohne Anmeldung. Die Quell-IP ist die Zugangskontrolle, keine kryptografische Geräteidentität.
- Ausschließlich `allowed_client` darf SMTP-Verbindungen verwenden. Nur `sender_address` ist als SMTP-Absender zugelassen.
- Keine Freigabe von Port 2525 ins Internet. Bei VLANs ausschließlich den notwendigen Netzwerkweg freigeben.
- Der Versand zum Relayhost erfordert TLS mit Zertifikatsprüfung und mindestens TLS 1.2 sowie SMTP-Anmeldung.
- Der SMTP-Schlüssel liegt in der Home-Assistant-Add-on-Konfiguration und zur Laufzeit in einer restriktiv berechtigten Postfix-Datei. Administratoren mit Zugriff auf den Host oder unverschlüsselte Backups können ihn lesen.
- Wartende Nachrichten enthalten Dokumente und persönliche Daten. Backups und Host entsprechend schützen.
- Protokolle enthalten gegebenenfalls Absender, Empfänger, interne IPs und Zustellinformationen. Vor einer Veröffentlichung anonymisieren.
- Der konfigurierbare Anzeigename ist auf 200 Zeichen begrenzt. Steuerzeichen werden abgelehnt, damit keine zusätzlichen Header eingeschleust werden können.

## Probleme melden

Keine SMTP-Schlüssel, vollständigen Dokumente oder unbereinigten Konfigurationsdateien in öffentliche Issues stellen. Für vertrauliche Schwachstellen die private GitHub-Funktion **Report a vulnerability** verwenden, sofern sie aktiviert ist. Wenn kein privater Meldeweg angeboten wird, zunächst nur um einen vertraulichen Kontaktweg bitten und technische Details zurückhalten.
