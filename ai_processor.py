"""
DeepSeek / Claude / Gemini / LM Studio 중 사용 가능한 AI로 텍스트를 처리하는 모듈.
우선순위: DeepSeek → Claude → Gemini → LM Studio (로컬)
"""
import os
import json
import urllib.request
import urllib.error


def _call_deepseek(prompt: str, system: str) -> str:
    api_key = os.environ["DEEPSEEK_API_KEY"]
    url = "https://api.deepseek.com/chat/completions"
    body = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 4096,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    })
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


def _call_claude(prompt: str, system: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def _call_gemini(prompt: str, system: str) -> str:
    api_key = os.environ["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    body = json.dumps({
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 4096},
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return data["candidates"][0]["content"]["parts"][0]["text"]


def _call_lmstudio(prompt: str, system: str) -> str:
    base_url = os.environ.get("LM_STUDIO_URL", "http://localhost:1234")
    url = f"{base_url}/v1/chat/completions"
    model = os.environ.get("LM_STUDIO_MODEL", "local-model")
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 4096,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


def generate(prompt: str, system: str = "당신은 제약회사 영업 전문가 어시스턴트입니다.") -> str:
    """사용 가능한 AI 엔진 순서대로 시도."""
    errors = []

    if os.environ.get("DEEPSEEK_API_KEY"):
        try:
            return _call_deepseek(prompt, system)
        except Exception as e:
            errors.append(f"DeepSeek: {e}")

    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return _call_claude(prompt, system)
        except Exception as e:
            errors.append(f"Claude: {e}")

    if os.environ.get("GEMINI_API_KEY"):
        try:
            return _call_gemini(prompt, system)
        except Exception as e:
            errors.append(f"Gemini: {e}")

    try:
        return _call_lmstudio(prompt, system)
    except Exception as e:
        errors.append(f"LM Studio: {e}")

    return f"[AI 처리 실패]\n" + "\n".join(errors)
