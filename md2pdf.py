"""Markdown to PDF converter with Korean font support + clickable TOC."""
import re
import sys
from pathlib import Path

from fpdf import FPDF
from PIL import Image


def normalize_heading_label(text):
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    text = text.replace("`", "").replace("**", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_toc_heading(title):
    normalized = normalize_heading_label(title)
    normalized = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", normalized)
    return normalized == "목차"


def heading_number_depth(title):
    normalized = normalize_heading_label(title)
    match = re.match(r"^(\d+(?:\.\d+)*)\b", normalized)
    if not match:
        return None
    return match.group(1).count(".") + 1


def is_qa_heading(title):
    normalized = normalize_heading_label(title)
    return re.match(r"^Q\d+\.", normalized, re.IGNORECASE) is not None


def convert(md_path, pdf_path):
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    md_dir = Path(md_path).resolve().parent
    pdf = FPDF()
    default_page_break_margin = 20
    summary_page_break_margin = 6
    default_margin_lr = 10
    default_margin_top = 10
    summary_margin_lr = 6
    summary_margin_top = 6
    pdf.set_margins(default_margin_lr, default_margin_top, default_margin_lr)
    pdf.set_auto_page_break(auto=True, margin=default_page_break_margin)

    # 한국어 폰트 등록
    pdf.add_font("Malgun", "", r"C:\Windows\Fonts\malgun.ttf", uni=True)
    pdf.add_font("Malgun", "B", r"C:\Windows\Fonts\malgunbd.ttf", uni=True)
    pdf.add_font("Consolas", "", r"C:\Windows\Fonts\consola.ttf", uni=True)

    # 1pass: heading 수집 + 링크 ID 미리 생성
    heading_links = {}  # normalized title -> link_id
    for line in lines:
        s = line.rstrip()
        for prefix in ("# ", "## ", "### ", "#### ", "##### "):
            if s.startswith(prefix):
                title = normalize_heading_label(s[len(prefix):].strip())
                heading_links[title] = pdf.add_link()
                break

    pdf.add_page()
    blank_page_content_len = len(pdf.pages[pdf.page].contents)
    pdf.set_font("Malgun", "", 10)

    in_toc = False
    toc_deferred = []  # (page, x, y, w, h, link_id) — 목차 링크 나중에 삽입
    links_set = set()  # set_link 완료된 title
    keep_next_h2_on_page = False
    after_pagebreak = False
    summary_mode = False

    def summary_tuned(default_value, summary_value):
        return summary_value if summary_mode else default_value

    def fit_col_widths(raw_widths, page_w, min_col_w):
        widths = [max(w, min_col_w) for w in raw_widths]
        total_w = sum(widths)
        if total_w > page_w:
            adjustable = [max(w - min_col_w, 0) for w in widths]
            adjustable_total = sum(adjustable)
            if adjustable_total > 0:
                deficit = total_w - page_w
                widths = [
                    w - (deficit * adj / adjustable_total) if adj > 0 else w
                    for w, adj in zip(widths, adjustable)
                ]
        widths[-1] += page_w - sum(widths)
        return widths

    def parse_table(table_lines):
        rows = []
        for line in table_lines:
            cells = [c.strip() for c in line.strip("|").split("|")]
            rows.append(cells)
        rows = [r for r in rows if not all(set(c.strip()) <= set("-: ") for c in r)]
        return rows

    def normalize_table_cell(cell_text):
        text = cell_text.strip()
        is_bold = False
        if text.startswith("**") and text.endswith("**") and len(text) >= 4:
            text = text[2:-2].strip()
            is_bold = True
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
        text = text.replace("`", "").replace("**", "")
        text = re.sub(r"\s+", " ", text).strip()
        return text, is_bold

    def draw_table(rows):
        if not rows:
            return
        num_cols = max(len(r) for r in rows)
        page_w = pdf.w - pdf.l_margin - pdf.r_margin

        table_font_size = summary_tuned(10.2, 6.9)
        header_h = summary_tuned(8.8, 4.8)
        cell_line_h = summary_tuned(6.2, 3.35)
        row_unit_h = summary_tuned(7.6, 3.8)
        if num_cols >= 6:
            table_font_size = summary_tuned(8.4, 6.6)
            header_h = summary_tuned(7.2, 4.5)
            cell_line_h = summary_tuned(5.0, 3.2)
            row_unit_h = summary_tuned(6.1, 3.6)

        pdf.set_font("Malgun", "", table_font_size)
        raw_widths = []
        for i in range(num_cols):
            col_texts = []
            for row in rows:
                if i < len(row):
                    col_texts.append(normalize_table_cell(row[i][:200])[0])
            measured = max((pdf.get_string_width(text) + 6 for text in col_texts), default=18)
            raw_widths.append(measured)
        if num_cols <= 2:
            min_col_w = page_w * 0.28
        elif num_cols == 3:
            min_col_w = page_w * 0.16
        elif num_cols == 4:
            min_col_w = page_w * 0.13
        else:
            min_col_w = page_w * 0.10
        col_widths = fit_col_widths(raw_widths, page_w, min_col_w)

        normalized_header = [normalize_table_cell(cell[:80])[0] for cell in rows[0]]
        normalized_rows = []
        for row in rows[1:]:
            normalized_row = []
            cell_heights = []
            for i, cell in enumerate(row):
                cell_text, is_bold = normalize_table_cell(cell[:200])
                normalized_row.append((cell_text, is_bold))
                sw = pdf.get_string_width(cell_text)
                usable_w = max(col_widths[i] - 2, 1)
                n_lines = max(1, int(sw / usable_w) + 1)
                cell_heights.append(n_lines)
            max_lines = max(cell_heights) if cell_heights else 1
            normalized_rows.append((normalized_row, row_unit_h * max_lines))

        def draw_header():
            pdf.set_font("Malgun", "B", table_font_size)
            pdf.set_fill_color(240, 240, 240)
            for col_w, cell_text in zip(col_widths, normalized_header):
                pdf.cell(col_w, header_h, cell_text, border=1, align="L", fill=True)
            pdf.ln()

        full_table_height = header_h + sum(row_h for _, row_h in normalized_rows)
        remaining_height = pdf.h - pdf.b_margin - pdf.get_y()
        page_capacity = pdf.h - pdf.t_margin - pdf.b_margin

        if full_table_height <= page_capacity and full_table_height > remaining_height:
            pdf.add_page()

        draw_header()

        for normalized_row, row_h in normalized_rows:
            if pdf.get_y() + row_h > pdf.h - pdf.b_margin:
                pdf.add_page()
                draw_header()

            y_before = pdf.get_y()
            x_cursor = pdf.l_margin
            for i in range(num_cols):
                cell_text, is_bold = normalized_row[i] if i < len(normalized_row) else ("", False)
                col_w = col_widths[i]
                pdf.rect(x_cursor, y_before, col_w, row_h)
                pdf.set_xy(x_cursor + 1, y_before + 1)
                pdf.set_font("Malgun", "B" if is_bold else "", table_font_size)
                pdf.multi_cell(col_w - 2, cell_line_h, cell_text, border=0)
                x_cursor += col_w
            pdf.set_y(y_before + row_h)
            pdf.set_font("Malgun", "", table_font_size)

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

    def match_heading_link(label):
        normalized = normalize_heading_label(label)
        if normalized in heading_links:
            return heading_links[normalized]
        for h_title, h_link in heading_links.items():
            if h_title in normalized or normalized in h_title:
                return h_link
        return None

    def bind_heading_link(title):
        normalized_title = normalize_heading_label(title)
        if normalized_title in heading_links:
            pdf.set_link(heading_links[normalized_title], y=pdf.get_y(), page=pdf.page_no())
            links_set.add(normalized_title)

    def should_render_toc_entry(label, level):
        if level == 0:
            return True
        depth = heading_number_depth(label)
        if depth is None:
            return level <= 1
        return depth <= 2

    def current_page_is_fresh():
        page_obj = pdf.pages.get(pdf.page)
        if page_obj is None:
            return False
        return len(page_obj.contents) <= blank_page_content_len

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
            pdf.set_font("Malgun", "", summary_tuned(8, 6.6))
            pdf.set_fill_color(245, 245, 245)
            pdf.cell(0, summary_tuned(5, 3.6), stripped, ln=True, fill=True)
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
            pdf.ln(summary_tuned(3, 0.8))
            continue

        if stripped == "<!-- KEEP_NEXT_H2_ON_PAGE -->":
            keep_next_h2_on_page = True
            continue

        if stripped == "<!-- PAGEBREAK -->":
            summary_mode = False
            pdf.set_margins(default_margin_lr, default_margin_top, default_margin_lr)
            pdf.set_auto_page_break(auto=True, margin=default_page_break_margin)
            top_threshold = getattr(pdf, "t_margin", 10) + 6
            if pdf.get_y() > top_threshold:
                pdf.add_page()
            in_toc = False
            after_pagebreak = True
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
            bind_heading_link(stripped[2:].strip())
            pdf.set_font("Malgun", "B", 16)
            pdf.multi_cell(0, 8.5, stripped[2:])
            pdf.ln(1)
            continue

        if stripped.startswith("## "):
            title = stripped[3:].strip()
            summary_mode = "1페이지 요약" in title
            if summary_mode:
                pdf.set_margins(summary_margin_lr, summary_margin_top, summary_margin_lr)
                pdf.set_auto_page_break(auto=True, margin=summary_page_break_margin)
            else:
                pdf.set_margins(default_margin_lr, default_margin_top, default_margin_lr)
                pdf.set_auto_page_break(auto=True, margin=default_page_break_margin)
            if is_toc_heading(title):
                in_toc = True
                if not current_page_is_fresh():
                    pdf.add_page()
                pdf.ln(4)
            else:
                in_toc = False
                if keep_next_h2_on_page:
                    keep_next_h2_on_page = False
                elif after_pagebreak:
                    after_pagebreak = False
                elif not current_page_is_fresh():
                    pdf.add_page()
                else:
                    after_pagebreak = False
            # 링크 대상 등록
            bind_heading_link(title)
            pdf.set_font("Malgun", "B", summary_tuned(14, 11.5))
            pdf.multi_cell(0, summary_tuned(8, 5.6), title)
            pdf.ln(summary_tuned(2, 0.8))
            continue

        if stripped.startswith("### "):
            in_toc = False
            title = stripped[4:].strip()
            if not is_qa_heading(title):
                pdf.ln(summary_tuned(2, 0.8))
                bind_heading_link(title)
                pdf.set_font("Malgun", "B", summary_tuned(12, 9.6))
                pdf.multi_cell(0, summary_tuned(7, 4.8), title)
                pdf.ln(summary_tuned(1, 0.3))
            else:
                pdf.ln(summary_tuned(1.6, 0.5))
                bind_heading_link(title)
                pdf.set_text_color(36, 71, 163)
                pdf.set_font("Malgun", "B", summary_tuned(11.4, 9.1))
                pdf.multi_cell(0, summary_tuned(6.6, 4.6), title)
                pdf.set_text_color(0, 0, 0)
                pdf.ln(summary_tuned(0.6, 0.2))
            continue
        if stripped.startswith("#### "):
            pdf.ln(summary_tuned(1, 0.5))
            bind_heading_link(stripped[5:].strip())
            pdf.set_font("Malgun", "B", summary_tuned(10, 8.5))
            pdf.multi_cell(0, summary_tuned(6, 4.2), stripped[5:])
            pdf.ln(summary_tuned(1, 0.2))
            continue
        if stripped.startswith("##### "):
            bind_heading_link(stripped[6:].strip())
            pdf.set_font("Malgun", "B", summary_tuned(10, 8.5))
            pdf.multi_cell(0, summary_tuned(6, 4.2), stripped[6:])
            pdf.ln(summary_tuned(1, 0.2))
            continue

        # 목차 영역의 리스트 → 클릭 가능 링크
        toc_bullet_match = re.match(r"^(\s*)[-*]\s+(.*)$", stripped)
        if in_toc and toc_bullet_match:
            indent_spaces = len(toc_bullet_match.group(1).replace("\t", "    "))
            level = indent_spaces // 2
            item_text = toc_bullet_match.group(2).strip()
            toc_label = item_text
            toc_link_target = item_text
            toc_match = re.match(r"^\[(.*?)\]\((.*?)\)$", item_text)
            if toc_match:
                toc_label = toc_match.group(1).strip()
                toc_link_target = toc_match.group(1).strip()
            toc_label = normalize_heading_label(toc_label)
            if not should_render_toc_entry(toc_label, level):
                continue
            matched_link = match_heading_link(toc_link_target)
            font_size = max(summary_tuned(10, 8.2) - (level * summary_tuned(0.55, 0.45)), summary_tuned(7.6, 6.4))
            line_h = max(summary_tuned(6, 4.4) - (level * summary_tuned(0.2, 0.15)), summary_tuned(4.2, 3.2))
            x_offset = pdf.l_margin + summary_tuned(5, 3) + (level * summary_tuned(4, 2.8))
            bullet = "\u2022 " if level == 0 else "- "
            pdf.set_font("Malgun", "B" if level == 0 else "", font_size)
            pdf.set_x(x_offset)
            if matched_link:
                pdf.set_text_color(0, 0, 180)
            x_before = pdf.get_x()
            y_before = pdf.get_y()
            pdf.cell(0, line_h, bullet + toc_label, ln=True)
            if matched_link:
                w = pdf.get_string_width(bullet + toc_label)
                toc_deferred.append((pdf.page_no(), x_before, y_before, w, line_h, matched_link))
                pdf.set_text_color(0, 0, 0)
            pdf.ln(summary_tuned(0.8, 0.2))
            continue

        # 인용
        if stripped.startswith("> "):
            pdf.set_font("Malgun", "", summary_tuned(9, 7.1))
            x_start = pdf.l_margin + summary_tuned(8, 4.5)
            y_top = pdf.get_y()
            pdf.set_x(x_start)
            pdf.multi_cell(0, summary_tuned(5, 3.35), stripped[2:])
            y_bottom = pdf.get_y()
            pdf.set_draw_color(150, 150, 150)
            pdf.line(pdf.l_margin + summary_tuned(4, 2.5), y_top, pdf.l_margin + summary_tuned(4, 2.5), y_bottom)
            pdf.set_draw_color(0, 0, 0)
            pdf.ln(summary_tuned(1, 0.2))
            continue

        # 리스트
        if stripped.startswith("- ") or stripped.startswith("* "):
            pdf.set_font("Malgun", "", summary_tuned(10, 7.7))
            pdf.set_x(pdf.l_margin + summary_tuned(5, 3))
            pdf.multi_cell(0, summary_tuned(5, 3.45), "\u2022 " + stripped[2:])
            pdf.ln(summary_tuned(1, 0.2))
            continue

        # 번호 리스트
        m = re.match(r"^(\d+)\.\s+", stripped)
        if m:
            pdf.set_font("Malgun", "", summary_tuned(10, 7.7))
            pdf.set_x(pdf.l_margin + summary_tuned(5, 3))
            pdf.multi_cell(0, summary_tuned(5, 3.45), stripped)
            pdf.ln(summary_tuned(1, 0.2))
            continue

        # 일반 텍스트
        text = stripped.replace("**", "").replace("`", "")
        pdf.set_font("Malgun", "", summary_tuned(10, 7.7))
        pdf.multi_cell(0, summary_tuned(5, 3.45), text)
        pdf.ln(summary_tuned(1, 0.2))

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
