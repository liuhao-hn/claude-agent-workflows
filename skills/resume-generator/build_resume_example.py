#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_resume_example.py — 单页中文简历构建脚本示例。

工作流：HTML（含 CSS style + 占位照片 src）→ Chrome headless 渲染 → A4 单页 PDF → pypdf 校验页数。

用法：
    python3 build_resume_example.py --html 个人简历.html --photo 证件照.jpg --out 个人简历.pdf

依赖：Python3 + pypdf + Chrome（macOS 路径 /Applications/Google Chrome.app，可改 CHROME 变量）。
本文件是示例模板，按需改路径与参数。
"""

import argparse
import base64
import subprocess
import tempfile
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def embed_photo(html: Path, photo: Path) -> str:
    """把照片 base64 进 HTML 的 {{PHOTO_BASE64}} 占位；无照片则去掉 img 标签。"""
    text = html.read_text(encoding="utf-8")
    if photo.exists():
        b64 = base64.b64encode(photo.read_bytes()).decode()
        return text.replace("{{PHOTO_BASE64}}", f"data:image/jpeg;base64,{b64}")
    return text.replace('src="{{PHOTO_BASE64}}"', "")


def render(html_text: str, out: Path) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html_text)
        tmp_html = f.name
    cmd = [CHROME, "--headless", "--disable-gpu", "--no-sandbox",
           f"--print-to-pdf={out}", f"file://{tmp_html}"]
    try:
        subprocess.run(cmd, check=True)
    finally:
        Path(tmp_html).unlink(missing_ok=True)


def page_count(pdf: Path) -> int:
    from pypdf import PdfReader
    return len(PdfReader(str(pdf)).pages)


def main() -> None:
    p = argparse.ArgumentParser(description="单页中文简历构建示例")
    p.add_argument("--html", required=True, help="含 CSS 的 HTML 简历文件")
    p.add_argument("--photo", default="", help="证件照路径（可缺省）")
    p.add_argument("--out", required=True, help="输出 PDF 路径")
    args = p.parse_args()

    html_text = embed_photo(Path(args.html), Path(args.photo))
    out = Path(args.out)
    render(html_text, out)
    pages = page_count(out)
    print(f"已生成: {out}（{pages} 页）")
    if pages != 1:
        print("⚠ 非单页，请调整字号/行距或删减内容")


if __name__ == "__main__":
    main()
