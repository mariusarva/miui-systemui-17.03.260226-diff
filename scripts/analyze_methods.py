#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
方法级归一化 smali diff（apktool 解码态）

剔除 dex 重编译噪声：nop / .source / .line / .registers / .locals /
寄存器重编号 / 标签重命名 / const-string-jumbo / 字段静态初值。
输出 data/real_diff.md + data/method_diff.tsv

用法（先在解包目录跑索引脚本生成 data/*.txt）：
  DIFF_A=/path/A DIFF_B=/path/B DIFF_DATA=/path/data python3 analyze_methods.py
"""
import os, re, collections

A = os.environ.get("DIFF_A", "A")
B = os.environ.get("DIFF_B", "B")
DATA = os.environ.get("DIFF_DATA", "data")

CALL = re.compile(r"invoke-[\w/]+.*?L([\w/$]+);->([\w$<>]+)")


def strip_class(root, rel):
    """按类路径（去掉 smali_classesN 前缀）定位文件"""
    for d in ("smali", "smali_classes2", "smali_classes3", "smali_classes4", "smali_classes5"):
        p = os.path.join(root, d, rel)
        if os.path.exists(p):
            return p
    return None


def norm(s):
    s = s.strip()
    if not s or s == "nop":
        return ""
    if s.startswith((".source ", ".line ", ".prologue", ".registers", ".locals")):
        return ""
    if s.startswith(".field "):
        s = re.sub(r"\s*=\s*(null|false|true|0x0|-?\d+(\.\d+)?[a-zA-Z]*)$", "", s)
    s = s.replace("const-string/jumbo", "const-string")
    s = re.sub(r"\b[vp]\d+\b", "R", s)
    s = re.sub(r":[A-Za-z0-9_$-]+", ":L", s)
    return s


def parse(path):
    methods, fields, cur, body = {}, [], None, []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            if s.startswith(".field "):
                n = norm(s)
                if n:
                    fields.append(n)
            if s.startswith(".method "):
                cur, body = s[8:].strip(), []
            elif s == ".end method":
                if cur is not None:
                    methods[cur] = body
                cur = None
            elif cur is not None:
                n = norm(s)
                if n:
                    body.append(n)
    return methods, fields


def lines(p):
    p = os.path.join(DATA, p)
    if not os.path.exists(p):
        return []
    return [x.strip() for x in open(p, encoding="utf-8") if x.strip()]


def main():
    differ = lines("differ_classes.txt")
    newc = lines("new_classes.txt")
    delc = lines("del_classes.txt")
    real = []
    method_rows = []
    fields_new, fields_del = [], []
    hot = collections.Counter()
    new_calls = collections.Counter()

    for c in differ:
        pa, pb = strip_class(A, c), strip_class(B, c)
        if not pa or not pb:
            continue
        mo, fo = parse(pa)
        mm, fm = parse(pb)
        add = sorted(set(mm) - set(mo))
        rm = sorted(set(mo) - set(mm))
        chg = [k for k in sorted(set(mo) & set(mm)) if mo[k] != mm[k]]
        nf = sorted(set(fm) - set(fo))
        df = sorted(set(fo) - set(fm))
        if not (add or rm or chg or nf or df):
            continue  # 纯噪声
        real.append(c)
        for m in add:
            method_rows.append((c, "新增", m, len(mm.get(m, []))))
        for m in rm:
            method_rows.append((c, "删除", m, len(mo.get(m, []))))
        for m in chg:
            oldb, newb = mo[m], mm[m]
            added = [x for x in newb if x not in oldb]
            removed = [x for x in oldb if x not in newb]
            method_rows.append((c, "改动", "%s (+%d/-%d)" % (m, len(added), len(removed)), len(added)))
            for ln in added:
                for cls, meth in CALL.findall(ln):
                    hot["%s;->%s" % (cls, meth)] += 1
        for f in nf:
            fields_new.append((c, f))
        for f in df:
            fields_del.append((c, f))

    for c in newc:
        pb = strip_class(B, c)
        if not pb:
            continue
        mm, _ = parse(pb)
        for m, body in mm.items():
            for ln in body:
                for cls, meth in CALL.findall(ln):
                    new_calls["%s;->%s" % (cls, meth)] += 1

    out = os.path.join(DATA, "real_diff.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("# 归一化后的真实改动\n\n")
        f.write("- 内容不同类文件：%d\n- 归一化后真实改动类：%d\n" % (len(differ), len(real)))
        f.write("- 新增类：%d / 删除类：%d\n" % (len(newc), len(delc)))
        f.write("- 新增方法：%d / 删除方法：%d / 改动方法：%d\n\n" % (
            sum(1 for r in method_rows if r[1] == "新增"),
            sum(1 for r in method_rows if r[1] == "删除"),
            sum(1 for r in method_rows if r[1] == "改动")))
        f.write("## 真实改动类清单\n\n")
        for c in real:
            f.write("- `%s`\n" % c)
        f.write("\n## 新增方法\n\n")
        for r in method_rows:
            if r[1] == "新增":
                f.write("- `%s` → `%s`\n" % (r[0], r[2]))
        f.write("\n## 改动方法（+新增指令行 / -删除指令行）\n\n")
        for r in method_rows:
            if r[1] == "改动":
                f.write("- `%s` → `%s`\n" % (r[0], r[2]))
        f.write("\n## 新增字段\n\n")
        for c, x in fields_new:
            f.write("- `%s` : %s\n" % (c, x))
        f.write("\n## 删除字段\n\n")
        for c, x in fields_del:
            f.write("- `%s` : %s\n" % (c, x))
        f.write("\n## 改动方法里新增指令调用的热点（top 80）\n\n")
        for k, v in hot.most_common(80):
            f.write("- %4d  `%s`\n" % (v, k))
        f.write("\n## 新增类里调用的外部符号（top 80）\n\n")
        for k, v in new_calls.most_common(80):
            f.write("- %4d  `%s`\n" % (v, k))

    with open(os.path.join(DATA, "method_diff.tsv"), "w", encoding="utf-8") as f:
        for r in method_rows:
            f.write("%s\t%s\t%s\t%d\n" % r)

    open(os.path.join(DATA, "real_classes.txt"), "w", encoding="utf-8").write("\n".join(real))
    print("真实改动类 %d / 内容不同 %d；方法行 %d" % (len(real), len(differ), len(method_rows)))
    print("输出:", out)


if __name__ == "__main__":
    main()
