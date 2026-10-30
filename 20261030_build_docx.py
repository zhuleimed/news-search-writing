#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把“新闻解读纯文本 + 配图”组装成头条风格的 Word 文档。

排版规则（参照头条图文文章的阅读习惯）：
    - 标题：22 磅加粗，左对齐，深色；
    - 标题下：一行小字“全文约 XXXX 字”，灰色；
    - 正文：12 磅（小四）微软雅黑，1.5 倍行距，段后 10 磅，不首行缩进；
    - 配图：居中，宽 15.5 厘米；图下配 9 磅灰色说明，注明来源；
    - 文末：参考资料 9.5 磅灰色；免责声明 9 磅灰色。

用法：
    python 20261030_build_docx.py \
        --txt news_papers/20261030/20261030_1014_01.txt \
        --images news_papers/20261030/images/01/images_manifest.json \
        --out news_papers/20261030/20261030_1014_01.docx \
        --rank 3 \
        --original-title "“张雪机车”商标终于归“张雪”了"
"""

import argparse
import json
import os
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image

# ====================== 版式参数 ======================
FONT = "微软雅黑"
TITLE_SIZE = 22
BODY_SIZE = 12
REF_SIZE = 9.5
CAPTION_SIZE = 9
META_SIZE = 9
IMAGE_WIDTH_CM = 15.5
IMAGE_MAX_HEIGHT_CM = 18.0

SHORT_DISCLAIMER = "声明：本文图片来源于网络，版权归原作者所有，如有侵权请联系删除。"

TITLE_COLOR = RGBColor(0x1A, 0x1A, 0x1A)
BODY_COLOR = RGBColor(0x22, 0x22, 0x22)
GRAY = RGBColor(0x88, 0x88, 0x88)
LIGHT_GRAY = RGBColor(0x66, 0x66, 0x66)


def set_run_font(run, size=BODY_SIZE, bold=False, color=BODY_COLOR, italic=False):
    """统一设置中英文字体，避免 Word 里中文变成宋体。"""
    run.font.name = FONT
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), FONT)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = color


def add_text(doc, text, size=BODY_SIZE, bold=False, color=BODY_COLOR,
             align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=10,
             line_spacing=1.5, first_line_indent=None):
    """添加一个文字段落，并设置头条常见的行距、段距。"""
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = align
    pf.space_after = Pt(space_after)
    pf.line_spacing = line_spacing
    if first_line_indent is not None:
        pf.first_line_indent = Cm(first_line_indent)
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold, color=color)
    return p


def add_image(doc, image_path, caption, source_name):
    """插入一张居中图片，并在下面加一行灰色说明。"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)

    run = p.add_run()
    # 先按最大宽度 15.5cm 计算；如果是竖图，高度可能超过一页，
    # 这时改为“最大高度 18cm”反推宽度，避免一张图占满整页。
    try:
        with Image.open(image_path) as im:
            width_px, height_px = im.size
        ratio = width_px / height_px if height_px else 1.5
        width_cm = IMAGE_WIDTH_CM
        height_cm = width_cm / ratio
        if height_cm > IMAGE_MAX_HEIGHT_CM:
            height_cm = IMAGE_MAX_HEIGHT_CM
            width_cm = height_cm * ratio
        run.add_picture(image_path, width=Cm(width_cm), height=Cm(height_cm))
    except Exception:
        # 万一图片读不了，退回固定宽度（至少不会崩）
        run.add_picture(image_path, width=Cm(IMAGE_WIDTH_CM))

    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(12)

    text = caption.strip() if caption else "资料图"
    # 如果 caption 里已经写了“来源：xxx”，就不再重复追加
    if source_name and source_name not in text and "来源：" not in text and "来源:" not in text:
        text = f"{text}（来源：{source_name}）"
    r = cap.add_run(text)
    set_run_font(r, size=CAPTION_SIZE, color=GRAY)


def parse_article(raw):
    """
    把纯文本拆成：标题、正文段落、旧参考资料（如果有）、声明。

    新格式的文章没有“参考资料”，只有标题、正文和一句短声明。
    为了兼容旧稿，如果还有“参考资料：”，也能正确拆开。
    """
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if not lines:
        return "", [], [], ""

    title = lines[0]

    ref_index = None
    disclaimer_index = None
    for i, line in enumerate(lines):
        if ref_index is None and re.match(r"^参考资料\s*[：:]", line):
            ref_index = i
        if disclaimer_index is None and line.startswith("声明："):
            disclaimer_index = i

    ends = [x for x in (ref_index, disclaimer_index, len(lines)) if x is not None]
    body_end = min(ends)
    body = lines[1:body_end]

    if ref_index is not None:
        ref_end = disclaimer_index if disclaimer_index is not None and disclaimer_index > ref_index else len(lines)
        refs = lines[ref_index + 1:ref_end]
    else:
        refs = []

    disclaimer = lines[disclaimer_index] if disclaimer_index is not None else ""
    return title, body, refs, disclaimer


def count_chars(paragraphs):
    """统计正文有效字数（去掉空白）。"""
    return len(re.sub(r"\s", "", "\n".join(paragraphs)))


