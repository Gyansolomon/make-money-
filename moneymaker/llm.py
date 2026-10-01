"""Minimal LLM client: Gemini (free tier) or any OpenAI-compatible API."""

from __future__ import annotations

import json
import os
import re
import time

import requests


class LLMError(RuntimeError):
    pass


def available() -> str | None:
    if os.environ.get("GEMINI_API_KEY"):
        return "gemini"
    if os.environ.get("OPENAI_COMPAT_API_KEY"):
        return "openai"
    return None


def complete(prompt: str, provider: str | None = None, timeout: float = 120.0) -> str:
    provider = provider or available()
    if provider == "gemini":
        call = _gemini
    elif provider == "openai":
        call = _openai_compat
    else:
        raise LLMError("No LLM configured (set GEMINI_API_KEY or OPENAI_COMPAT_API_KEY)")
    last: Exception | None = None
    for attempt in range(3):
        try:
            return call(prompt, timeout)
        except (requests.RequestException, LLMError) as exc:
            last = exc
            time.sleep(2 ** (attempt + 1))  # free tiers rate-limit; back off
    raise LLMError(f"{provider} request failed: {last}")


def _gemini(prompt: str, timeout: float) -> str:
    model = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4, "responseMimeType": "application/json"},
        },
        timeout=timeout,
    )
    if resp.status_code != 200:
        raise LLMError(f"Gemini HTTP {resp.status_code}: {resp.text[:300]}")
    try:
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise LLMError(f"Unexpected Gemini response: {resp.text[:300]}") from exc


def _openai_compat(prompt: str, timeout: float) -> str:
    base = os.environ.get("OPENAI_COMPAT_BASE_URL", "https://api.deepseek.com").rstrip("/")
    resp = requests.post(
        f"{base}/chat/completions",
        headers={"Authorization": f"Bearer {os.environ['OPENAI_COMPAT_API_KEY']}"},
        json={
            "model": os.environ.get("OPENAI_COMPAT_MODEL", "deepseek-chat"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
            "response_format": {"type": "json_object"},
        },
        timeout=timeout,
    )
    if resp.status_code != 200:
        raise LLMError(f"LLM HTTP {resp.status_code}: {resp.text[:300]}")
    return resp.json()["choices"][0]["message"]["content"]


def parse_json(text: str):
    """Parse JSON from a model reply, tolerating code fences and surrounding prose."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        i, j = text.find(open_ch), text.rfind(close_ch)
        if i != -1 and j > i:
            try:
                return json.loads(text[i : j + 1])
            except json.JSONDecodeError:
                continue
    raise LLMError(f"Model did not return valid JSON: {text[:200]}")
