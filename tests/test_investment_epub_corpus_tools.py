from __future__ import annotations

import json
import zipfile
from pathlib import Path

from scripts.investment_corpus_support import (
    _make_bridge_example,
    _make_local_examples,
    build_corpus,
    build_gemini_dataset,
    build_pseudonymized_corpus,
    estimate_token_count,
    extract_epub_text,
    parse_episode_number,
    select_ssot_dir,
)

CONTAINER_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml" />
  </rootfiles>
</container>
"""


def build_epub(
    epub_path: Path, *, manifest_items: list[tuple[str, str]], spine_ids: list[str], files: dict[str, str]
) -> None:
    opf_items = "\n".join(
        f'    <item id="{item_id}" href="{href}" media-type="application/xhtml+xml" />'
        for item_id, href in manifest_items
    )
    spine = "\n".join(f'    <itemref idref="{item_id}" />' for item_id in spine_ids)
    content_opf = f"""\
<?xml version="1.0" encoding="utf-8"?>
<package version="2.0" xmlns="http://www.idpf.org/2007/opf">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>test</dc:title>
    <dc:language>ko</dc:language>
  </metadata>
  <manifest>
{opf_items}
  </manifest>
  <spine>
{spine}
  </spine>
</package>
"""
    with zipfile.ZipFile(epub_path, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip")
        archive.writestr("META-INF/container.xml", CONTAINER_XML)
        archive.writestr("OEBPS/content.opf", content_opf)
        for relative_path, content in files.items():
            archive.writestr(relative_path, content)


def html_doc(body: str) -> str:
    return f"""\
<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>sample</title>
    <style>body {{ color: black; }}</style>
  </head>
  <body>
    {body}
  </body>