def split_for_display(text, max_chars=200):
    """
    把一个长段落按句号/问号/叹号拆成 2～3 个短段，方便手机阅读。

    注意：只在“句末标点后面不是引号/括号”的位置拆，
    避免把 “……” 这类引语拆坏。
    """
    parts = re.split(r'(?<=[。！？])(?=[^”’」』】）)])', text)
    chunks = []
    current = ""
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if not current or len(current) + len(part) <= max_chars:
            current += part
        else:
            chunks.append(current)
            current = part
    if current:
        chunks.append(current)
    return chunks


def image_positions(n_images, n_paragraphs):
    """
    决定每张图插在第几段之后。

    例如 5 段正文：
        3 张图 -> 第 1、3、5 段后
        4 张图 -> 第 1、2、4、5 段后
        5 张图 -> 每段后各一张
    """
    if n_images <= 0 or n_paragraphs <= 0:
        return []

    if n_images == 1:
        return [max(1, n_paragraphs // 2)]
    if n_images == 2:
        return [1, n_paragraphs]
    if n_images == 3:
        return sorted({1, max(2, (n_paragraphs + 1) // 2), n_paragraphs})
    if n_images == 4:
        return sorted({
            1,
            max(2, n_paragraphs // 3),
            max(3, (2 * n_paragraphs) // 3),
            n_paragraphs,
        })

    # 5 张及以上：均匀分布，且不重复
    positions = []
    for i in range(1, n_images + 1):
        pos = round(i * n_paragraphs / n_images)
        pos = min(max(pos, 1), n_paragraphs)
        if pos not in positions:
            positions.append(pos)
    return positions


def build_docx(txt_path, images_path, out_path, rank, original_title):
    with open(txt_path, "r", encoding="utf-8") as f:
        raw = f.read()

    title, body, refs, disclaimer = parse_article(raw)
    if not title or not body:
        raise ValueError("文章为空，或第一行标题/正文格式不对")

    images = []
    if images_path and os.path.exists(images_path):
        with open(images_path, "r", encoding="utf-8") as f:
            images = json.load(f).get("images", [])

    doc = Document()

    # ---------- 页面设置 ----------
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.2)

    # ---------- 默认字体 ----------
    style = doc.styles["Normal"]
    style.font.name = FONT
    style.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    style.font.size = Pt(BODY_SIZE)

    # ---------- 标题 ----------
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(title)
    set_run_font(run, size=TITLE_SIZE, bold=True, color=TITLE_COLOR)

    # ---------- 标题下的小字 ----------
    body_chars = count_chars(body)
    meta_text = f"全文约 {body_chars} 字"
    if images:
        meta_text += f" · 配图 {len(images)} 张"
    add_text(
        doc,
        meta_text,
        size=META_SIZE,
        color=GRAY,
        align=WD_ALIGN_PARAGRAPH.LEFT,
        space_after=14,
        line_spacing=1.0,
    )

    # ---------- 正文 + 配图 ----------
    positions = image_positions(len(images), len(body))
    image_index = 0

    for paragraph_index, paragraph in enumerate(body, start=1):
        # 原文一段可能在 Word 里拆成 2～3 个短段，阅读更轻松
        for chunk in split_for_display(paragraph):
            add_text(
                doc,
                chunk,
                size=BODY_SIZE,
                line_spacing=1.5,
                space_after=8,
            )

        if paragraph_index in positions and image_index < len(images):
            image = images[image_index]
            add_image(
                doc,
                image["local_path"],
                image.get("caption", ""),
                image.get("source_name", ""),
            )
            image_index += 1

    # 如果还有没插完的图，补在正文最后
    while image_index < len(images):
        image = images[image_index]
        add_image(
            doc,
            image["local_path"],
            image.get("caption", ""),
            image.get("source_name", ""),
        )
        image_index += 1

    # ---------- 短声明（不再放参考资料） ----------
    add_text(
        doc,
        SHORT_DISCLAIMER,
        size=9,
        color=GRAY,
        align=WD_ALIGN_PARAGRAPH.LEFT,
        space_after=0,
        line_spacing=1.2,
    )

    # ---------- 文档属性（方便后续质检） ----------
    doc.core_properties.title = title
    doc.core_properties.subject = f"百度热榜第 {rank} 名"
    doc.core_properties.keywords = (
        f"rank={rank};body_chars={body_chars};images={len(images)}"
    )
    doc.core_properties.comments = original_title or ""

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    doc.save(out_path)

    print(f"已生成：{out_path}")
    print(f"  标题：{title}")
    print(f"  正文：{body_chars} 字，{len(body)} 段")
    print(f"  配图：{len(images)} 张")
    print(f"  参考资料：{len(refs)} 条")


def main():
    parser = argparse.ArgumentParser(description="生成头条风格新闻解读 docx")
    parser.add_argument("--txt", required=True, help="纯文本成稿")
    parser.add_argument("--images", default=None, help="图片清单 JSON")
    parser.add_argument("--out", required=True, help="输出 docx 路径")
    parser.add_argument("--rank", type=int, default=0, help="榜单排名")
    parser.add_argument("--original-title", default="", help="原始热点标题")
    args = parser.parse_args()

    build_docx(
        txt_path=args.txt,
        images_path=args.images,
        out_path=args.out,
        rank=args.rank,
        original_title=args.original_title,
    )


if __name__ == "__main__":
    main()
