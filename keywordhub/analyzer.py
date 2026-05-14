from __future__ import annotations

import os
import re
import html as html_lib
import unicodedata
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from importlib.util import find_spec
from io import BytesIO
from pathlib import Path
from typing import Iterable

import numpy as np
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from docx import Document
except ImportError:  # pragma: no cover
    Document = None

try:
    from rake_nltk import Rake
except ImportError:  # pragma: no cover
    Rake = None


TOKEN_RE = re.compile(r"[^\W_]+(?:[ʻʼ’'`´‘ʹ′＇-][^\W_]+)*", re.UNICODE)
APOSTROPHE_RE = re.compile(r"[ʻʼ’`´‘ʹ′＇]")
SPACE_RE = re.compile(r"[\u00A0\u2007\u202F]")
SOFT_HYPHEN_RE = re.compile(r"[\u00AD\u200B\u200C\u200D]")
HTML_BLOCK_RE = re.compile(r"<\s*(script|style)[^>]*>.*?<\s*/\s*\1\s*>", re.IGNORECASE | re.DOTALL)
HTML_TAG_RE = re.compile(r"<[^>]+>")
HTML_ENTITY_RE = re.compile(r"&(?:[a-zA-Z][a-zA-Z0-9]+|#[0-9]+|#x[0-9a-fA-F]+);")
PHRASE_BREAK_RE = re.compile(r"\b(?:va|hamda|bilan|yoki|ammo|lekin)\b", re.IGNORECASE)

UZBEK_STOPWORDS = {
    "adi",
    "albatta",
    "alohida",
    "amalga",
    "ana",
    "avval",
    "ayni",
    "ba'zi",
    "balki",
    "va",
    "ham",
    "bu",
    "bunda",
    "buning",
    "bo'lib",
    "bo'yicha",
    "shu",
    "uchun",
    "bilan",
    "lekin",
    "ammo",
    "yoki",
    "hamda",
    "agar",
    "ekan",
    "edi",
    "etadi",
    "etgan",
    "etish",
    "etiladi",
    "bo'ladi",
    "bo'lgan",
    "bo'lsa",
    "bor",
    "bo'lgani",
    "bo'ylab",
    "davomida",
    "qiladi",
    "qilish",
    "qilib",
    "qilgan",
    "qaratilgan",
    "kerak",
    "kerakli",
    "so'ng",
    "yana",
    "juda",
    "eng",
    "bir",
    "ikki",
    "uch",
    "kabi",
    "sifatida",
    "orqali",
    "ichida",
    "ko'ra",
    "ko'proq",
    "ko'plab",
    "barcha",
    "har",
    "hech",
    "o'z",
    "ozi",
    "o'zi",
    "o'zida",
    "o'zining",
    "siz",
    "biz",
    "ular",
    "ularga",
    "ularning",
    "meni",
    "seni",
    "uni",
    "ularni",
    "unda",
    "uning",
    "hammasi",
    "hali",
    "hatto",
    "faqat",
    "turli",
    "yani",
    "ya'ni",
    "yoki",
    "yuzasidan",
    "mavjud",
    "mumkin",
    "muhim",
    "aria",
    "button",
    "class",
    "color",
    "data",
    "dataset",
    "display",
    "div",
    "false",
    "flex",
    "grid",
    "html",
    "input",
    "label",
    "markdown",
    "preview",
    "script",
    "span",
    "style",
    "true",
    "unsafe",
    "width",
    "kim",
    "nima",
    "qanday",
    "qachon",
    "qayerda",
    "nega",
}

RUSSIAN_STOPWORDS = {
    "и",
    "в",
    "во",
    "не",
    "что",
    "он",
    "на",
    "я",
    "с",
    "со",
    "как",
    "а",
    "то",
    "все",
    "она",
    "так",
    "его",
    "но",
    "да",
    "ты",
    "к",
    "у",
    "же",
    "вы",
    "за",
    "бы",
    "по",
    "только",
    "ее",
    "мне",
    "было",
    "вот",
    "от",
    "меня",
    "еще",
    "нет",
    "о",
    "из",
    "ему",
    "теперь",
    "когда",
    "даже",
    "ну",
    "вдруг",
    "ли",
    "если",
    "уже",
    "или",
    "ни",
    "быть",
    "был",
    "него",
    "до",
    "вас",
    "нибудь",
    "опять",
    "уж",
    "вам",
}

