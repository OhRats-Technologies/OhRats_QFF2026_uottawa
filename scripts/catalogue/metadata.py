"""The byte/identity contract for a cached official catalogue response."""
import hashlib
import json

API = 'https://open.canada.ca/data/api/action/package_show?id='
MAX_BYTES = 4_000_000
OWNER_IDS = [
    '7cbdfae1-f724-4679-8f0f-1c611f17186f',
    'a6b81e8b-d429-4629-9121-5a56786fcb83',
    '836082d5-d55f-46c3-9b9c-aaf1a306c247',
    '0bce352f-6f3f-4a30-9763-c80805fcf272',
    '347a2de5-1006-4c1f-ba09-b66947654d0a',
    '1728e7f9-472a-474e-9e04-f96bf59479f9',
    'adfa340a-1781-48b1-ab17-2e1ca1b915df',
]


def read_package(path):
    with path.open('rb') as stream:
        body = stream.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        raise ValueError(f'{path.stem}: cached metadata exceeds byte budget')
    receipt = json.loads(path.with_suffix('.receipt.json').read_text())
    package = json.loads(body)
    identifier = path.stem
    if hashlib.sha256(body).hexdigest() != receipt['sha256']:
        raise ValueError(f'{identifier}: cached metadata hash mismatch')
    if not package.get('success') or package['result']['id'] != identifier:
        raise ValueError(f'{identifier}: cached metadata identity mismatch')
    if (receipt['id'] != identifier or receipt['url'] != API + identifier
            or receipt['status'] != 200 or receipt['bytes'] != len(body)):
        raise ValueError(f'{identifier}: cached request receipt mismatch')
    return package['result'], receipt
