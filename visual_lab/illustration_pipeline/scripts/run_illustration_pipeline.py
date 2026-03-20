from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a reference-driven illustration pipeline job.")
    parser.add_argument("--job", required=True, help="Path to job JSON.")
    parser.add_argument(
        "--reuse-existing",
        action="store_true",
        help="Reuse existing generated candidates instead of regenerating them.",
    )
    return parser


def workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_workspace_env() -> None:
    env_path = workspace_root() / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=True)
    load_dotenv(override=True)


def build_client() -> tuple[genai.Client, str]:
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if api_key:
        return genai.Client(api_key=api_key), "gemini"

    project = os.getenv("VERTEX_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("VERTEX_LOCATION") or os.getenv("GOOGLE_CLOUD_LOCATION")
    if project and location:
        return genai.Client(vertexai=True, project=project, location=location), "vertex"

    raise RuntimeError("No Google / Vertex credentials available.")


def load_job(job_path: Path) -> dict:
    return json.loads(job_path.read_text(encoding="utf-8"))


def ensure_output_dir(job: dict) -> Path:
    output_dir = Path(job["output_dir"]).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def iter_response_parts(response):
    parts = getattr(response, "parts", None)
    if parts:
        for part in parts:
            yield part
        return

    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        candidate_parts = getattr(content, "parts", None) or []
        for part in candidate_parts:
            yield part


def save_response(output_path: Path, response) -> tuple[list[Path], Path | None]:
    image_paths: list[Path] = []
    text_chunks: list[str] = []
    image_index = 0

    for part in iter_response_parts(response):
        text = getattr(part, "text", None)
        if text:
            text_chunks.append(text)
            continue
        inline_data = getattr(part, "inline_data", None)
        if inline_data is None:
            continue

        image_index += 1
        current_output = output_path
        if image_index > 1:
            current_output = output_path.with_name(
                f"{output_path.stem}_{image_index}{output_path.suffix}"
            )
        part.as_image().save(current_output)
        image_paths.append(current_output)

    text_path = None
    if text_chunks:
        text_path = output_path.with_suffix(".txt")
        text_path.write_text("\n\n".join(text_chunks).strip() + "\n", encoding="utf-8")

    if not image_paths:
        raise RuntimeError("Model returned no image data.")

    return image_paths, text_path


def generate_candidate(
    client: genai.Client,
    model: str,
    reference_image: Path,
    variant_prompt: str,
    output_path: Path,
    reuse_existing: bool,
) -> None:
    if reuse_existing and output_path.exists():
        return

    prompt = f"""
You are creating a polished Korean webnovel cover illustration.

Use the provided reference image only as inspiration for:
- dramatic composition
- central subject dominance
- commercial cover energy
- perspective intensity

Do not copy the original subject literally.
Create a new illustration.

Hard requirements:
- no text
- no logos
- no readable letters
- no watermark
- one premium finished illustration
- beautiful face and high-end anime illustration quality
- make it suitable for a top-tier romance fantasy cover

Variant direction:
{variant_prompt}
""".strip()

    response = client.models.generate_content(
        model=model,
        contents=[prompt, Image.open(reference_image)],
        config=types.GenerateContentConfig(
            responseModalities=[types.Modality.TEXT, types.Modality.IMAGE],
            temperature=0.35,
            candidateCount=1,
        ),
    )

    save_response(output_path, response)


def judge_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "ropan_style": {"type": "integer"},
            "beauty": {"type": "integer"},
            "polish": {"type": "integer"},
            "composition_impact": {"type": "integer"},
            "reference_energy_match": {"type": "integer"},
            "anatomy_integrity": {"type": "integer"},
            "text_cleanliness": {"type": "integer"},
            "has_unwanted_text": {"type": "boolean"},
            "issues": {"type": "array", "items": {"type": "string"}},
            "summary": {"type": "string"}
        },
        "required": [
            "ropan_style",
            "beauty",
            "polish",
            "composition_impact",
            "reference_energy_match",
            "anatomy_integrity",
            "text_cleanliness",
            "has_unwanted_text",
            "issues",
            "summary"
        ]
    }