VERB_LIKE_SUFFIXES = (
    "adi",
    "ydi",
    "moqda",
    "yapti",
    "yotgan",
    "ayotgan",
    "lash",
    "lashtiradi",
    "tiradi",
    "qiladi",
    "etadi",
    "beradi",
    "ko'rsatadi",
    "yaratadi",
    "oshiradi",
    "rivojlantiradi",
    "kuchaytiradi",
)

MODIFIER_LIKE_SUFFIXES = (
    "iy",
    "li",
    "dor",
    "simon",
    "kor",
    "bop",
    "chan",
)

SUPPLEMENTARY_WORDS = {
    # About, regarding
    "haqida",
    "haqidagi",
    "haqdagi",
    # Size/quality descriptors
    "kichik",
    "katta",
    "uzoq",
    "qisqa",
    "yangi",
    "eski",
    "yaxshi",
    "yomon",
    # Directional/positional
    "tomonidan",
    "tomoni",
    "tomonida",
    "beri",
    "orta",
    "o'rta",
    "yuqori",
    "pastki",
    "chap",
    "o'ng",
    # Question-related
    "savol",
    "savolli",
    "savollash",
    # Other supplementary
    "kabi",
    "misol",
    "misoli",
    "sherchasi",
    "oʻrniga",
    "orniga",
    # More supplementary descriptors
    "soddalashtira",
    "murakkab",
    "oddiy",
    "xusus",
    "umumiy",
}

def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    normalized = SPACE_RE.sub(" ", normalized)
    normalized = SOFT_HYPHEN_RE.sub("", normalized)
    normalized = APOSTROPHE_RE.sub("'", normalized)
    return normalized.replace("\u02bb", "'").replace("\u2018", "'").replace("`", "'")


def _strip_markup_artifacts(text: str) -> str:
    unescaped = html_lib.unescape(text)
    unescaped = HTML_BLOCK_RE.sub(" ", unescaped)
    unescaped = HTML_TAG_RE.sub(" ", unescaped)
    unescaped = HTML_ENTITY_RE.sub(" ", unescaped)
    unescaped = re.sub(r"\b[\w-]+\s*=\s*(['\"]).*?\1", " ", unescaped)
    unescaped = re.sub(r"[{}<>/\\=;]", " ", unescaped)
    return unescaped


def _normalize_token(token: str) -> str:
    return _normalize_text(token).strip("-'").lower()


STOPWORDS = {_normalize_token(word) for word in (set(ENGLISH_STOP_WORDS) | UZBEK_STOPWORDS | RUSSIAN_STOPWORDS)}
CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache" / "huggingface"


@dataclass
class KeywordItem:
    term: str
    score: float
    source: str


@dataclass
class AnalysisResult:
    total_words: int
    unique_words: int
    top_keywords: list[KeywordItem]
    top_ngrams: list[KeywordItem]
    top_phrases: list[KeywordItem]
    cleaned_text: str


def tokenize(text: str) -> list[str]:
    normalized = _normalize_text(_strip_markup_artifacts(text))
    tokens = [_normalize_token(match.group(0)) for match in TOKEN_RE.finditer(normalized)]
    return [token for token in tokens if len(token) > 1 and token not in STOPWORDS]


def _looks_verb_like(token: str) -> bool:
    return any(token.endswith(suffix) for suffix in VERB_LIKE_SUFFIXES)


def _looks_modifier_like(token: str) -> bool:
    return any(token.endswith(suffix) for suffix in MODIFIER_LIKE_SUFFIXES)


