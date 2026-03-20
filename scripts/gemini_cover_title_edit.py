"""Edit a cover image by adding title typography via Gemini image models.

This script intentionally lives outside the main runtime. It loads `.env`,
uses the existing Google / Vertex credentials already used by the workspace,
and sends the base image plus an optional style reference image to Gemini's
native image generation / editing models.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image


DEFAULT_MODEL = "gemini-3.1-flash-image-preview"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Add Korean title typography to a cover image via Gemini image editing."
    )
    parser.add_argument("--input", required=True, help="Base cover image path.")
    parser.add_argument("--output", required=True, help="Output image path.")
    parser.add_argument("--title", required=True, help="Title text to place on the cover.")
    parser.add_argument(
        "--style-ref",
        default=None,
        help="Optional style reference image path. Use this when cloning a typography mood.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("GEMINI_IMAGE_MODEL", DEFAULT_MODEL),
        help=(
            "Gemini image model. Examples: gemini-3.1-flash-image-preview, "
            "gemini-3-pro-image-preview, gemini-2.5-flash-image."
        ),
    )
    parser.add_argument(
        "--provider",
        choices=("auto", "gemini", "vertex"),
        default="auto",
        help="Credential mode. auto prefers GOOGLE_API_KEY, then Vertex.",
    )
    parser.add_argument(
        "--placement",
        default="bottom area",
        help="Desired title placement, e.g. 'bottom area', 'bottom-left', 'top-center'.",
    )
    parser.add_argument(
        "--extra-prompt",
        default="",
        help="Extra prompt details appended to the base edit instruction.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Generation temperature.",
    )
    parser.add_argument(
        "--candidates",
        type=int,
        default=1,
        help="Number of image candidates to request.",
    )
    parser.add_argument(
        "--dry-run-prompt",
        action="store_true",
        help="Print the composed prompt without calling the API.",
    )
    return parser


def load_workspace_env() -> None:
    project_root = Path(__file__).resolve().parents[1]
    dotenv_path = project_root / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path, override=True)
    load_dotenv(override=True)


def build_client(provider: str) -> tuple[genai.Client, str]:
    google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    vertex_project = os.getenv("VERTEX_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    vertex_location = os.getenv("VERTEX_LOCATION") or os.getenv("GOOGLE_CLOUD_LOCATION")

    if provider in ("auto", "gemini") and google_api_key:
        return genai.Client(api_key=google_api_key), "gemini"

    if provider in ("auto", "vertex") and vertex_project and vertex_location:
        return (
            genai.Client(vertexai=True, project=vertex_project, location=vertex_location),
            "vertex",
        )

    raise RuntimeError(
        "No usable Google image credentials found. "
        "Set GOOGLE_API_KEY for Gemini Developer API, or set "
        "VERTEX_PROJECT_ID and VERTEX_LOCATION for Vertex AI."
    )


def build_prompt(title: str, placement: str, has_style_ref: bool, extra_prompt: str) -> str:
    prompt = f"""
You are editing a Korean webnovel cover image.

Task:
- Add exactly one Korean title: "{title}"
- Place the title in the {placement}
- Preserve the character identity, pose, costume, facial features, body proportions, camera framing, and overall cover composition
- Do not redraw the whole artwork unless needed for typography integration
- Do not add any extra words, logos, subtitles, issue numbers, signatures, or watermarks
- Make the title look professionally integrated into a commercial Korean cover, not like a flat overlay
- Maintain high legibility at thumbnail size
"""
    if has_style_ref:
        prompt += """
Reference handling:
- The first image is the base cover to edit
- The second image is a typography style reference
- Match the reference's general typography treatment, energy, stroke behavior, glow, layering, and placement logic
- Do not copy unrelated characters or non-title elements from the reference
"""
    prompt += """
Quality bar:
- The result should look like a finished published cover
- Keep the title crisp, balanced, and natural inside the scene
- Avoid malformed Korean glyphs, duplicated letters, broken spacing, or accidental extra characters
"""
    if extra_prompt.strip():
        prompt += f"\nExtra direction:\n- {extra_prompt.strip()}\n"
    return prompt.strip()


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
        raise RuntimeError("The model returned no image data.")

    return image_paths, text_path


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    load_workspace_env()

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    style_ref_path = Path(args.style_ref).expanduser().resolve() if args.style_ref else None

    if not input_path.exists():
        parser.error(f"--input not found: {input_path}")
    if style_ref_path and not style_ref_path.exists():
        parser.error(f"--style-ref not found: {style_ref_path}")

    prompt = build_prompt(
        title=args.title,
        placement=args.placement,
        has_style_ref=style_ref_path is not None,
        extra_prompt=args.extra_prompt,
    )

    if args.dry_run_prompt:
        print(prompt)
        return 0

    client, resolved_provider = build_client(args.provider)

    contents: list[object] = [prompt, Image.open(input_path)]
    if style_ref_path is not None:
        contents.append(Image.open(style_ref_path))

    config = types.GenerateContentConfig(
        responseModalities=[types.Modality.TEXT, types.Modality.IMAGE],
        temperature=args.temperature,
        candidateCount=args.candidates,
    )

    response = client.models.generate_content(
        model=args.model,
        contents=contents,
        config=config,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image_paths, text_path = save_response(output_path, response)

    print(f"provider={resolved_provider}")
    print(f"model={args.model}")
    for path in image_paths:
        print(f"image={path}")
    if text_path is not None:
        print(f"text={text_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
