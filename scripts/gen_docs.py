#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 data/ 生成 docs/01-代码层.md 与 docs/02-资源层.md"""
import os, re, collections

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
DOCS = os.path.join(BASE, "docs")
os.makedirs(DOCS, exist_ok=True)

MODULE = {
    "IosLeftIcons / 左置图标": [
        "statusbar/phone/ui/IosLeftIcons", "MiuiRotateIconInjector", "StatusBarIconControllerImpl",
        "KeyguardStatusBarViewController", "HomeStatusBarViewBinderInjector", "StatusBarRootKt$$ExternalSyntheticLambda3",
        "HomeStatusBarIconBlockListInteractor", "MiuiIconManagerUtils", "DarkIconDispatcherExt",
        "StatusBarIconView", "MiuiKeyguardStatusBarView", "PhoneStatusBarView", "MiuiPhoneStatusBarPolicy",
    ],
    "双排运营商/信号": [
        "pipeline/mobile", "ControlCenterStatusBarIcon", "ControlCenterFakeStatusIcons", "statusbar/phone/PhoneStatusBar",
    ],
    "通知中心头部": [
        "qs/MiuiNotificationHeaderView", "NotificationHeaderExpandController", "ControlCenterHeaderExpandController",
        "ControlCenterHeaderController", "ShadeHeaderClipController",
    ],
    "PIN 玻璃": ["keyguard/"],
    "毛玻璃/圆角": [
        "vieweffect/", "NotificationUtil$1", "StackScrollAlgorithm", "SharedNotificationContainerInteractor",
        "MiuiBaseNotifUtil",
    ],
    "时钟增强": ["views/MiuiClock", "miui/clock/"],
    "网速": ["NetworkSpeed"],
    "电量": ["MiuiBatteryMeterView"],
    "媒体": ["MiuiMediaViewControllerImpl"],
    "其它": [],
}


def module_of(cls):
    for name, pats in MODULE.items():
        for p in pats:
            if p and p in cls:
                return name
    return "其它"


def gen_code():
    rows = [l.rstrip("\n").split("\t") for l in open(os.path.join(DATA, "method_diff.tsv"), encoding="utf-8") if l.strip()]
    bycls = collections.defaultdict(list)
    for r in rows:
        if len(r) >= 4:
            bycls[r[0]].append((r[1], r[2], r[3]))
    real = [x.strip() for x in open(os.path.join(DATA, "real_classes.txt"), encoding="utf-8") if x.strip()]
    newc = [x.strip() for x in open(os.path.join(DATA, "new_classes.txt"), encoding="utf-8") if x.strip()]
    differ = [x.strip() for x in open(os.path.join(DATA, "differ_classes.txt"), encoding="utf-8") if x.strip()]

    mods = collections.Counter(module_of(c) for c in real)
    out = []
    out.append("# 代码层全量差异\n")
    out.append("原版 `系统界面_17.03.260226.r.apk` vs 改版 `MiuiSystemUI.apk`，apktool 3.0.3 解码态。\n")
    out.append("- 类总数：44,183 → 44,240（新增 57，删除 0）")
    out.append("- 内容不同类文件：%d" % len(differ))
    out.append("- 归一化后真实改动类：%d（剔除 %d 个纯重编译噪声）" % (len(real), len(differ) - len(real)))
    out.append("- 新增方法 21 / 删除方法 0 / 改动方法 %d\n" % sum(1 for r in rows if r[0] in real and r[1] == "改动"))
    out.append("## 按模块归属\n")
    out.append("| 模块 | 改动类数 |")
    out.append("|---|---|")
    for k, v in mods.most_common():
        out.append("| %s | %d |" % (k, v))
    out.append("")
    out.append("## 一、真实改动类的方法级清单\n")
    cur = None
    for c in real:
        out.append("### `%s`\n" % c)
        out.append("| 类型 | 方法 | +指令行 |")
        out.append("|---|---|---|")
        for kind, sig, n in sorted(bycls.get(c, []), key=lambda x: (x[0], x[1])):
            out.append("| %s | `%s` | %s |" % (kind, sig.replace("|", "\\|"), n))
        out.append("")
    out.append("## 二、新增类（57）\n")
    out.append("| 类 |")
    out.append("|---|")
    for c in newc:
        out.append("| `%s` |" % c.replace(".smali", "").replace("/", "."))
    out.append("")
    out.append("## 三、噪声明细\n")
    out.append("以下 %d 个类文件字节不同，但归一化后方法与字段完全一致，属 dex 重编译导致：" % (len(differ) - len(real)))
    out.append("")
    for c in differ:
        if c not in real:
            out.append("- `%s`" % c)
    out.append("")
    open(os.path.join(DOCS, "01-代码层.md"), "w", encoding="utf-8").write("\n".join(out))
    print("docs/01-代码层.md 生成完成：%d 类" % len(real))


def gen_res():
    v = open(os.path.join(DATA, "vals_diff.md"), encoding="utf-8").read()
    f = open(os.path.join(DATA, "resfile_diff.md"), encoding="utf-8").read()
    out = []
    out.append("# 资源层全量差异\n")
    out.append("`resources.arsc` 4,606,804 B → 4,792,648 B（+185,844 B）；`public.xml` 新增 41 个条目。\n")
    out.append("## 一、res 文件资源\n")
    out.append(f.replace("# res 文件资源差异（解码态）", "", 1).strip())
    out.append("")
    out.append("## 二、values 层\n")
    out.append(v.replace("# values 层差异", "", 1).strip())
    out.append("")
    out.append("## 三、layout / drawable / xml 逐文件 diff\n")
    out.append("完整 unified diff 见仓库 `data/res_diff_text/`。以下为按文件的关键摘录。\n")
    ddir = os.path.join(DATA, "res_diff_text")
    for fn in sorted(os.listdir(ddir)):
        txt = open(os.path.join(ddir, fn), encoding="utf-8").read().strip().splitlines()
        keep = [l for l in txt if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
        if not keep:
            continue
        out.append("### `%s`\n" % fn.replace(".xml.diff", "").replace("__", "/"))
        out.append("```diff")
        out.extend(l[:400] for l in keep[:60])
        out.append("```")
        out.append("")
    open(os.path.join(DOCS, "02-资源层.md"), "w", encoding="utf-8").write("\n".join(out))
    print("docs/02-资源层.md 生成完成")


if __name__ == "__main__":
    gen_code()
    gen_res()
