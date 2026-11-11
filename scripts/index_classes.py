#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""类级索引与 md5 比对：生成 new_classes.txt / del_classes.txt / differ_classes.txt

按「去 smali_classesN 前缀的类路径」建索引，避免同一类在 A/B 落在不同 dex 目录时误判。
用法：python3 index_classes.py <A解码目录> <B解码目录> <输出data目录>
"""
import os, sys, hashlib

def index(root):
    m = {}
    for d in sorted(os.listdir(root)):
        if not d.startswith("smali"):
            continue
        for dp, _, fs in os.walk(os.path.join(root, d)):
            for f in fs:
                if f.endswith(".smali"):
                    p = os.path.join(dp, f)
                    m.setdefault(os.path.relpath(p, os.path.join(root, d)), p)
    return m

def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def main():
    A, B, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(OUT, exist_ok=True)
    a, b = index(A), index(B)
    new = sorted(set(b) - set(a))
    dele = sorted(set(a) - set(b))
    mod = [k for k in sorted(set(a) & set(b)) if md5(a[k]) != md5(b[k])]
    open(os.path.join(OUT, "new_classes.txt"), "w").write("\n".join(new))
    open(os.path.join(OUT, "del_classes.txt"), "w").write("\n".join(dele))
    open(os.path.join(OUT, "differ_classes.txt"), "w").write("\n".join(mod))
    print("A=%d B=%d new=%d del=%d mod=%d" % (len(a), len(b), len(new), len(dele), len(mod)))

if __name__ == "__main__":
    main()
