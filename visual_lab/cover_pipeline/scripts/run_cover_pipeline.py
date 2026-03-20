from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the cover AI pipeline for a job config.")
    parser.add_argument("--job", required=True, help="Path to a job JSON file.")
    parser.add_argument(
        "--reuse-existing",
        action="store_true",
        help="Reuse already-generated candidate images if present.",
    )
    return parser


def workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_workspace_env() -> None:
    env_path = workspace_root() / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=True)
    load_dotenv(override=True)


def load_job(job_path: Path) -> dict:
    return json.loads(job_path.read_text(encoding="utf-8"))


def ensure_output_dir(job: dict) -> Path:
    output_dir = Path(job["output_dir"]).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def generator_script() -> Path:
    return workspace_root() / "scripts" / "gemini_cover_title_edit.py"


def run_generator(job: dict, variant: dict, candidate_path: Path, reuse_existing: bool) -> None:
    if reuse_existing and candidate_path.exists():
        return

    cmd = [
        sys.executable,
        str(generator_script()),
        "--input",
        job["base_image"],
        "--output",
        str(candidate_path),
        "--title",
        job["title"],
        "--style-ref",
        job["style_reference"],
        "--placement",
        job["placement"],
        "--model",
        job["generation_model"],
        "--extra-prompt",
        (
            "Render the title text exactly as: "
            f"{job['title']}. "
            "Never misspell or replace any Korean syllable. "
            "Preserve the heroine completely. "
            + variant["extra_prompt"]
        ),
    ]
    subprocess.run(cmd, check=True)


def build_client() -> genai.Client:
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if api_key:
        return genai.Client(api_key=api_key)

    project = os.getenv("VERTEX_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("VERTEX_LOCATION") or os.getenv("GOOGLE_CLOUD_LOCATION")
    if project and location:
        return genai.Client(vertexai=True, project=project, location=location)

    raise RuntimeError("No Google / Vertex credentials available for judging.")


def judge_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "exact_title_match": {"type": "boolean"},
            "detected_title": {"type": "string"},
            "title_accuracy": {"type": "integer"},
            "style_match": {"type": "integer"},
            "character_preservation": {"type": "integer"},
            "cover_impact": {"type": "integer"},
            "readability": {"type": "integer"},
            "issues": {"type": "array", "items": {"type": "string"}},
            "summary": {"type": "string"},
        },
        "required": [
            "exact_title_match",
            "detected_title",
            "title_accuracy",
            "style_match",
            "character_preservation",
            "cover_impact",
            "readability",
            "issues",
            "summary",
        ],
    }


def judge_candidate(client: genai.Client, job: dict, candidate_path: Path) -> dict:
    prompt = f"""
You are judging a Korean webnovel cover candidate.

Inputs:
- First image: original base cover
- Second image: typography style reference
- Third image: candidate output

Evaluate the third image only.

Target title:
{job['title']}

Scoring rules:
- exact_title_match: true only if the candidate title is exactly "{job['title']}"
- detected_title: write the title you actually read from the candidate
- title_accuracy: 0-10, where any misspelled Korean syllable should score very low
- style_match: 0-10 against the typography mood of the reference image
- character_preservation: 0-10, based on whether the heroine stayed faithful to the base cover
- cover_impact: 0-10, based on whether this feels like a premium commercial webnovel cover
- readability: 0-10 at thumbnail scale
- issues: short concrete problems only
- summary: one short paragraph

Be strict. If the title is even slightly wrong, punish title_accuracy hard.
""".strip()

    response = client.models.generate_content(
        model=job["judge_model"],
        contents=[
            prompt,
            Image.open(job["base_image"]),
            Image.open(job["style_reference"]),
            Image.open(candidate_path),
        ],
        config=types.GenerateContentConfig(
            responseMimeType="application/json",
            responseSchema=judge_schema(),
            temperature=0.1,
        ),
    )

    text = (response.text or "").strip()
    data = json.loads(text)
    data["candidate"] = str(candidate_path)
    data["score"] = (
        data["title_accuracy"] * 4
        + data["style_match"] * 3
        + data["character_preservation"] * 2
        + data["cover_impact"] * 2
        + data["readability"] * 2
        + (10 if data["exact_title_match"] else 0)
        - (min(len(data["issues"]), 3) * 2)
    )
    return data


def save_json(path: Path, payload: dict | list) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_summary(job: dict, results: list[dict], output_dir: Path) -> None:
    lines = [
        f"# Cover AI Pipeline Summary: {job['job_id']}",
        "",
        f"- generation model: `{job['generation_model']}`",
        f"- judge model: `{job['judge_model']}`",
        f"- target title: `{job['title']}`",
        "",
        "## Ranking",
        "",
    ]
    for idx, item in enumerate(results, start=1):
        lines.extend(
            [
                f"### {idx}. {Path(item['candidate']).name}",
                f"- score: `{item['score']}`",
                f"- exact_title_match: `{item['exact_title_match']}`",
                f"- detected_title: `{item['detected_title']}`",
                f"- title_accuracy: `{item['title_accuracy']}`",
                f"- style_match: `{item['style_match']}`",
                f"- character_preservation: `{item['character_preservation']}`",
                f"- cover_impact: `{item['cover_impact']}`",
                f"- readability: `{item['readability']}`",
                f"- issues: `{'; '.join(item['issues'])}`",
                f"- summary: {item['summary']}",
                "",
            ]
        )
    (output_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    load_workspace_env()

    job_path = Path(args.job).resolve()
    job = load_job(job_path)
    output_dir = ensure_output_dir(job)

    candidates: list[Path] = []
    for idx, variant in enumerate(job["variants"], start=1):
        candidate_path = output_dir / f"candidate_{idx:02d}_{variant['name']}.png"
        print(f"[generate] {candidate_path.name}")
        run_generator(job, variant, candidate_path, args.reuse_existing)
        candidates.append(candidate_path)

    client = build_client()
    results: list[dict] = []
    for candidate in candidates:
        print(f"[judge] {candidate.name}")
        judged = judge_candidate(client, job, candidate)
        results.append(judged)
        save_json(output_dir / f"{candidate.stem}.judge.json", judged)

    results.sort(key=lambda item: item["score"], reverse=True)
    save_json(output_dir / "ranking.json", results)
    write_summary(job, results, output_dir)

    best = results[0]
    print(f"[best] {best['candidate']} score={best['score']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