def _is_supplementary_keyword(term: str) -> bool:
    """Check if a keyword contains supplementary/auxiliary words that should be filtered."""
    parts = term.lower().split()
    for part in parts:
        normalized_part = _normalize_token(part)
        
        # Check for exact matches
        if normalized_part in SUPPLEMENTARY_WORDS:
            return True
        
        # Check if normalized part starts with any supplementary word
        # This handles variants like "haqida" -> "haqidagi", "haqidasi", etc.
        for supp_word in SUPPLEMENTARY_WORDS:
            if normalized_part.startswith(supp_word) and len(normalized_part) > len(supp_word):
                # Only filter if it seems like an actual variant (has suffix)
                suffix = normalized_part[len(supp_word):]
                # Common Uzbek suffixes that create variants
                if suffix in {'gi', 'si', 'ni', 'da', 'ga', 'dan', 'adan', 'nan', 'tan', 'ing', 'ngiz', 'ning', 'ringiz',
                               'lari', 'lash', 'lar', 'lik', 'li', 'lig', 'siz', 'dir', 'roq', 'dilar', 'xona', 'xonada', 
                               'mi', 'yotgan', 'yay', 'iyor', 'il', 'ili', 'ini', 'lar', 'sing', 'singiz', 'ka', 'qa', 
                               'chi', 'chiga', 'chilar', 'chisi', 'likcha', 'likchi', 'sizning', 'miz', 'nning'}:
                    return True
    
    return False


def _filter_keywords(items: list[KeywordItem]) -> list[KeywordItem]:
    """Filter out keywords containing supplementary words."""
    return [item for item in items if not _is_supplementary_keyword(item.term)]


def _phrase_naturalness(parts: list[str], first_index: int, total_tokens: int, count: int) -> float:
    avg_length = sum(len(part) for part in parts) / max(len(parts), 1)
    position_score = max(0.0, 1.0 - (first_index / max(total_tokens, 1)))
    repetition_bonus = min(count, 3) * 0.42
    size_bonus = 0.62 if len(parts) == 2 else 0.46
    length_bonus = min(avg_length / 10, 1.0) * 0.28
    uniqueness_bonus = (len(set(parts)) / max(len(parts), 1)) * 0.24

    final_penalty = 0.48 if _looks_verb_like(parts[-1]) else 0.0
    middle_penalty = 0.24 if len(parts) == 3 and _looks_verb_like(parts[1]) else 0.0
    opening_penalty = 0.12 if _looks_verb_like(parts[0]) else 0.0
    order_bonus = 0.26 if _looks_modifier_like(parts[0]) and len(parts) >= 2 else 0.0
    order_penalty = 0.34 if len(parts) >= 2 and _looks_modifier_like(parts[-1]) else 0.0
    middle_modifier_penalty = 0.16 if len(parts) == 3 and _looks_modifier_like(parts[1]) else 0.0

    return (
        repetition_bonus
        + size_bonus
        + length_bonus
        + (position_score * 0.26)
        + uniqueness_bonus
        + order_bonus
        - final_penalty
        - middle_penalty
        - opening_penalty
        - order_penalty
        - middle_modifier_penalty
    )


def _collect_phrase_candidates(text: str, sizes: tuple[int, ...] = (2, 3)) -> tuple[dict[str, dict], int]:
    candidates: dict[str, dict] = {}
    token_offset = 0

    for sentence in re.split(r"[.!?\n;:]+", text):
        for clause in re.split(r"[,()]+", sentence):
            for span in re.split(PHRASE_BREAK_RE, clause):
                tokens = tokenize(span)
                if len(tokens) < min(sizes, default=2):
                    token_offset += len(tokens)
                    continue
                for size in sizes:
                    if len(tokens) < size:
                        continue
                    for index in range(len(tokens) - size + 1):
                        parts = tokens[index : index + size]
                        if min(len(part) for part in parts) < 4:
                            continue
                        if len(set(parts)) < len(parts):
                            continue
                        phrase = " ".join(parts)
                        item = candidates.setdefault(
                            phrase,
                            {
                                "parts": parts,
                                "size": size,
                                "count": 0,
                                "first_index": token_offset + index,
                            },
                        )
                        item["count"] += 1
                        item["first_index"] = min(item["first_index"], token_offset + index)
                token_offset += len(tokens)

    return candidates, max(token_offset, 1)