def judge_candidate(
    client: genai.Client,
    judge_model: str,
    reference_image: Path,
    candidate_image: Path,
) -> dict:
    prompt = """
You are judging a Korean webnovel illustration candidate.

Inputs:
- first image: the original reference image
- second image: the generated candidate

Judge the second image only.

Scoring:
- ropan_style: 0-10 for premium romance-fantasy (로판) feel
- beauty: 0-10 for visual attractiveness of the main subject
- polish: 0-10 for finish quality and professional illustration feel
- composition_impact: 0-10 for cover-like impact and focal hierarchy
- reference_energy_match: 0-10 for matching the dramatic commercial energy of the reference
- anatomy_integrity: 0-10 for face/body/hands coherence
- text_cleanliness: 0-10, where 10 means absolutely no unwanted text or marks
- has_unwanted_text: true if there are any readable letters, pseudo-letters, logo-like marks, or watermark traces
- issues: short concrete flaws
- summary: one short strict assessment

Be strict. Penalize blandness, weak composition, cheap fantasy tropes, malformed hands, and any stray text.
""".strip()

    response = client.models.generate_content(
        model=judge_model,
        contents=[prompt, Image.open(reference_image), Image.open(candidate_image)],
        config=types.GenerateContentConfig(
            responseMimeType="application/json",
            responseSchema=judge_schema(),
            temperature=0.1,
        ),
    )
    data = json.loads((response.text or "").strip())
    data["candidate"] = str(candidate_image)
    data["score"] = (
        data["ropan_style"] * 3
        + data["beauty"] * 4
        + data["polish"] * 4
        + data["composition_impact"] * 3
        + data["reference_energy_match"] * 2
        + data["anatomy_integrity"] * 3
        + data["text_cleanliness"] * 4
        - (12 if data["has_unwanted_text"] else 0)
        - (min(len(data["issues"]), 3) * 2)
    )
    return data


def save_json(path: Path, payload: dict | list) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_summary(job: dict, results: list[dict], output_dir: Path) -> None:
    lines = [
        f"# Illustration Pipeline Summary: {job['job_id']}",
        "",
        f"- generation model: `{job['generation_model']}`",
        f"- judge model: `{job['judge_model']}`",
        f"- reference image: `{job['reference_image']}`",
        "",
        "## Ranking",
        "",
    ]
    for idx, item in enumerate(results, start=1):
        lines.extend(
            [
                f"### {idx}. {Path(item['candidate']).name}",
                f"- score: `{item['score']}`",
                f"- ropan_style: `{item['ropan_style']}`",
                f"- beauty: `{item['beauty']}`",
                f"- polish: `{item['polish']}`",
                f"- composition_impact: `{item['composition_impact']}`",
                f"- reference_energy_match: `{item['reference_energy_match']}`",
                f"- anatomy_integrity: `{item['anatomy_integrity']}`",
                f"- text_cleanliness: `{item['text_cleanliness']}`",
                f"- has_unwanted_text: `{item['has_unwanted_text']}`",
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
    client, provider = build_client()
    print(f"[provider] {provider}")

    job_path = Path(args.job).resolve()
    job = load_job(job_path)
    output_dir = ensure_output_dir(job)
    reference_image = Path(job["reference_image"]).resolve()

    candidates: list[Path] = []
    for idx, variant in enumerate(job["variants"], start=1):
        candidate_path = output_dir / f"candidate_{idx:02d}_{variant['name']}.png"
        print(f"[generate] {candidate_path.name}")
        generate_candidate(
            client=client,
            model=job["generation_model"],
            reference_image=reference_image,
            variant_prompt=variant["prompt"],
            output_path=candidate_path,
            reuse_existing=args.reuse_existing,
        )
        candidates.append(candidate_path)

    results: list[dict] = []
    for candidate in candidates:
        print(f"[judge] {candidate.name}")
        judged = judge_candidate(
            client=client,
            judge_model=job["judge_model"],
            reference_image=reference_image,
            candidate_image=candidate,
        )
        results.append(judged)
        save_json(output_dir / f"{candidate.stem}.judge.json", judged)

    results.sort(key=lambda item: item["score"], reverse=True)
    save_json(output_dir / "ranking.json", results)
    write_summary(job, results, output_dir)
    print(f"[best] {results[0]['candidate']} score={results[0]['score']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
