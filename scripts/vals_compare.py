#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源层集合对比（apktool 解码态）

values 层：拆成 (variant, type, name) -> 规范化值，避免 XML 顺序噪声。
文件资源层：res/<type>-<variant>/<name>.<ext> 按相对路径 -> 规范化文本对比。
颜色 6/8 位归一化（#ffRRGGBB == #RRGGBB）。

用法：DIFF_A=A DIFF_B=B DIFF_DATA=data python3 vals_compare.py
"""
import os, re, sys
import xml.etree.ElementTree as ET

A = os.environ.get("DIFF_A", "A")
B = os.environ.get("DIFF_B", "B")
DATA = os.environ.get("DIFF_DATA", "data")


def colnorm(v):
    v = (v or "").strip()
    m = re.fullmatch(r"#([0-9a-fA-F]{6})", v)
    if m:
        return "#" + m.group(1).lower()
    m = re.fullmatch(r"#ff([0-9a-fA-F]{6})", v)
    if m:
        return "#" + m.group(1).lower()
    return v


def values_map(root):
    """res/values*/*.xml -> {(variant, tag, name): value}"""
    out = {}
    for d in sorted(os.listdir(os.path.join(root, "res"))):
        if not d.startswith("values"):
            continue
        variant = "default" if d == "values" else d[len("values"):]
        p = os.path.join(root, "res", d)
        for fn in sorted(os.listdir(p)):
            if not fn.endswith(".xml"):
                continue
            try:
                tree = ET.parse(os.path.join(p, fn))
            except Exception as e:
                print("解析失败", p, fn, e, file=sys.stderr)
                continue
            for el in tree.getroot():
                if not isinstance(el.tag, str):
                    continue
                name = el.get("name")
                if name is None:
                    continue
                # 值 = 属性集合（去 format 等展示性属性）+ 文本
                attrs = {k: v for k, v in el.attrib.items()
                         if k not in ("name", "format", "translatable")}
                txt = (el.text or "").strip()
                sub = []
                for c in el:
                    if isinstance(c.tag, str):
                        sub.append(c.tag + ":" + repr(c.attrib) + ":" + ((c.text or "").strip()))
                val = colnorm(txt) if el.tag in ("color", "dimen") else txt
                out[(variant, el.tag, name)] = (val, tuple(sorted(attrs.items())), tuple(sub))
    return out


def file_map(root):
    """res/<type>-<variant>/<file> -> 规范化文本（只对字节有变化的文件做后续分析）"""
    out = {}
    base = os.path.join(root, "res")
    for d in sorted(os.listdir(base)):
        if d.startswith("values"):
            continue
        p = os.path.join(base, d)
        if not os.path.isdir(p):
            continue
        for fn in sorted(os.listdir(p)):
            fp = os.path.join(p, fn)
            if not os.path.isfile(fp):
                continue
            rel = d + "/" + fn
            try:
                txt = open(fp, encoding="utf-8").read()
                txt = re.sub(r">\s+<", "><", txt.strip())
            except Exception:
                out[rel] = ("BIN", os.path.getsize(fp))
                continue
            out[rel] = ("TXT", txt)
    return out


def main():
    os.makedirs(DATA, exist_ok=True)
    va, vb = values_map(A), values_map(B)
    fa, fb = file_map(A), file_map(B)

    new_v = sorted(set(vb) - set(va))
    del_v = sorted(set(va) - set(vb))
    chg_v = sorted(k for k in set(va) & set(vb) if va[k] != vb[k])

    new_f = sorted(set(fb) - set(fa))
    del_f = sorted(set(fa) - set(fb))
    chg_f = sorted(k for k in set(fa) & set(fb) if fa[k] != fb[k])

    with open(os.path.join(DATA, "vals_diff.md"), "w", encoding="utf-8") as f:
        f.write("# values 层差异\n\n")
        f.write("- 新增键 %d / 删除键 %d / 值变化 %d\n\n" % (len(new_v), len(del_v), len(chg_v)))
        f.write("## 新增键\n\n")
        for k in new_v:
            f.write("- `%s/%s/%s` = `%s`\n" % (k[0], k[1], k[2], str(vb[k][0])[:200]))
        f.write("\n## 删除键\n\n")
        for k in del_v:
            f.write("- `%s/%s/%s` = `%s`\n" % (k[0], k[1], k[2], str(va[k][0])[:200]))
        f.write("\n## 值变化\n\n")
        for k in chg_v:
            f.write("- `%s/%s/%s` : `%s` → `%s`\n" % (k[0], k[1], k[2], str(va[k][0])[:160], str(vb[k][0])[:160]))

    with open(os.path.join(DATA, "resfile_diff.md"), "w", encoding="utf-8") as f:
        f.write("# res 文件资源差异（解码态）\n\n")
        f.write("- 新增 %d / 删除 %d / 内容变化 %d\n\n" % (len(new_f), len(del_f), len(chg_f)))
        f.write("## 新增\n\n")
        for k in new_f:
            f.write("- `%s`\n" % k)
        f.write("\n## 删除\n\n")
        for k in del_f:
            f.write("- `%s`\n" % k)
        f.write("\n## 内容变化\n\n")
        for k in chg_f:
            f.write("- `%s`\n" % k)

    # 详细 diff 目录
    ddir = os.path.join(DATA, "res_diff_text")
    os.makedirs(ddir, exist_ok=True)
    import difflib
    for k in chg_f:
        if fa[k][0] != "TXT" or fb[k][0] != "TXT":
            continue
        sa = re.sub("><", ">\n<", fa[k][1]).splitlines()
        sb = re.sub("><", ">\n<", fb[k][1]).splitlines()
        d = "\n".join(difflib.unified_diff(sa, sb, fromfile="A/" + k, tofile="B/" + k, lineterm="", n=2))
        safe = k.replace("/", "__")
        open(os.path.join(ddir, safe + ".diff"), "w", encoding="utf-8").write(d)

    print("values: new %d del %d chg %d" % (len(new_v), len(del_v), len(chg_v)))
    print("resfile: new %d del %d chg %d" % (len(new_f), len(del_f), len(chg_f)))


if __name__ == "__main__":
    main()
