from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.core.llm_generate import generate_content_via_router  # noqa: E402
from scripts.gold_manuscript_benchmark_support import (  # noqa: E402
    build_case_prompt,
    build_gold_package,
    run_gold_benchmark,
    write_json,
)
from scripts.investment_corpus_support import dump_json, slugify_title  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and optionally score a manuscript-only gold benchmark package.")
    parser.add_argument(
        "--input-root",
        required=True,
        help="Direct title dir or corpus root containing manifest.json / title subdirectories.",
    )
    parser.add_argument("--title", default=None, help="Exact title name when resolving from a corpus root.")
    parser.add_argument(
        "--output-root",
        default="data/gold_manuscript_benchmark",
        help="Output root for package and result JSON.",
    )
    parser.add_argument("--checkpoint-size", type=int, default=3, help="Number of episodes per checkpoint case.")
    parser.add_argument("--max-cases", type=int, default=5, help="Maximum number of benchmark cases to emit.")
    parser.add_argument("--genre", default="investment", help="Genre passed to the intrinsic scoring validator.")
    parser.add_argument(
        "--model",
        action="append",
        default=[],
        help="Optional model id to run. Repeat for multiple models, e.g. --model gemini-3.1-pro-preview --model gemini-2.5-pro",
    )
    parser.add_argument(
        "--candidate-dir",
        default=None,
        help="Optional directory containing <case_id>.txt candidate continuations.",
    )
    parser.add_argument(
        "--use-gold-candidate",
        action="store_true",
        help="Score each case against its own gold continuation as a pipeline self-check.",
    )
    parser.add_argument("--temperature", type=float, default=0.4, help="Sampling temperature for model runs.")
    parser.add_argument("--max-output-tokens", type=int, default=8192, help="Generation max_output_tokens.")
    return parser.parse_args()


