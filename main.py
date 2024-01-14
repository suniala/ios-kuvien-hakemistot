import argparse
from os import makedirs
from os import walk, path
from shutil import copy2 as copy_with_metadata
from time import strptime, strftime

import exifread


def read_exif(image_path):
    with open(image_path, mode='rb') as f:
        return exifread.process_file(f)


def read_specific_exif(image_path):
    exif = read_exif(image_path)
    original_ts_str = 'EXIF DateTimeOriginal' in exif and str(exif['EXIF DateTimeOriginal']) or None
    original_ts = original_ts_str and strptime(original_ts_str, '%Y:%m:%d %H:%M:%S') or None
    return {
        # Image Model: iPhone 11 Pro
        'is_iphone': 'Image Model' in exif and str(exif['Image Model']).startswith('iPhone'),
        # EXIF DateTimeOriginal: 2022:05:27 13:48:26
        'original_ts': original_ts,
    }


def find_files_with_meta(root_path):
    metas = []
    for dirpath, dirnames, filenames in walk(root_path):
        for filename in filenames:
            image_path = path.join(dirpath, filename)
            meta = {
                'full_path': image_path,
                'path': image_path.removeprefix(root_path).strip('/')
            }
            # print(image_path)
            if filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
                # exif = read_exif(image_path)
                exif = read_specific_exif(image_path)
                meta['exif'] = exif
            metas.append(meta)

    return metas


def resolve_target(file_with_meta):
    target_from_path = file_with_meta['path'].strip('/').split('/')[0]
    if not target_from_path:
        raise Exception('Polusta ei löytynyt kohdetta tiedostolle: %s' % (file_with_meta['path']))

    exif = 'exif' in file_with_meta and file_with_meta['exif'] or None
    if exif and exif['is_iphone'] and exif['original_ts']:
        target = strftime('%Y-%m-%d', exif['original_ts'])
    else:
        target = target_from_path
    return {
        'target': target,
        'target_change': target != target_from_path
    }


def lue_kuvat(root_path):
    files_with_meta = find_files_with_meta(root_path)
    files_with_targets = []
    for f in files_with_meta:
        target, target_change = resolve_target(f).values()
        files_with_targets.append({'meta': f, 'target': target, 'target_change': target_change})
    return files_with_targets


def kopioi_kuvat(kuiva_ajo, polku_ulos, kuvat):
    for kuva in kuvat:
        kuvan_polku = kuva['meta']['full_path']
        if kuiva_ajo:
            print('%s %s -> <ulos>/%s' % (
                kuva['target_change'] and 'muuttuu' or 'ei-muutu',
                kuvan_polku,
                kuva['target']))
        else:
            kohdehakemisto = path.join(polku_ulos, kuva['target'])
            print('kopioidaan %s -> %s' % (kuvan_polku, kohdehakemisto))
            makedirs(kohdehakemisto, exist_ok=True)
            copy_with_metadata(kuvan_polku, kohdehakemisto)


def suorita(parametrit):
    kuvat = lue_kuvat(parametrit.sisaan)
    if kuvat:
        kopioi_kuvat(parametrit.listaa, parametrit.ulos, kuvat)
    else:
        print('Kuvia ei löytynyt.')


def lue_parametrit():
    parametrien_jasentaja = argparse.ArgumentParser(description='Lajittele kuvat.')
    parametrien_jasentaja.add_argument('--sisaan', metavar='sisaan', type=str,
                                       help='polku josta luetaan')
    operaatioryhma = parametrien_jasentaja.add_mutually_exclusive_group(required=True)
    operaatioryhma.add_argument('--ulos', metavar='ulos', type=str, required=False,
                                help='polku johon kirjoitetaan')
    operaatioryhma.add_argument('--listaa', action='store_true', required=False,
                                help='listaa tiedostot, älä tee muuta')
    return parametrien_jasentaja.parse_args()


if __name__ == '__main__':
    suorita(lue_parametrit())
