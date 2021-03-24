from collections.abc import Mapping

from tqdm import tqdm


class LazyDict(dict):
    cache = {}

    def __getitem__(self, key):
        item = super().__getitem__(key)
        if isinstance(item, tuple) \
                and len(item) > 1 \
                and hasattr(item[0], '__call__'):
            if item not in self.cache:
                func, args = item[0], item[1:]
                self.cache[item] = func(*args)
            return self.cache[item]
        return item

    def __setitem__(self, key, item):
        super().__setitem__(key, item)

    def __iter__(self):
        return iter(self._raw_dict)

    def __len__(self):
        return len(self._raw_dict)


def download_progress(total_bytes, stream, filename, callback=None):
    block_size = 512  # 1 Kibibyte
    progress_bar = tqdm(total=total_bytes, unit='iB', unit_scale=True)
    current = 0
    with open(filename, 'wb') as file:
        # shutil.copyfileobj(response.raw, file, length=total_bytes)
        for data in stream(block_size):
            if callback:
                current += len(data)
                callback(current / total_bytes)
            progress_bar.update(len(data))
            file.write(data)
    progress_bar.close()
