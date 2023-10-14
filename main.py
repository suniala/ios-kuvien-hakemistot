import exifread
from os import walk, path
from time import strptime, strftime


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


def find_files_with_meta():
    metas = []
    root_path = '/home/kosmik/Media/kuvat/2022'
    for dirpath, dirnames, filenames in walk(root_path):
        for filename in filenames:
            image_path = path.join(dirpath, filename)
            meta = {
                'full_path': image_path,
                'path': image_path.removeprefix(root_path).strip('/')
            }
            print(image_path)
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


if __name__ == '__main__':
    files_with_meta = find_files_with_meta()
    print(files_with_meta)
    files_with_targets = [{'meta': f, 'target': resolve_target(f)} for f in files_with_meta]
    for file in files_with_targets:
        print(file['meta']['full_path'])
        print('  %s' % file['target'])
        print('  %s' % ('exif' in file['meta'] and file['meta']['exif'] or None))
