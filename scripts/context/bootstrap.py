"""Acquire the official SCANFI directory/README required by bounded context scripts."""
import argparse
import json
from pathlib import Path

from scanfi import BASE
from wms import request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=Path('.cache/catalogue/20261006'))
    args = parser.parse_args()
    guides = args.cache / 'guides'
    guides.mkdir(parents=True, exist_ok=True)
    records = []
    for url, name in [(BASE, 'scanfi-directory.raw'),
                      (BASE + '_SCANFI_v2_read_me.txt', 'scanfi-readme.raw')]:
        _, receipt = request(url, guides / name, budget=2_000_000)
        records.append(receipt)
    print(json.dumps({'resources': records, 'role': 'access documentation only'}, indent=2))


if __name__ == '__main__':
    main()