def extract_text_from_file(name: str, data: bytes) -> str:
    suffix = Path(name).suffix.lower()
    if suffix in {".txt", ".md", ".csv"}:
        return data.decode("utf-8", errors="ignore")
    if suffix == ".docx":
        if not Document:
            raise ValueError("Word fayllari uchun python-docx kutubxonasi kerak.")
        document = Document(BytesIO(data))
        parts = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
        return "\n".join(parts)
    raise ValueError("Faqat .txt, .md, .csv va .docx fayllar qo'llab-quvvatlanadi.")


def _build_frequency_keywords(tokens: list[str], top_k: int) -> list[KeywordItem]:
    counts = Counter(tokens)
    total = sum(counts.values()) or 1
    return [
        KeywordItem(term=term, score=round(count / total, 4), source="frequency")
        for term, count in counts.most_common(top_k)
    ]


def _build_tfidf_keywords(text: str, top_k: int) -> list[KeywordItem]:
    if not text.strip():
        return []
    try:
        vectorizer = TfidfVectorizer(
            tokenizer=tokenize,
            preprocessor=_normalize_text,
            token_pattern=None,
            lowercase=False,
            ngram_range=(1, 1),
            sublinear_tf=True,
        )
        matrix = vectorizer.fit_transform([text])
        features = vectorizer.get_feature_names_out()
        scores = matrix.toarray()[0]
        positive_scores = [float(score) for score in scores if score > 0]
        if positive_scores and max(positive_scores) - min(positive_scores) < 1e-9:
            return []
        pairs = sorted(zip(features, scores), key=lambda item: item[1], reverse=True)
        return [
            KeywordItem(term=term, score=round(float(score), 4), source="tfidf")
            for term, score in pairs[:top_k]
            if score > 0
        ]
    except ValueError:
        return []


def _build_ngram_keywords(text: str, top_k: int) -> list[KeywordItem]:
    if not text.strip():
        return []
    candidates: Counter[str] = Counter()
    first_seen: dict[str, int] = {}
    token_offset = 0

    for sentence in re.split(r"[.!?\n;:]+", text):
        sentence_tokens = tokenize(sentence)
        if len(sentence_tokens) < 2:
            token_offset += len(sentence_tokens)
            continue
        size = 2
        for index in range(len(sentence_tokens) - size + 1):
            parts = sentence_tokens[index : index + size]
            if min(len(part) for part in parts) < 4:
                continue
            term = " ".join(parts)
            candidates[term] += 1
            first_seen.setdefault(term, token_offset + index)
        token_offset += len(sentence_tokens)

    if not candidates:
        return []

    scored: list[tuple[str, float]] = []
    total_tokens = max(token_offset, 1)
    for term, count in candidates.items():
        parts = term.split()
        length_score = sum(len(part) for part in parts) / (len(parts) * 12)
        position_score = max(0.0, 1.0 - (first_seen[term] / total_tokens))
        score = count + (length_score * 0.35) + (position_score * 0.3)
        scored.append((term, score))

    ranked = sorted(scored, key=lambda item: (item[1], len(item[0])), reverse=True)
    return [
        KeywordItem(term=term, score=round(float(score), 4), source="ngram")
        for term, score in ranked[:top_k]
    ]


def _build_rake_phrases(text: str, top_k: int) -> list[KeywordItem]:
    if not Rake or not text.strip():
        return []
    try:
        rake = Rake(stopwords=list(STOPWORDS))
        rake.extract_keywords_from_text(_normalize_text(text))
        phrases = rake.get_ranked_phrases_with_scores()
    except LookupError:
        return []
    return [
        KeywordItem(term=phrase, score=round(float(score), 4), source="rake")
        for score, phrase in phrases[:top_k]
    ]


