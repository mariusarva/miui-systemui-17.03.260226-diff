#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ZIP 条目级对比：新增 / 删除 / 内容变化（不依赖 apktool）。

用法：python3 zipdiff.py <原版.apk> <改版.apk> [输出文件]
默认输出 zip_layer.txt。
"""
import sys, os, zipfile, collections


def load(p):
    z = zipfile.ZipFile(p)
    return {i.filename: (i.file_size, i.CRC, i.compress_type) for i in z.infolist()}


def cat(n):
    if n.startswith("classes") and n.endswith(".dex"):
        return "dex"
    if n == "resources.arsc":
        return "arsc"
    if n == "AndroidManifest.xml":
        return "manifest"
    if n.startswith("res/"):
        return "res"
    if n.startswith("assets/"):
        return "assets"
    if n.startswith("lib/"):
        return "lib"
    if n.startswith("META-INF/"):
        return "META-INF"
    if n.startswith("kotlin/"):
        return "kotlin"
    return "other"


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    A, B = sys.argv[1], sys.argv[2]
    out = sys.argv[3] if len(sys.argv) > 3 else "zip_layer.txt"
    a, b = load(A), load(B)
    only_a = sorted(set(a) - set(b))
    only_b = sorted(set(b) - set(a))
    mod = sorted(k for k in set(a) & set(b) if a[k][:2] != b[k][:2])

    def summary(lst):
        return dict(collections.Counter(cat(n) for n in lst))

    print("A entries=%d B entries=%d" % (len(a), len(b)))
    print("onlyA=%d %s" % (len(only_a), summary(only_a)))
    print("onlyB=%d %s" % (len(only_b), summary(only_b)))
    print("modified=%d %s" % (len(mod), summary(mod)))

    with open(out, "w", encoding="utf-8") as f:
        f.write("### 仅原版 (A only) %d\n" % len(only_a))
        f.write("\n".join(only_a) + "\n")
        f.write("\n### 仅改版 (B only) %d\n" % len(only_b))
        f.write("\n".join(only_b) + "\n")
        f.write("\n### 内容变化 (modified) %d\n" % len(mod))
        for n in mod:
            f.write("%s  %s -> %s\n" % (n, a[n][:2], b[n][:2]))
    print("完整清单 ->", os.path.abspath(out))


if __name__ == "__main__":
    main()
