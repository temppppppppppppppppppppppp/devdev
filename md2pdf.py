"""Markdown to PDF converter with Korean font support + clickable TOC."""
import re
import sys
from pathlib import Path

from fpdf import FPDF
from PIL import Image


def convert(md_path, pdf_path):
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    md_dir = Path(md_path).resolve().parent
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    # 한국어 폰트 등록
    pdf.add_font("Malgun", "", r"C:\Windows\Fonts\malgun.ttf", uni=True)
    pdf.add_font("Malgun", "B", r"C:\Windows\Fonts\malgunbd.ttf", uni=True)
    pdf.add_font("Consolas", "", r"C:\Windows\Fonts\consola.ttf", uni=True)

    # 1pass: h2 헤딩 수집 + 링크 ID 미리 생성
    heading_links = {}  # title -> link_id
    for line in lines:
        s = line.rstrip()
        if s.startswith("## "):
            title = s[3:].strip()
            heading_links[title] = pdf.add_link()

    pdf.add_page()
    pdf.set_font("Malgun", "", 10)

    in_toc = False
    toc_deferred = []  # (page, x, y, w, h, link_id) — 목차 링크 나중에 삽입
    links_set = set()  # set_link 완료된 title
    keep_next_h2_on_page = False

    def parse_table(table_lines):
        rows = []
        for line in table_lines:
            cells = [c.strip() for c in line.strip("|").split("|")]
            rows.append(cells)
        rows = [r for r in rows if not all(set(c.strip()) <= set("-: ") for c in r)]
        return rows

    def draw_table(rows):
        if not rows:
            return
        num_cols = max(len(r) for r in rows)
        page_w = pdf.w - pdf.l_margin - pdf.r_margin
        col_w = page_w / num_cols

        pdf.set_font("Malgun", "B", 8)
        pdf.set_fill_color(240, 240, 240)
        for cell in rows[0]:
            pdf.cell(col_w, 7, cell[:80], border=1, align="L", fill=True)
        pdf.ln()

        pdf.set_font("Malgun", "", 8)
        for row in rows[1:]:
            cell_heights = []
            for i, cell in enumerate(row):
                sw = pdf.get_string_width(cell[:200])
                n_lines = max(1, int(sw / (col_w - 2)) + 1)
                cell_heights.append(n_lines)
            max_lines = max(cell_heights)
            h = 6 * max_lines

            if pdf.get_y() + h > pdf.h - pdf.b_margin:
                pdf.add_page()

            y_before = pdf.get_y()
            for i in range(num_cols):
                cell = row[i] if i < len(row) else ""
                x = pdf.l_margin + i * col_w
                pdf.rect(x, y_before, col_w, h)
                pdf.set_xy(x + 1, y_before + 1)
                pdf.multi_cell(col_w - 2, 5, cell[:200], border=0)
            pdf.set_y(y_before + h)

    def draw_image(alt_text, rel_path):
        width_scale = 1.0
        if "|w=" in rel_path:
            rel_path, width_hint = rel_path.rsplit("|w=", 1)
            try:
                width_scale = float(width_hint.strip())
            except ValueError:
                width_scale = 1.0
            width_scale = max(0.2, min(width_scale, 1.0))
        img_path = (md_dir / rel_path).resolve()
        if not img_path.exists():
            pdf.set_font("Malgun", "B", 9)
            pdf.set_text_color(180, 40, 40)
            pdf.multi_cell(0, 5, f"[이미지 누락] {rel_path}")
            pdf.set_text_color(0, 0, 0)
            pdf.ln(1)
            return

        with Image.open(img_path) as img:
            img_w_px, img_h_px = img.size

        max_w = pdf.w - pdf.l_margin - pdf.r_margin
        display_w = max_w * width_scale
        display_h = img_h_px * display_w / img_w_px
        caption_h = 6 if alt_text else 0
        required_h = display_h + caption_h + 4

        if pdf.get_y() + required_h > pdf.h - pdf.b_margin:
            pdf.add_page()

        y_before = pdf.get_y()
        x_before = pdf.l_margin + ((max_w - display_w) / 2)
        pdf.image(str(img_path), x=x_before, y=y_before, w=display_w)
        pdf.set_y(y_before + display_h + 2)

        if alt_text:
            pdf.set_font("Malgun", "", 8)
            pdf.set_text_color(90, 90, 90)
            pdf.multi_cell(0, 4, alt_text)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(1)

    in_code_block = False
    in_table = False
    table_lines = []

    for line in lines:
        stripped = line.rstrip()

        # 코드 블록
        if stripped.startswith("```"):
            if in_code_block:
                in_code_block = False
                pdf.ln(2)
            else:
                in_code_block = True
            continue

        if in_code_block:
            pdf.set_font("Malgun", "", 8)
            pdf.set_fill_color(245, 245, 245)
            pdf.cell(0, 5, stripped, ln=True, fill=True)
            continue

        # 테이블
        if "|" in stripped and stripped.strip().startswith("|"):
            if not in_table:
                in_table = True
                table_lines = []
            table_lines.append(stripped)
            continue
        elif in_table:
            rows = parse_table(table_lines)
            draw_table(rows)
            in_table = False
            table_lines = []

        # 빈 줄
        if not stripped:
            pdf.ln(3)
            continue

        if stripped == "<!-- KEEP_NEXT_H2_ON_PAGE -->":
            keep_next_h2_on_page = True
            continue

        if stripped == "<!-- PAGEBREAK -->":
            top_threshold = getattr(pdf, "t_margin", 10) + 6
            if pdf.get_y() > top_threshold:
                pdf.add_page()
            in_toc = False
            continue

        # 구분선
        if stripped == "---":
            y = pdf.get_y()
            pdf.set_draw_color(200, 200, 200)
            pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
            pdf.set_draw_color(0, 0, 0)
            pdf.ln(4)
            continue

        img_match = re.match(r"^!\[(.*?)\]\((.+)\)$", stripped)
        if img_match:
            draw_image(img_match.group(1).strip(), img_match.group(2).strip())
            continue

        # 헤딩
        if stripped.startswith("# "):
            pdf.set_font("Malgun", "B", 18)
            pdf.multi_cell(0, 10, stripped[2:])
            pdf.ln(2)
            continue

        if stripped.startswith("## "):
            title = stripped[3:].strip()
            if title == "목차":
                in_toc = True
                pdf.ln(4)
            else:
                in_toc = False
                if keep_next_h2_on_page:
                    keep_next_h2_on_page = False
                else:
                    pdf.add_page()
            # 링크 대상 등록
            if title in heading_links:
                pdf.set_link(heading_links[title], y=pdf.get_y(), page=pdf.page_no())
                links_set.add(title)
            pdf.set_font("Malgun", "B", 14)
            pdf.multi_cell(0, 8, title)
            pdf.ln(2)
            continue

        if stripped.startswith("### "):
            in_toc = False
            pdf.ln(2)
            pdf.set_font("Malgun", "B", 12)
            pdf.multi_cell(0, 7, stripped[4:])
            pdf.ln(1)
            continue
        if stripped.startswith("#### "):
            pdf.ln(1)
            pdf.set_font("Malgun", "B", 10)
            pdf.multi_cell(0, 6, stripped[5:])
            pdf.ln(1)
            continue
        if stripped.startswith("##### "):
            pdf.set_font("Malgun", "B", 10)
            pdf.multi_cell(0, 6, stripped[6:])
            pdf.ln(1)
            continue

        # 목차 영역의 리스트 → 클릭 가능 링크
        if in_toc and (stripped.startswith("- ") or stripped.startswith("* ")):
            item_text = stripped[2:].strip()
            # heading_links에서 매칭 찾기
            matched_link = None
            for h_title, h_link in heading_links.items():
                if h_title in item_text or item_text in h_title:
                    matched_link = h_link
                    break
            pdf.set_font("Malgun", "", 10)
            pdf.set_x(pdf.l_margin + 5)
            if matched_link:
                pdf.set_text_color(0, 0, 180)
            x_before = pdf.get_x()
            y_before = pdf.get_y()
            pdf.cell(0, 6, "\u2022 " + item_text, ln=True)
            if matched_link:
                w = pdf.get_string_width("\u2022 " + item_text)
                toc_deferred.append((pdf.page_no(), x_before, y_before, w, 6, matched_link))
                pdf.set_text_color(0, 0, 0)
            pdf.ln(1)
            continue

        # 인용
        if stripped.startswith("> "):
            pdf.set_font("Malgun", "", 9)
            x_start = pdf.l_margin + 8
            y_top = pdf.get_y()
            pdf.set_x(x_start)
            pdf.multi_cell(0, 5, stripped[2:])
            y_bottom = pdf.get_y()
            pdf.set_draw_color(150, 150, 150)
            pdf.line(pdf.l_margin + 4, y_top, pdf.l_margin + 4, y_bottom)
            pdf.set_draw_color(0, 0, 0)
            pdf.ln(1)
            continue

        # 리스트
        if stripped.startswith("- ") or stripped.startswith("* "):
            pdf.set_font("Malgun", "", 10)
            pdf.set_x(pdf.l_margin + 5)
            pdf.multi_cell(0, 5, "\u2022 " + stripped[2:])
            pdf.ln(1)
            continue

        # 번호 리스트
        m = re.match(r"^(\d+)\.\s+", stripped)
        if m:
            pdf.set_font("Malgun", "", 10)
            pdf.set_x(pdf.l_margin + 5)
            pdf.multi_cell(0, 5, stripped)
            pdf.ln(1)
            continue

        # 일반 텍스트
        text = stripped.replace("**", "").replace("`", "")
        pdf.set_font("Malgun", "", 10)
        pdf.multi_cell(0, 5, text)
        pdf.ln(1)

    # 마지막 테이블
    if in_table and table_lines:
        rows = parse_table(table_lines)
        draw_table(rows)

    # deferred 목차 링크 삽입
    for page, x, y, w, h, link_id in toc_deferred:
        pdf.page = page
        pdf.link(x, y, w, h, link_id)

    pdf.output(pdf_path)
    print(f"Done: {pdf_path}")


if __name__ == "__main__":
    if len(sys.argv) == 3:
        md_file = sys.argv[1]
        pdf_file = sys.argv[2]
    elif len(sys.argv) == 1:
        md_file = r"C:\Users\wjjo\Desktop\글도비\docs\2026-03-11\프로젝트승인요청서-글도비.md"
        pdf_file = r"C:\Users\wjjo\Desktop\글도비\docs\2026-03-11\프로젝트승인요청서-글도비.pdf"
    else:
        raise SystemExit("Usage: python md2pdf.py <input.md> <output.pdf>")
    convert(md_file, pdf_file)
