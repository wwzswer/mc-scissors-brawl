# -*- coding: utf-8 -*-
"""把 classes.dex 放进 APK 并重新打包成干净的 zip（这台机器没有 zip 命令时的替代）

用法： python tools/apk_repack.py <base.apk> <classes.dex>
"""
import os
import sys
import shutil
import tempfile
import zipfile


def repack(apk_path, dex_path):
    tmp = tempfile.mkdtemp(prefix='apkrepack-')
    try:
        with zipfile.ZipFile(apk_path) as z:
            z.extractall(tmp)
        shutil.copy(dex_path, os.path.join(tmp, 'classes.dex'))

        entries = []
        for root, _dirs, files in os.walk(tmp):
            for name in files:
                full = os.path.join(root, name)
                rel = os.path.relpath(full, tmp).replace(os.sep, '/')
                entries.append((full, rel))

        # resources.arsc / AndroidManifest.xml / classes.dex 尽量靠前，其余保持相对顺序
        def rank(rel):
            order = {'resources.arsc': 0, 'AndroidManifest.xml': 1, 'classes.dex': 2}
            return order.get(rel, 3)

        entries.sort(key=lambda p: (rank(p[1]), p[1]))

        # Android 11+（targetSdk >= 30）硬性要求：
        #   resources.arsc 必须 STORED（不压缩）且 4 字节对齐，否则安装报
        #   INSTALL_PARSE_FAILED_RESOURCES_ARSC_COMPRESSED / "Failure [-124]"
        # 所以这里对 resources.arsc 用 ZIP_STORED，其余照常 DEFLATE。
        out = apk_path + '.new'
        with zipfile.ZipFile(out, 'w') as z:
            for full, rel in entries:
                if rel == 'resources.arsc':
                    z.write(full, rel, compress_type=zipfile.ZIP_STORED)
                else:
                    z.write(full, rel, compress_type=zipfile.ZIP_DEFLATED)
        os.replace(out, apk_path)
        return len(entries)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    n = repack(sys.argv[1], sys.argv[2])
    print('   重新打包完成：%d 个条目（含 classes.dex）' % n)