def _load_api_client():
    dotenv_path = ROOT / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path, override=True)
    load_dotenv(override=True)

    google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if google_api_key:
        return genai.Client(api_key=google_api_key), "gemini"

    vertex_api_key = os.getenv("VERTEX_API_KEY")
    vertex_project = os.getenv("VERTEX_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    vertex_location = os.getenv("VERTEX_LOCATION") or os.getenv("GOOGLE_CLOUD_LOCATION")
    if vertex_api_key:
        return genai.Client(vertexai=True, api_key=vertex_api_key), "vertex"
    if vertex_project and vertex_location:
        return genai.Client(vertexai=True, project=vertex_project, location=vertex_location), "vertex"

    raise RuntimeError("No Gemini or Vertex credentials found. Set .env / env vars before model runs.")


def _run_model(output_root: Path, gold_package: dict, *, model: str, genre: str, temperature: float, max_output_tokens: int):
    client, provider = _load_api_client()
    model_slug = slugify_title(model)
    run_root = output_root / "model_runs" / model_slug
    candidate_dir = run_root / "candidates"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    generation_errors: list[dict[str, str]] = []

    for case in gold_package["cases"]:
        prompt = build_case_prompt(gold_package["title"], case)
        case_id = case["case_id"]
        candidate_path = candidate_dir / f"{case_id}.txt"
        try:
            response = generate_content_via_router(
                client=client,
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                ),
            )
            text = (response.text or "").strip()
            if not text:
                raise RuntimeError("empty response text")
            candidate_path.write_text(text + "\n", encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            generation_errors.append({"case_id": case_id, "error": str(exc)})

    result = run_gold_benchmark(gold_package, candidate_dir=candidate_dir, genre=genre)
    result["model"] = model
    result["provider"] = provider
    result["generation_errors"] = generation_errors
    result["temperature"] = temperature
    result["max_output_tokens"] = max_output_tokens
    result_path = run_root / "benchmark_result.json"
    write_json(result_path, result)
    return {"model": model, "result_path": result_path, "result": result}


def main() -> int:
    args = parse_args()
    gold_package = build_gold_package(
        Path(args.input_root),
        title=args.title,
        checkpoint_size=args.checkpoint_size,
        max_cases=args.max_cases,
    )
    output_root = Path(args.output_root) / slugify_title(gold_package["title"])
    package_path = output_root / "gold_package.json"
    write_json(package_path, gold_package)

    result_path = None
    result_payload = None
    if args.use_gold_candidate or args.candidate_dir:
        result_payload = run_gold_benchmark(
            gold_package,
            candidate_dir=Path(args.candidate_dir) if args.candidate_dir else None,
            use_gold_candidate=args.use_gold_candidate,
            genre=args.genre,
        )
        result_path = output_root / "benchmark_result.json"
        write_json(result_path, result_payload)

    model_runs = []
    if args.model:
        for model in args.model:
            model_runs.append(
                _run_model(
                    output_root,
                    gold_package,
                    model=model,
                    genre=args.genre,
                    temperature=args.temperature,
                    max_output_tokens=args.max_output_tokens,
                )
            )
        comparison = {
            "title": gold_package["title"],
            "title_slug": gold_package["title_slug"],
            "score_profile": "continuity-gold-relative-v2",
            "primary_score_axis": "continuity_index",
            "case_count": gold_package["case_count"],
            "models": [
                {
                    "model": item["model"],
                    "average_continuity_index": item["result"]["average_continuity_index"],
                    "average_continuity_score": item["result"]["average_continuity_score"],
                    "average_gold_continuity_score": item["result"]["average_gold_continuity_score"],
                    "average_gold_fidelity_score": item["result"]["average_gold_fidelity_score"],
                    "average_writing_quality_score": item["result"]["average_writing_quality_score"],
                    "average_legacy_blended_auto_score": item["result"]["average_legacy_blended_auto_score"],
                    "scored_case_count": item["result"]["scored_case_count"],
                    "missing_cases": item["result"]["missing_cases"],
                    "generation_error_count": len(item["result"].get("generation_errors", [])),
                    "result_path": item["result_path"].as_posix(),
                }
                for item in model_runs
            ],
        }
        write_json(output_root / "model_comparison.json", comparison)

    print(f"PACKAGE: {package_path.as_posix()}")
    if result_path is not None and result_payload is not None:
        print(f"RESULT: {result_path.as_posix()}")
        print(
            dump_json(
                {
                    "title": result_payload["title"],
                    "scored_case_count": result_payload["scored_case_count"],
                    "average_continuity_index": result_payload["average_continuity_index"],
                    "average_continuity_score": result_payload["average_continuity_score"],
                    "average_gold_continuity_score": result_payload["average_gold_continuity_score"],
                    "average_gold_fidelity_score": result_payload["average_gold_fidelity_score"],
                    "average_writing_quality_score": result_payload["average_writing_quality_score"],
                    "missing_cases": result_payload["missing_cases"],
                }
            )
        )
    elif model_runs:
        print(f"MODEL_COMPARISON: {(output_root / 'model_comparison.json').as_posix()}")
        print(
            dump_json(
                {
                    "title": gold_package["title"],
                    "models": [
                        {
                            "model": item["model"],
                            "average_continuity_index": item["result"]["average_continuity_index"],
                            "average_continuity_score": item["result"]["average_continuity_score"],
                            "average_gold_continuity_score": item["result"]["average_gold_continuity_score"],
                            "average_gold_fidelity_score": item["result"]["average_gold_fidelity_score"],
                            "average_writing_quality_score": item["result"]["average_writing_quality_score"],
                            "scored_case_count": item["result"]["scored_case_count"],
                            "generation_error_count": len(item["result"].get("generation_errors", [])),
                        }
                        for item in model_runs
                    ],
                }
            )
        )
    else:
        print(
            dump_json(
                {
                    "title": gold_package["title"],
                    "case_count": gold_package["case_count"],
                    "checkpoint_size": gold_package["checkpoint_size"],
                }
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
