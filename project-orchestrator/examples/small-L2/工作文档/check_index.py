# -*- coding: utf-8 -*-
"""索引自检（示例脚本）：条目数、锚点、相对链接、外部引用。"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "..", "交付成果（DELIVERABLES）")
HTML = os.path.join(DOCS, "索引页_index_v1.0.html")
MD = os.path.join(DOCS, "文档索引_v1.0.md")


def main():
    issues = []
    html = open(HTML, encoding="utf-8").read()
    md = open(MD, encoding="utf-8").read()

    cards = re.findall(r'<article class="card" id="([^"]+)"', html)
    rows = [ln for ln in md.splitlines() if ln.startswith("| 源文档/")]
    if len(cards) != 8:
        issues.append("HTML 卡片数 %d != 8" % len(cards))
    if len(rows) != 8:
        issues.append("Markdown 条目数 %d != 8" % len(rows))

    ids = set(cards)
    anchors = set(re.findall(r'href="#([^"]+)"', html))
    for a in sorted(anchors - ids - {"top"}):
        issues.append("锚点目标不存在：#%s" % a)

    for href in re.findall(r'href="([^"#][^"]*)"', html):
        if href.startswith(("http://", "https://", "//")):
            issues.append("发现外部引用：%s" % href)
        elif not os.path.exists(os.path.join(DOCS, href)):
            issues.append("相对链接目标不存在：%s" % href)

    for m in ("http://", "https://"):
        if m in html:
            issues.append("发现外部 URL：%s" % m)

    print("卡片 %d ｜ Markdown 条目 %d ｜ 锚点 %d ｜ 问题 %d"
          % (len(cards), len(rows), len(anchors), len(issues)))
    for i in issues:
        print("  -", i)
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
