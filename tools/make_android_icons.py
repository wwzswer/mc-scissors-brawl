# -*- coding: utf-8 -*-
"""生成 Android 各密度启动图标：python tools/make_android_icons.py <res目录>"""
import os
import sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), 'icon-512.png')
DENSITIES = {
    'mipmap-mdpi': 48,
    'mipmap-hdpi': 72,
    'mipmap-xhdpi': 96,
    'mipmap-xxhdpi': 144,
    'mipmap-xxxhdpi': 192,
}

def main():
    res = sys.argv[1] if len(sys.argv) > 1 else 'android/res'
    img = Image.open(SRC).convert('RGB')
    for folder, size in DENSITIES.items():
        d = os.path.join(res, folder)
        os.makedirs(d, exist_ok=True)
        out = os.path.join(d, 'ic_launcher.png')
        img.resize((size, size), Image.LANCZOS).save(out, 'PNG', optimize=True)
        print('  ', out, size)

if __name__ == '__main__':
    main()
