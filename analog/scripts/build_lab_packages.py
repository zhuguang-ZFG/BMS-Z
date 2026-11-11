"""Build reproducible downloadable labs; instructions have one source in docs/."""
import argparse
import io
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
LABS = ROOT / 'assets/labs'
IDS = ('rc', 'mosfet', 'lm358')


def section(text, marker):
    match = re.search(rf'<!-- {re.escape(marker)}:start -->\n(.*?)\n<!-- {re.escape(marker)}:end -->', text, re.S)
    if not match:
        raise ValueError(f'Missing lab instructions: {marker}')
    return match[1].strip()


def build_packages():
    text = (ROOT / 'docs/p8-03-s8-3.md').read_text(encoding='utf-8')
    common = section(text, 'labs:common')
    for lab in IDS:
        instructions = '# ' + lab.upper() + ' 实验包\n\n' + common + '\n\n' + section(text, f'lab:{lab}') + '\n'
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_STORED) as archive:
            entries = {'README.md': instructions.encode('utf-8'),
                       'LICENSE': (ROOT / 'LICENSE').read_text(encoding='utf-8').encode('utf-8')}
            for filename in ('circuit.cir', 'bom.csv', 'reference.csv', 'measurements.csv'):
                entries[filename] = (LABS / lab / filename).read_text(encoding='utf-8').replace('\r\n', '\n').encode('utf-8')
            for filename, content in sorted(entries.items()):
                info = zipfile.ZipInfo(filename, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, content)
        yield lab, buffer.getvalue()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for lab, data in build_packages():
        path = LABS / f'{lab}-lab.zip'
        if args.check:
            if not path.exists() or path.read_bytes() != data:
                raise SystemExit(f'{path.name} is stale; run python scripts/build_lab_packages.py')
        else:
            path.write_bytes(data)
    print('Three lab packages are reproducible.' if args.check else 'Built three lab packages.')


if __name__ == '__main__':
    main()
