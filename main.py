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
    root_path = root_path
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
    exif = 'exif' in file_with_meta and file_with_meta['exif'] or None
    if exif and exif['is_iphone'] and exif['original_ts']:
        target = strftime('%Y-%m-%d', exif['original_ts'])
    else:
        target = file_with_meta['path'].strip('/').split('/')[0]
        if not target:
            raise Exception('Polusta ei löytynyt kohdetta tiedostolle: %s' % (file_with_meta['path']))
    return target


def lue_kuvat(root_path):
    files_with_meta = find_files_with_meta(root_path)
    files_with_targets = [{'meta': f, 'target': resolve_target(f)} for f in files_with_meta]
    return files_with_targets


def kopioi_kuvat(polku_ulos, kuvat):
    for kuva in kuvat:
        makedirs(path.join(polku_ulos, kuva['target']), exist_ok=True)
        kuvan_polku = kuva['meta']['full_path']
        kohdehakemisto = path.join(polku_ulos, kuva['target'])
        print('kopioidaan %s -> %s' % (kuvan_polku, kohdehakemisto))
        copy_with_metadata(kuvan_polku, kohdehakemisto)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Lajittele kuvat.')
    parser.add_argument('sisaan', metavar='sisaan', type=str,
                        help='polku josta luetaan')
    parser.add_argument('ulos', metavar='ulos', type=str,
                        help='polku johon kirjoitetaan')

    args = parser.parse_args()
    kuvat = lue_kuvat(args.sisaan)
    print(kuvat[0])
    kopioi_kuvat(args.ulos, kuvat)
