"""Linux/Docker integration test. Uses a local TLS SMTP sink; no external mail."""
import json
import os
import queue
import smtplib
import socket
import socketserver
import ssl
import subprocess
import tempfile
import threading
import time
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from pathlib import Path

IMAGE = os.environ.get('TEST_IMAGE', 'brother-smtp-relay:test')
CONTAINER = 'brother-smtp-relay-integration'
received = queue.Queue()


def command(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


class SMTPHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.wfile.write(b'220 localhost test SMTP\r\n')
        tls = False
        authenticated = False
        while True:
            line = self.rfile.readline()
            if not line:
                return
            verb = line.split(None, 1)[0].upper()
            if verb in (b'EHLO', b'HELO'):
                if tls:
                    self.wfile.write(b'250-localhost\r\n250 AUTH PLAIN\r\n')
                else:
                    self.wfile.write(b'250-localhost\r\n250 STARTTLS\r\n')
            elif verb == b'STARTTLS':
                self.wfile.write(b'220 Start TLS\r\n')
                self.wfile.flush()
                self.connection = self.server.tls.wrap_socket(self.connection, server_side=True)
                self.rfile = self.connection.makefile('rb')
                self.wfile = self.connection.makefile('wb', buffering=0)
                tls = True
            elif verb == b'AUTH' and tls:
                import base64
                parts = line.strip().split()
                if len(parts) == 3 and base64.b64decode(parts[2]) == b'\0test-user\0test-password':
                    authenticated = True
                    self.wfile.write(b'235 Authenticated\r\n')
                else:
                    self.wfile.write(b'535 Authentication failed\r\n')
            elif verb in (b'MAIL', b'RCPT') and authenticated:
                self.wfile.write(b'250 OK\r\n')
            elif verb == b'DATA' and authenticated:
                self.wfile.write(b'354 Send message\r\n')
                chunks = []
                while True:
                    part = self.rfile.readline()
                    if part in (b'.\r\n', b''):
                        break
                    chunks.append(part[1:] if part.startswith(b'..') else part)
                received.put(b''.join(chunks))
                self.wfile.write(b'250 Accepted\r\n')
            elif verb == b'QUIT':
                self.wfile.write(b'221 Bye\r\n')
                return
            elif verb in (b'RSET', b'NOOP'):
                self.wfile.write(b'250 OK\r\n')
            else:
                self.wfile.write(b'530 Authentication required\r\n')


class SMTPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        cert, key = root / 'test.crt', root / 'test.key'
        command('openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                '-keyout', str(key), '-out', str(cert), '-days', '1',
                '-subj', '/CN=localhost', '-addext', 'subjectAltName=DNS:localhost',
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Docker must be able to traverse and read the mounted test fixtures.
        root.chmod(0o755)
        cert.chmod(0o644)
        options = root / 'options.json'
        options.write_text(json.dumps({
            'allowed_client': '127.0.0.1', 'relay_host': 'localhost', 'relay_port': 2526,
            'relay_username': 'test-user', 'relay_password': 'test-password',
            'sender_address': 'scanner@example.com', 'sender_name': 'Dokumentenscanner Büro',
        }))
        options.chmod(0o644)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert, key)
        with SMTPServer(('127.0.0.1', 2526), SMTPHandler) as server:
            server.tls = context
            threading.Thread(target=server.serve_forever, daemon=True).start()
            command('docker', 'run', '-d', '--name', CONTAINER, '--network', 'host',
                    '-v', f'{options}:/data/options.json:ro',
                    '-v', f'{cert}:/usr/local/share/ca-certificates/integration.crt:ro',
                    '--entrypoint', '/bin/sh', IMAGE, '-c',
                    'update-ca-certificates && exec python3 /run.py', stdout=subprocess.DEVNULL)
            try:
                for attempt in range(60):
                    try:
                        with smtplib.SMTP('127.0.0.1', 2525, timeout=2):
                            break
                    except (OSError, smtplib.SMTPException):
                        time.sleep(1)
                else:
                    raise AssertionError('SMTP listener did not start')
                # Only the allowlisted IP may connect.
                try:
                    smtplib.SMTP('127.0.0.1', 2525, timeout=5, source_address=('127.0.0.2', 0))
                except smtplib.SMTPConnectError as exc:
                    assert exc.smtp_code == 554
                else:
                    raise AssertionError('Unlisted client IP was accepted')
                with smtplib.SMTP('127.0.0.1', 2525, timeout=5) as client:
                    client.ehlo()
                    code, _ = client.mail('wrong@example.com')
                    assert code >= 500, 'Unlisted sender was accepted'
                message = EmailMessage()
                message['From'] = 'Original Scanner <scanner@example.com>'
                message['To'] = 'recipient@example.com'
                message['Subject'] = 'Local integration test'
                message.set_content('Body remains unchanged.\n')
                message.add_attachment(b'example attachment', maintype='application',
                                       subtype='octet-stream', filename='document.bin')
                with smtplib.SMTP('127.0.0.1', 2525, timeout=5) as client:
                    client.send_message(message)
                result = BytesParser(policy=policy.default).parsebytes(received.get(timeout=40))
                assert result['From'].addresses[0].display_name == 'Dokumentenscanner Büro'
                assert result['From'].addresses[0].addr_spec == 'scanner@example.com'
                assert result.get_body(preferencelist=('plain',)).get_content().strip() == 'Body remains unchanged.'
                assert next(result.iter_attachments()).get_payload(decode=True) == b'example attachment'
                logs = command('docker', 'logs', CONTAINER, capture_output=True, text=True)
                assert 'Verified TLS connection established' in logs.stdout + logs.stderr
                print('PASS: client allowlist, sender restriction, verified TLS, SMTP auth, display name, body and attachment')
            finally:
                subprocess.run(['docker', 'logs', CONTAINER], check=False)
                subprocess.run(['docker', 'rm', '-f', CONTAINER], check=False, stdout=subprocess.DEVNULL)
                server.shutdown()


if __name__ == '__main__':
    main()
