from datetime import datetime, timezone
import hashlib
import json
import requests

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from urllib.parse import urlparse
import base64

from django.contrib.auth import get_user_model


def sign(username, url, method, date, digest, domain):

    keyId = f'https://{domain}/ap/users/{username}/#main-key'

    User = get_user_model()
    user = User.objects.get(username=username)


    parsed = urlparse(url)

    target = parsed.path


    data = (
        f'(request-target): {method.lower()} {target}\n' + 
        f'host: {parsed.netloc}\n' + 
        f'date: {date}'
    )

    signed_header = '(request-target) host date'

    if digest:
        data += f'\ndigest: {digest}'
        signed_header += ' digest'


    private_key = serialization.load_pem_private_key(
        user.private_key.encode("utf-8"),
        password=None
    )

    signature_bytes = private_key.sign(
        data.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256()
    )

    signature = base64.b64encode(signature_bytes).decode("utf-8")

    http_signature_header = (
        f'keyId="{keyId}",' + 
        f'headers="{signed_header}",' +
        f'signature="{signature}",' + 
        'algorithm="rsa-sha256"'
    )

    return http_signature_header



def create_digest(body):
    digest_hash = hashlib.sha256(body).digest()

    digest_base64 = base64.b64encode(digest_hash).decode("utf-8")

    return f"sha-256={digest_base64}"


def create_signed_header(username, url, method, body, domain):
    

    date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

    parsed = urlparse(url)
    digest = create_digest(body)
    signature = sign(username, url, method, date, digest, domain)

    return {
        "Host": parsed.netloc,
        "Date": date,
        "Digest": digest,
        "Signature": signature,
        "Content-Type": "application/activity+json"

    }


def signed_post(username, url, body_dict, domain):
    body = json.dumps(body_dict).encode("utf-8")
    headers = create_signed_header(username, url, "POST", body, domain)

    request = requests.post(url, data=body, headers=headers, timeout=10)
    return request