def _build_keybert_phrases(text: str, top_k: int) -> list[KeywordItem]:
    if not text.strip():
        return []
    if find_spec("torch") is None or find_spec("torchvision") is None:
        return []
    if find_spec("sentence_transformers") is None:
        return []
    try:
        model = _get_semantic_model()
        candidate_map, total_tokens = _collect_phrase_candidates(text, sizes=(2, 3))
        ranked_candidates = _semantic_candidates(candidate_map, total_tokens, top_k=max(top_k * 4, 20))
        if not ranked_candidates:
            return []
        candidate_terms = [term for term, _ in ranked_candidates]
        doc_embedding = model.encode([_normalize_text(text)], show_progress_bar=False)
        phrase_embeddings = model.encode(candidate_terms, show_progress_bar=False)
        similarities = cosine_similarity(
            np.asarray(doc_embedding),
            np.asarray(phrase_embeddings),
        )[0]
    except Exception:
        return []

    scored: list[tuple[str, float]] = []
    max_base = max((base for _, base in ranked_candidates), default=1.0)
    for (phrase, base_score), similarity in zip(ranked_candidates, similarities):
        combined = (float(similarity) * 2.4) + ((base_score / max_base) * 1.6)
        scored.append((phrase, combined))

    ranked = sorted(scored, key=lambda item: item[1], reverse=True)
    return [
        KeywordItem(term=phrase, score=round(float(score), 4), source="semantic")
        for phrase, score in ranked[:top_k]
    ]


@lru_cache(maxsize=1)
def _get_semantic_model():
    os.environ.setdefault("HF_HOME", str(CACHE_DIR))
    os.environ.setdefault("TRANSFORMERS_CACHE", str(CACHE_DIR))
    os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", str(CACHE_DIR))
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", cache_folder=str(CACHE_DIR))


def _semantic_candidates(candidate_map: dict[str, dict], total_tokens: int, top_k: int) -> list[tuple[str, float]]:
    ranked: list[tuple[str, float]] = []
    for phrase, meta in candidate_map.items():
        parts = list(meta["parts"])
        base_score = _phrase_naturalness(parts, int(meta["first_index"]), total_tokens, int(meta["count"]))
        semantic_bonus = 0.22 if len(parts) == 2 else 0.14
        ranked.append((phrase, base_score + semantic_bonus))

    ranked.sort(key=lambda item: (item[1], -len(item[0].split()), len(item[0])), reverse=True)
    return ranked[:top_k]


def _build_simple_phrases(text: str, top_k: int) -> list[KeywordItem]:
    candidate_map, total_tokens = _collect_phrase_candidates(text, sizes=(2, 3))
    ranked = sorted(
        (
            (
                phrase,
                _phrase_naturalness(
                    list(meta["parts"]),
                    int(meta["first_index"]),
                    total_tokens,
                    int(meta["count"]),
                ),
            )
            for phrase, meta in candidate_map.items()
        ),
        key=lambda item: (item[1], -len(item[0].split()), len(item[0])),
        reverse=True,
    )
    return [
        KeywordItem(term=term, score=round(float(score), 4), source="fallback")
        for term, score in ranked[:top_k]
    ]


def _build_supported_keywords(
    tokens: list[str],
    ngrams: Iterable[KeywordItem],
    phrases: Iterable[KeywordItem],
    top_k: int,
) -> list[KeywordItem]:
    if not tokens:
        return []

    scores: dict[str, float] = {}
    counts = Counter(tokens)
    max_count = max(counts.values()) or 1
    first_index: dict[str, int] = {}
    for index, token in enumerate(tokens):
        first_index.setdefault(token, index)

    for term, count in counts.items():
        position_boost = max(0.0, 1.0 - (first_index[term] / max(len(tokens), 1)))
        length_boost = min(len(term), 12) / 24
        scores[term] = (count / max_count) + (position_boost * 0.35) + (length_boost * 0.2)

    for item in list(ngrams) + list(phrases):
        parts = tokenize(item.term)
        if not parts:
            continue
        source_weight = 0.18 if item.source == "ngram" else 0.24
        bonus = source_weight / max(len(parts), 1)
        for part in parts:
            scores[part] = scores.get(part, 0.0) + bonus

    ranked = sorted(scores.items(), key=lambda item: (item[1], len(item[0])), reverse=True)
    return [
        KeywordItem(term=term, score=round(float(score), 4), source="context")
        for term, score in ranked[:top_k]
    ]


