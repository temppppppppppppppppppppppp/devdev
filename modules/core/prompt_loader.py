"""YAML-backed prompt loader with lightweight provenance support."""

import logging
import os
import sys
import threading
from pathlib import Path
from typing import Any, Optional


class SafeDict(dict):
    """Preserve unknown placeholders during format_map substitution."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


class PromptLoader:
    """Singleton loader for prompts under config/prompts."""

    _instance: Optional["PromptLoader"] = None
    _cache: dict[tuple[str, str], dict[str, str]] = {}
    _metadata_cache: dict[tuple[str, str], dict[str, Any]] = {}
    _instance_lock = threading.Lock()
    _cache_lock = threading.Lock()

    def __new__(cls) -> "PromptLoader":
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._cache = {}
                    cls._metadata_cache = {}
        return cls._instance

    def __init__(self) -> None:
        prompts_dir = self._find_prompts_dir()
        if hasattr(self, "_initialized"):
            if self._prompts_dir != prompts_dir:
                self._prompts_dir = prompts_dir
            return
        self._prompts_dir = prompts_dir
        self._initialized = True

    def _find_prompts_dir(self) -> Path:
        env_path = os.getenv("PROMPT_DIR")
        if env_path:
            return Path(env_path)

        if getattr(sys, "frozen", False):
            base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
            prompts_dir = base / "config" / "prompts"
            if prompts_dir.is_dir():
                return prompts_dir

        current = Path(__file__).resolve()
        project_root = current.parent.parent.parent
        return project_root / "config" / "prompts"

    def _load_yaml_file(self, domain: str) -> dict[str, str]:
        cache_key = (str(self._prompts_dir), domain)
        with self._cache_lock:
            if cache_key in self._cache:
                return self._cache[cache_key]

        yaml_path = self._prompts_dir / f"{domain}.yaml"
        if not yaml_path.exists():
            with self._cache_lock:
                self._cache[cache_key] = {}
            return {}

        prompts: dict[str, str] = {}
        try:
            import re

            key_pattern = re.compile(r"^([A-Z][A-Z0-9_]+):\s*\|")
            current_key: str | None = None
            current_lines: list[str] = []
            indent_size = 2

            with open(yaml_path, encoding="utf-8") as handle:
                all_lines = handle.readlines()

            for line in all_lines:
                raw = line.rstrip("\n\r")
                match = key_pattern.match(raw)
                if match:
                    if current_key is not None:
                        while current_lines and current_lines[-1] == "":
                            current_lines.pop()
                        prompts[current_key] = "\n".join(current_lines)
                    current_key = match.group(1)
                    current_lines = []
                    indent_size = 2
                    continue

                if current_key is None:
                    continue
                if raw.strip() == "":
                    current_lines.append("")
                    continue
                if raw.startswith(" " * indent_size):
                    current_lines.append(raw[indent_size:])
                elif raw.startswith(" ") or raw.startswith("\t"):
                    current_lines.append(raw.lstrip())
                else:
                    if raw.strip().startswith("#"):
                        continue
                    current_lines.append(raw)

            if current_key is not None:
                while current_lines and current_lines[-1] == "":
                    current_lines.pop()
                prompts[current_key] = "\n".join(current_lines)
        except Exception as exc:
            logging.warning("[PromptLoader] Failed to load %s: %s", yaml_path, exc)
            prompts = {}

        with self._cache_lock:
            self._cache[cache_key] = prompts
        return prompts

    def _load_yaml_metadata(self, domain: str) -> dict[str, Any]:
        cache_key = (str(self._prompts_dir), domain)
        with self._cache_lock:
            if cache_key in self._metadata_cache:
                return self._metadata_cache[cache_key]

        yaml_path = self._prompts_dir / f"{domain}.yaml"
        if not yaml_path.exists():
            with self._cache_lock:
                self._metadata_cache[cache_key] = {}
            return {}

        metadata: dict[str, Any] = {}
        try:
            import re

            meta_pattern = re.compile(r"^(_[A-Za-z0-9_]+):\s*(.+?)\s*$")
            with open(yaml_path, encoding="utf-8") as handle:
                for line in handle:
                    raw = line.rstrip("\n\r")
                    if not raw or raw.lstrip().startswith("#"):
                        continue
                    if raw.startswith(" ") or raw.startswith("\t"):
                        continue
                    match = meta_pattern.match(raw)
                    if not match:
                        continue
                    value = match.group(2).strip()
                    if value == "|":
                        continue
                    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                        value = value[1:-1]
                    metadata[match.group(1)] = value
        except Exception as exc:
            logging.warning("[PromptLoader] Failed to load metadata for %s: %s", yaml_path, exc)
            metadata = {}

        with self._cache_lock:
            self._metadata_cache[cache_key] = metadata
        return metadata

    def _format_template(self, template: str, *, domain: str, key: str, kwargs: dict[str, Any]) -> str:
        if kwargs:
            try:
                return template.format_map(SafeDict(**kwargs))
            except Exception as exc:
                logging.warning("[PromptLoader] Template substitution failed for %s/%s: %s", domain, key, exc)
        return template

    def load(self, domain: str, key: str, **kwargs: Any) -> str | None:
        prompts = self._load_yaml_file(domain)
        if key not in prompts:
            logging.debug("[PromptLoader] missing key %s/%s", domain, key)
            return None
        return self._format_template(prompts[key], domain=domain, key=key, kwargs=kwargs)

    def resolve_prompt(
        self,
        domain: str,
        key: str,
        *,
        fallback: str | None = None,
        fallback_source: str = "inline_fallback",
        **kwargs: Any,
    ) -> tuple[str | None, dict[str, Any]]:
        authoritative_source = f"config/prompts/{domain}.yaml:{key}"
        prompt_version = f"{domain}@{self.get_prompt_version(domain)}"
        prompt = self.load(domain, key, **kwargs)
        contract = {
            "domain": str(domain or "").strip(),
            "key": str(key or "").strip(),
            "authoritative_source": authoritative_source,
            "fallback_source": fallback_source if fallback is not None else "",
            "effective_source": "",
            "prompt_version": prompt_version,
            "used_fallback": False,
            "available": False,
            "effective_chars": 0,
        }
        if prompt is not None:
            contract["effective_source"] = authoritative_source
            contract["available"] = True
            contract["effective_chars"] = len(prompt)
            return prompt, contract
        if fallback is None:
            return None, contract

        resolved_fallback = self._format_template(fallback, domain=domain, key=key, kwargs=kwargs)
        contract["effective_source"] = fallback_source
        contract["used_fallback"] = True
        contract["available"] = True
        contract["effective_chars"] = len(resolved_fallback)
        return resolved_fallback, contract

    def get_prompt_contract(
        self,
        domain: str,
        key: str,
        *,
        fallback: str | None = None,
        fallback_source: str = "inline_fallback",
        **kwargs: Any,
    ) -> dict[str, Any]:
        _prompt, contract = self.resolve_prompt(
            domain,
            key,
            fallback=fallback,
            fallback_source=fallback_source,
            **kwargs,
        )
        return contract

    def get_raw(self, domain: str, key: str) -> str | None:
        prompts = self._load_yaml_file(domain)
        return prompts.get(key)

    def list_keys(self, domain: str) -> list[str]:
        return list(self._load_yaml_file(domain).keys())

    def get_metadata(self, domain: str) -> dict[str, Any]:
        return dict(self._load_yaml_metadata(domain))

    def get_prompt_version(self, domain: str, default: str = "unversioned") -> str:
        version = self._load_yaml_metadata(domain).get("_version")
        if version:
            return str(version)

        prompts = self._load_yaml_file(domain)
        if not prompts:
            return default

        import hashlib

        source = "\n".join(f"{key}:{prompts[key]}" for key in sorted(prompts))
        digest = hashlib.md5(source.encode("utf-8"), usedforsecurity=False).hexdigest()[:10]
        return f"hash:{digest}"

    def compose_version_tag(self, *domains: str) -> str:
        ordered_domains: list[str] = []
        for domain in domains:
            name = str(domain or "").strip()
            if name and name not in ordered_domains:
                ordered_domains.append(name)
        return "|".join(f"{domain}@{self.get_prompt_version(domain)}" for domain in ordered_domains)

    def invalidate_cache(self, domain: str | None = None) -> None:
        with self._cache_lock:
            if domain:
                keys_to_remove = [key for key in self._cache if key[1] == domain]
                for key in keys_to_remove:
                    del self._cache[key]
                meta_keys = [key for key in self._metadata_cache if key[1] == domain]
                for key in meta_keys:
                    del self._metadata_cache[key]
            else:
                self._cache.clear()
                self._metadata_cache.clear()
