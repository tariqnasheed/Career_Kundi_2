from __future__ import annotations

import re


def ensure_terminal_punctuation(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return t
    if t[-1] in (".", "!", "?"):
        return t
    return t + "."


def normalize_answer_paragraphs(paragraphs: list[str]) -> str:
    cleaned = []
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        paragraph = ensure_terminal_punctuation(paragraph)
        cleaned.append(paragraph)
    return "\n\n".join(cleaned)


def _collapse_role_skill_repeats(text: str, role: str, skill: str) -> str:
    out = text
    if role:
        out = re.sub(rf"\b{re.escape(role)}\b(?:\s+\b{re.escape(role)}\b)+", role, out, flags=re.I)
    if skill:
        out = re.sub(rf"\b{re.escape(skill)}\b(?:\s+\b{re.escape(skill)}\b)+", skill, out, flags=re.I)
    return out


def _tighten_sentences(text: str) -> str:
    out = text
    out = re.sub(r"For example,\s+(During|On|When|In)\b", lambda m: f"For example, {m.group(1).lower()}", out)
    out = re.sub(r"Core technical terms I must use in this context are [^.]+\.\s*", "", out, flags=re.I)
    out = re.sub(r"Key terms are [^.]+\.\s*", "", out, flags=re.I)
    out = re.sub(r"Key terms in this case were [^.]+\.\s*", "", out, flags=re.I)
    out = re.sub(r"\.\s*,", ",", out)
    out = re.sub(r"\.\.+", ".", out)
    out = re.sub(r"\s+\.", ".", out)
    out = re.sub(r"\s{2,}", " ", out)
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out


def compress_compiled_answer(
    answer: str,
    role: str,
    skill: str,
    *,
    min_words: int = 150,
    max_words: int = 500,
) -> tuple[str, bool]:
    """Compress only when above the flexible quality-first maximum (default 500 words)."""
    raw = (answer or "").strip()
    if not raw:
        return raw, False

    out = _collapse_role_skill_repeats(raw, role, skill)
    out = _tighten_sentences(out)
    words = out.split()
    if len(words) <= max_words:
        return out, True

    paras = [p.strip() for p in out.split("\n\n") if p.strip()]
    if len(paras) >= 3:
        middle = paras[1:-1]
        compressed_middle: list[str] = []
        seen: set[str] = set()
        for para in middle:
            key = para.lower()[:80]
            if key in seen and (
                "for compliance" in para.lower() or "i would evidence" in para.lower()
            ):
                continue
            seen.add(key)
            compressed_middle.append(para)
        paras = [paras[0], *compressed_middle, paras[-1]]
        out = normalize_answer_paragraphs(paras)

    words = out.split()
    if len(words) > max_words:
        blocks = [p for p in out.split("\n\n") if p.strip()]
        keep = max_words
        new_blocks: list[str] = []
        for block in blocks:
            bw = block.split()
            if keep <= 0:
                break
            if len(bw) <= keep:
                new_blocks.append(block)
                keep -= len(bw)
            else:
                new_blocks.append(" ".join(bw[:keep]).rstrip(" ,;:") + ".")
                keep = 0
        out = normalize_answer_paragraphs(new_blocks) if new_blocks else " ".join(words[:max_words]).rstrip(" ,;:") + "."

    accepted = len(out.split()) <= max_words
    return out, accepted