</html>
"""


def test_parse_episode_number_variants() -> None:
    assert parse_episode_number("1.epub") == 1
    assert parse_episode_number("606377_1.epub") == 1
    assert parse_episode_number("금수저 투자백서 10화.epub") == 10
    assert parse_episode_number("창업의 신 1.epub") == 1
    assert parse_episode_number("재벌집 망나니 7대독자_0001.epub") == 1


def test_select_ssot_dir_prefers_root_when_it_is_superset(tmp_path: Path) -> None:
    title_dir = tmp_path / "[연재]만렙요원 재벌이 되다"
    title_dir.mkdir()
    (title_dir / "만렙요원_epub").mkdir()
    for episode in range(1, 4):
        (title_dir / f"{episode}.epub").write_text("", encoding="utf-8")
    for episode in range(1, 3):
        (title_dir / "만렙요원_epub" / f"502268_{episode}.epub").write_text("", encoding="utf-8")

    selection = select_ssot_dir("만렙요원 재벌이 되다", title_dir)

    assert selection.is_root_selection is True
    assert selection.rule == "prefer-root-superset-or-equal"
    assert selection.ssot_epub_count == 3


def test_extract_epub_text_uses_spine_and_skips_front_matter(tmp_path: Path) -> None:
    epub_path = tmp_path / "창업의 신 1.epub"
    build_epub(
        epub_path,
        manifest_items=[
            ("id0", "Text/0.html"),
            ("section0001", "Text/section0001.htm"),
            ("id17", "Text/17.html"),
        ],
        spine_ids=["id0", "section0001", "id17"],
        files={
            "OEBPS/Text/0.html": html_doc("<p>표지</p>"),
            "OEBPS/Text/section0001.htm": html_doc(
                "<h1>1화</h1><p>사업이 무너진 날이었다.</p><p>하지만 그는 다시 시작했다.</p>" * 40
            ),
            "OEBPS/Text/17.html": html_doc(
                "<p>전자책 출간일 2016.11.19</p><p>펴낸이 홍길동</p><p>이메일 test@example.com</p>"
            ),
        },
    )

    extracted = extract_epub_text(epub_path)

    assert extracted.episode == 1
    assert extracted.content_entries == ["OEBPS/Text/section0001.htm"]
    assert "사업이 무너진 날이었다." in extracted.text
    assert "전자책 출간일" not in extracted.text


def test_extract_epub_text_dedupes_duplicate_content_documents(tmp_path: Path) -> None:
    epub_path = tmp_path / "김 대리는 벼락부자 1화.epub"
    body = "<p>주가가 출렁였지만 그는 침착했다.</p>" * 60
    build_epub(
        epub_path,
        manifest_items=[
            ("chapter1", "Text/chapter_1.xhtml"),
            ("section1", "Text/Section0001.xhtml"),
        ],
        spine_ids=["chapter1", "section1"],
        files={
            "OEBPS/Text/chapter_1.xhtml": html_doc(body),
            "OEBPS/Text/Section0001.xhtml": html_doc(body),
        },
    )

    extracted = extract_epub_text(epub_path)

    assert len(extracted.content_entries) == 1
    assert extracted.text.count("주가가 출렁였지만 그는 침착했다.") == 60


def test_make_local_examples_respect_paragraph_and_scene_boundaries() -> None:
    first_scene = ("첫 장면에서 그는 시장의 냄새를 맡았다. " * 45).strip()
    second_scene = ("두 번째 장면에서 거래 테이블이 뒤집혔다. " * 45).strip()
    third_scene = ("세 번째 장면에서 판이 다시 짜였다. " * 45).strip()
    examples = _make_local_examples(
        "\n\n".join([first_scene, "***", second_scene, third_scene]),
        prompt_tokens=estimate_token_count(first_scene),
        completion_tokens=estimate_token_count(second_scene),
        stride_tokens=10_000,
    )

    assert examples
    prompt, completion = examples[0]
    assert prompt.endswith("***")
    assert "두 번째 장면" not in prompt
    assert completion.startswith("두 번째 장면에서 거래 테이블이 뒤집혔다.")


def test_make_bridge_example_uses_tail_and_head_paragraph_windows() -> None:
    previous_text = "\n\n".join(
        [
            ("이전 화 초반 압박이 계속됐다. " * 30).strip(),
            ("이전 화 말미에 그는 최종 결정을 내렸다. " * 40).strip(),
        ]
    )
    next_text = "\n\n".join(
        [
            ("다음 화 오프닝에서 시장이 즉시 반응했다. " * 35).strip(),
            ("다음 화 후반에 새로운 적이 등장했다. " * 35).strip(),
        ]
    )

    example = _make_bridge_example(
        previous_text,
        next_text,
        prompt_tokens=estimate_token_count("이전 화 말미에 그는 최종 결정을 내렸다. " * 20),
        completion_tokens=estimate_token_count("다음 화 오프닝에서 시장이 즉시 반응했다. " * 20),
    )

    assert example is not None
    prompt, completion = example
    assert "이전 화 초반 압박이 계속됐다." not in prompt
    assert prompt.startswith("이전 화 말미에 그는 최종 결정을 내렸다.")
    assert completion.startswith("다음 화 오프닝에서 시장이 즉시 반응했다.")
    assert "다음 화 후반에 새로운 적이 등장했다." not in completion


def test_build_corpus_and_gemini_dataset(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    output_root = tmp_path / "output"
    titles = ["금수저 투자백서", "대기업 말단이 일을 잘함"]
    for title in titles:
        title_dir = source_root / f"[연재]{title}" / "연재이펍"
        title_dir.mkdir(parents=True)
        for episode in range(1, 3):
            build_epub(
                title_dir / f"{title} {episode}화.epub",
                manifest_items=[("chapter1", "Text/chapter_1.xhtml")],
                spine_ids=["chapter1"],
                files={
                    "OEBPS/Text/chapter_1.xhtml": html_doc(
                        f"<p>{title} {episode}화 시작.</p><p>" + ("투자와 사업의 흐름을 읽었다. " * 80) + "</p>"
                    )
                },
            )

    corpus_manifest = build_corpus(source_root, output_root, titles)
    assert corpus_manifest["summary"]["written_episode_count"] == 4
    assert (output_root / "manifest.json").exists()
    assert (output_root / "titles").exists()

    dataset_manifest = build_gemini_dataset(
        output_root,
        holdout_fraction=0.5,
        prompt_tokens=90,
        completion_tokens=90,
        stride_tokens=45,
        bridge_prompt_tokens=60,
        bridge_completion_tokens=70,
    )

    train_lines = (output_root / "gemini" / "train.jsonl").read_text(encoding="utf-8").strip().splitlines()
    val_lines = (output_root / "gemini" / "val.jsonl").read_text(encoding="utf-8").strip().splitlines()
    first_record = json.loads(train_lines[0])

    assert dataset_manifest["train_example_count"] > 0
    assert dataset_manifest["val_example_count"] > 0
    assert set(dataset_manifest["train_titles"]).isdisjoint(dataset_manifest["holdout_titles"])
    assert dataset_manifest["window_unit"] == "estimated_tokens"
    assert dataset_manifest["window_strategy"] == "paragraph_boundary_scene_aware"
    assert "systemInstruction" in first_record
    assert first_record["contents"][0]["role"] == "user"
    assert first_record["contents"][1]["role"] == "model"
    assert len(train_lines) == dataset_manifest["train_example_count"]
    assert len(val_lines) == dataset_manifest["val_example_count"]


def test_build_pseudonymized_corpus_rewrites_people_and_orgs(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    raw_root = tmp_path / "raw"
    pseudo_root = tmp_path / "pseudo"
    title = "금수저 투자백서"
    title_dir = source_root / f"[연재]{title}" / "연재이펍"
    title_dir.mkdir(parents=True)

    repeated_body = (
        "<p>강도윤은 태성그룹의 후계 구도를 냉정하게 읽었다.</p>"
        "<p>강도윤이 태성그룹 본사로 향하자 태성그룹 전략실이 술렁였다.</p>"
        "<p>강도윤은 결국 태성그룹 지분 구조를 뒤집겠다고 선언했다.</p>"
    )
    for episode in range(1, 3):
        build_epub(
            title_dir / f"{title} {episode}화.epub",
            manifest_items=[("chapter1", "Text/chapter_1.xhtml")],
            spine_ids=["chapter1"],
            files={"OEBPS/Text/chapter_1.xhtml": html_doc(repeated_body * 20)},
        )

    build_corpus(source_root, raw_root, [title])
    pseudo_manifest = build_pseudonymized_corpus(
        raw_root,
        pseudo_root,
        min_person_frequency=2,
        min_org_frequency=2,
    )

    pseudo_text = (pseudo_root / "titles" / "금수저_투자백서" / "0001.txt").read_text(encoding="utf-8")
    entity_map = json.loads((pseudo_root / "entity_map.json").read_text(encoding="utf-8"))
    title_map = entity_map["titles"][title]

    assert pseudo_manifest["summary"]["pseudonymized_title_count"] == 1
    assert "강도윤" in title_map["persons"]
    assert "태성그룹" in title_map["organizations"]
    assert "강도윤" not in pseudo_text
    assert "태성그룹" not in pseudo_text
    assert title_map["persons"]["강도윤"] in pseudo_text
    assert title_map["organizations"]["태성그룹"] in pseudo_text
