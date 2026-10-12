from email.charset import Charset, BASE64
from email.header import Header


def make_sender_header(name, address):
    if any(ord(c) < 32 or ord(c) == 127 for c in name):
        raise ValueError('Sender name must not contain control characters')
    if len(name) > 200:
        raise ValueError('Sender name must not exceed 200 characters')
    name = name.strip()
    if not name:
        return None
    charset = Charset('utf-8')
    charset.header_encoding = BASE64
    encoded = Header(name, charset, header_name='From').encode(linesep=' ')
    return f'From: {encoded} <{address}>'
