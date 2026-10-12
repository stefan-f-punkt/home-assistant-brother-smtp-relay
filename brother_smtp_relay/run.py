import ipaddress
import json
import os
import pathlib
import re
import subprocess
from sender_header import make_sender_header

options = json.loads(pathlib.Path('/data/options.json').read_text())
client = str(ipaddress.IPv4Address(options['allowed_client']))
host = options['relay_host']
port = int(options['relay_port'])
username = options['relay_username']
password = options['relay_password']
sender = options['sender_address']
sender_header = make_sender_header(options.get('sender_name', ''), sender)
if not re.fullmatch(r'[A-Za-z0-9.-]+', host) or not 1 <= port <= 65535:
    raise SystemExit('Invalid relay host or port')
if not password:
    raise SystemExit('Please enter the Brevo SMTP key in relay_password first.')
if any(c in username + password + sender for c in '\r\n\x00'):
    raise SystemExit('Invalid newline in configuration')
if not re.fullmatch(r'[A-Za-z0-9_.+%-]+@[A-Za-z0-9.-]+', sender):
    raise SystemExit('Invalid sender address')

# Preserve deferred messages across add-on restarts.
spool = pathlib.Path('/var/spool/postfix')
data_spool = pathlib.Path('/data/spool')
if not data_spool.exists():
    subprocess.run(['cp', '-a', str(spool), str(data_spool)], check=True)
if not spool.is_symlink():
    subprocess.run(['rm', '-rf', str(spool)], check=True)
    spool.symlink_to(data_spool)

os.umask(0o077)
sasl = pathlib.Path('/etc/postfix/sasl_passwd')
sasl.write_text(f'[{host}]:{port} {username}:{password}\n')
subprocess.run(['postmap', 'lmdb:' + str(sasl)], check=True)
pathlib.Path('/etc/postfix/allowed_senders').write_text(sender + ' OK\n')
subprocess.run(['postmap', 'lmdb:/etc/postfix/allowed_senders'], check=True)

settings = {
 'myhostname': 'brother-relay.home.arpa',
 'mydestination': '',
 'alias_maps': '',
 'alias_database': '',
 'inet_interfaces': 'all',
 'inet_protocols': 'ipv4',
 'mynetworks': client + '/32',
 'relayhost': f'[{host}]:{port}',
 'smtp_sasl_auth_enable': 'yes',
 'smtp_sasl_password_maps': 'lmdb:/etc/postfix/sasl_passwd',
 'smtp_sasl_security_options': 'noanonymous',
 'smtp_sasl_tls_security_options': 'noanonymous',
 'smtp_tls_security_level': 'verify',
 'smtp_tls_CAfile': '/etc/ssl/cert.pem',
 'smtp_tls_mandatory_protocols': '>=TLSv1.2',
 'smtp_tls_loglevel': '1',
 'smtpd_tls_security_level': 'none',
 'smtpd_sasl_auth_enable': 'no',
 'smtpd_client_restrictions': 'permit_mynetworks, reject',
 'smtpd_delay_reject': 'no',
 'smtpd_relay_restrictions': 'permit_mynetworks, reject',
 'smtpd_sender_restrictions': 'check_sender_access lmdb:/etc/postfix/allowed_senders, reject',
 'message_size_limit': '26214400',
 'maillog_file': '/dev/stdout',
 'maillog_file_prefixes': '/dev',
 'smtputf8_enable': 'no',
 'compatibility_level': '3.6',
}
if sender_header:
    path = pathlib.Path('/etc/postfix/sender_header_checks')
    path.write_text('/^From:/ REPLACE ' + sender_header + '\n')
    path.chmod(0o644)
    settings['smtp_header_checks'] = 'regexp:' + str(path)
    check = subprocess.run(['postmap', '-q', 'From: Scanner <' + sender + '>',
                            'regexp:' + str(path)], check=True, capture_output=True, text=True)
    if check.stdout.strip() != 'REPLACE ' + sender_header:
        raise SystemExit('Sender-name header rule validation failed')
else:
    settings['smtp_header_checks'] = ''
for key, value in settings.items():
    subprocess.run(['postconf', '-e', key + ' = ' + value], check=True)
# Single listener, with no management or incoming internet service.
pathlib.Path('/etc/postfix/master.cf').write_text('''2525 inet n - n - - smtpd
pickup unix n - n 60 1 pickup
cleanup unix n - n - 0 cleanup
qmgr unix n - n 300 1 qmgr
rewrite unix - - n - - trivial-rewrite
tlsmgr unix - - n 1000? 1 tlsmgr
bounce unix - - n - 0 bounce
defer unix - - n - 0 bounce
trace unix - - n - 0 bounce
verify unix - - n - 1 verify
flush unix n - n 1000? 0 flush
proxymap unix - - n - - proxymap
proxywrite unix - - n - 1 proxymap
smtp unix - - n - - smtp
relay unix - - n - - smtp
showq unix n - n - - showq
error unix - - n - - error
retry unix - - n - - error
discard unix - - n - - discard
local unix - n n - - local
virtual unix - n n - - virtual
lmtp unix - - n - - lmtp
anvil unix - - n - 1 anvil
scache unix - - n - 1 scache
postlog unix-dgram n - n - 1 postlogd
''')
subprocess.run(['postfix', 'check'], check=True)
print(f'Relay ready: accepts only {client}; upstream {host}:{port} with verified TLS', flush=True)
# Retry persisted messages after the mail system has started.
subprocess.Popen(['sh', '-c', 'sleep 2; postfix flush'])
os.execvp('postfix', ['postfix', 'start-fg'])