def merge_keywords(*groups: Iterable[KeywordItem], top_k: int = 20) -> list[KeywordItem]:
    merged: dict[str, float] = {}
    sources: dict[str, set[str]] = {}
    for group in groups:
        for item in group:
            merged[item.term] = merged.get(item.term, 0.0) + item.score
            sources.setdefault(item.term, set()).add(item.source)
    ranked = sorted(merged.items(), key=lambda item: item[1], reverse=True)[:top_k]
    return [
        KeywordItem(term=term, score=round(score, 4), source=", ".join(sorted(sources[term])))
        for term, score in ranked
    ]


def analyze_text(text: str, top_k: int = 20, method: str = "TF-IDF") -> AnalysisResult:
    cleaned_text = " ".join(_normalize_text(_strip_markup_artifacts(text)).split())
    tokens = tokenize(cleaned_text)
    
    if method == "TF-IDF":
        keywords = _build_tfidf_keywords(cleaned_text, top_k)
    elif method == "N-gram":
        keywords = _build_ngram_keywords(cleaned_text, top_k)
    elif method == "TextRank":
        keywords = merge_keywords(
            _build_keybert_phrases(cleaned_text, top_k),
            _build_tfidf_keywords(cleaned_text, top_k),
            top_k=top_k,
        )
    elif method == "YAKE":
        keywords = _build_frequency_keywords(tokens, top_k)
    elif method == "RAKE":
        keywords = _build_rake_phrases(cleaned_text, top_k)
    else:
        # Default: combine all methods
        freq_keywords = _build_frequency_keywords(tokens, top_k)
        tfidf_keywords = _build_tfidf_keywords(cleaned_text, top_k)
        supported_keywords = _build_supported_keywords(tokens, _build_ngram_keywords(cleaned_text, top_k), [], top_k)
        keywords = merge_keywords(freq_keywords, tfidf_keywords, supported_keywords, top_k=top_k)
    
    ngrams = _build_ngram_keywords(cleaned_text, top_k)
    phrases = merge_keywords(
        _build_rake_phrases(cleaned_text, top_k),
        _build_keybert_phrases(cleaned_text, top_k),
        _build_simple_phrases(cleaned_text, top_k),
        top_k=top_k,
    )
    
    # Filter out supplementary keywords
    filtered_keywords = _filter_keywords(keywords)
    filtered_ngrams = _filter_keywords(ngrams)
    filtered_phrases = _filter_keywords(phrases)
    
    # Ensure we still have enough results
    if len(filtered_keywords) < top_k:
        if method == "TF-IDF":
            keywords_extra = _build_tfidf_keywords(cleaned_text, top_k * 2)
        elif method == "N-gram":
            keywords_extra = _build_ngram_keywords(cleaned_text, top_k * 2)
        elif method == "RAKE":
            keywords_extra = _build_rake_phrases(cleaned_text, top_k * 2)
        else:
            freq_keywords_extra = _build_frequency_keywords(tokens, top_k * 2)
            tfidf_keywords_extra = _build_tfidf_keywords(cleaned_text, top_k * 2)
            keywords_extra = merge_keywords(freq_keywords_extra, tfidf_keywords_extra, top_k=top_k * 2)
        filtered_keywords = _filter_keywords(keywords_extra)[:top_k]
    
    if len(filtered_ngrams) < top_k:
        ngrams_extra = _build_ngram_keywords(cleaned_text, top_k * 2)
        filtered_ngrams = _filter_keywords(ngrams_extra)[:top_k]
    
    if len(filtered_phrases) < top_k:
        phrases_extra = merge_keywords(
            _build_rake_phrases(cleaned_text, top_k * 2),
            _build_keybert_phrases(cleaned_text, top_k * 2),
            _build_simple_phrases(cleaned_text, top_k * 2),
            top_k=top_k * 2,
        )
        filtered_phrases = _filter_keywords(phrases_extra)[:top_k]
    
    return AnalysisResult(
        total_words=len(tokens),
        unique_words=len(set(tokens)),
        top_keywords=filtered_keywords,
        top_ngrams=filtered_ngrams,
        top_phrases=filtered_phrases,
        cleaned_text=cleaned_text,
    )
