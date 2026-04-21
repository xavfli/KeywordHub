from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

try:
    from rake_nltk import Rake
except ImportError:  # pragma: no cover
    Rake = None


TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яЁё0-9'-]+", re.UNICODE)

UZBEK_STOPWORDS = {
    "va",
    "ham",
    "bu",
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
    "bo'ladi",
    "bo'lgan",
    "bo'lsa",
    "qiladi",
    "qilish",
    "qilib",
    "qilgan",
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
    "barcha",
    "har",
    "hech",
    "o'z",
    "ozi",
    "siz",
    "biz",
    "ular",
    "meni",
    "seni",
    "uni",
    "ularni",
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

STOPWORDS = set(ENGLISH_STOP_WORDS) | UZBEK_STOPWORDS | RUSSIAN_STOPWORDS


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


def _normalize_token(token: str) -> str:
    return token.strip("-'").lower()


def tokenize(text: str) -> list[str]:
    tokens = [_normalize_token(match.group(0)) for match in TOKEN_RE.finditer(text)]
    return [token for token in tokens if len(token) > 1 and token not in STOPWORDS]


def extract_text_from_file(name: str, data: bytes) -> str:
    suffix = Path(name).suffix.lower()
    if suffix in {".txt", ".md", ".csv"}:
        return data.decode("utf-8", errors="ignore")
    raise ValueError("Faqat .txt, .md va .csv fayllar qo'llab-quvvatlanadi.")


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
        vectorizer = TfidfVectorizer(stop_words=list(STOPWORDS), ngram_range=(1, 1))
        matrix = vectorizer.fit_transform([text])
        features = vectorizer.get_feature_names_out()
        scores = matrix.toarray()[0]
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
    try:
        vectorizer = TfidfVectorizer(stop_words=list(STOPWORDS), ngram_range=(2, 3))
        matrix = vectorizer.fit_transform([text])
        features = vectorizer.get_feature_names_out()
        scores = matrix.toarray()[0]
        pairs = sorted(zip(features, scores), key=lambda item: item[1], reverse=True)
        return [
            KeywordItem(term=term, score=round(float(score), 4), source="ngram")
            for term, score in pairs[:top_k]
            if score > 0
        ]
    except ValueError:
        return []


def _build_rake_phrases(text: str, top_k: int) -> list[KeywordItem]:
    if not Rake or not text.strip():
        return []
    rake = Rake(stopwords=list(STOPWORDS))
    rake.extract_keywords_from_text(text)
    phrases = rake.get_ranked_phrases_with_scores()
    return [
        KeywordItem(term=phrase, score=round(float(score), 4), source="rake")
        for score, phrase in phrases[:top_k]
    ]


def _build_keybert_phrases(text: str, top_k: int) -> list[KeywordItem]:
    if not text.strip():
        return []
    try:
        from keybert import KeyBERT

        model = KeyBERT()
        phrases = model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 3),
            stop_words=list(STOPWORDS),
            top_n=top_k,
        )
    except Exception:
        return []
    return [
        KeywordItem(term=phrase, score=round(float(score), 4), source="keybert")
        for phrase, score in phrases
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


def analyze_text(text: str, top_k: int = 20) -> AnalysisResult:
    cleaned_text = " ".join(text.split())
    tokens = tokenize(cleaned_text)
    freq_keywords = _build_frequency_keywords(tokens, top_k)
    tfidf_keywords = _build_tfidf_keywords(cleaned_text, top_k)
    merged_keywords = merge_keywords(freq_keywords, tfidf_keywords, top_k=top_k)
    ngrams = _build_ngram_keywords(cleaned_text, top_k)
    phrases = merge_keywords(
        _build_rake_phrases(cleaned_text, top_k),
        _build_keybert_phrases(cleaned_text, top_k),
        top_k=top_k,
    )
    return AnalysisResult(
        total_words=len(tokens),
        unique_words=len(set(tokens)),
        top_keywords=merged_keywords,
        top_ngrams=ngrams,
        top_phrases=phrases,
        cleaned_text=cleaned_text,
    )
