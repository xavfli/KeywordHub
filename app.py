from __future__ import annotations

import asyncio

import pandas as pd
import streamlit as st

from keywordhub.analyzer import AnalysisResult, analyze_text, extract_text_from_file
from keywordhub.exporters import keywords_to_text, rows_to_csv_bytes, suggestions_to_text
from keywordhub.suggestions import SuggestionPanel, fetch_suggestions


st.set_page_config(
    page_title="KeywordHub",
    page_icon="KH",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

    :root {
        --bg: #f7efe3;
        --bg-soft: #fffaf3;
        --surface: rgba(255, 251, 245, 0.92);
        --surface-strong: #fffdf9;
        --ink: #201811;
        --muted: #6e6256;
        --accent: #c96a42;
        --accent-dark: #9f4e2d;
        --accent-soft: rgba(201, 106, 66, 0.12);
        --line: rgba(71, 53, 35, 0.12);
        --shadow: 0 18px 44px rgba(88, 63, 33, 0.10);
        --shadow-soft: 0 10px 24px rgba(88, 63, 33, 0.08);
    }

    html, body, [class*="css"] {
        font-family: "Space Grotesk", sans-serif;
    }

    .stApp {
        color: var(--ink);
        background:
            radial-gradient(circle at top left, rgba(201, 106, 66, 0.16), transparent 24%),
            radial-gradient(circle at top right, rgba(93, 140, 122, 0.12), transparent 18%),
            linear-gradient(180deg, #efe2d0 0%, var(--bg) 42%, #fcf8f1 100%);
    }

    .block-container {
        max-width: 1220px;
        padding-top: 1.6rem;
        padding-bottom: 2.8rem;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2a211a 0%, #221b16 100%);
        border-right: 1px solid rgba(255,255,255,0.06);
    }

    section[data-testid="stSidebar"] * {
        color: #f8efe0 !important;
    }

    div[data-testid="stMetric"] {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 22px;
        padding: 12px 14px;
        box-shadow: var(--shadow-soft);
    }

    div[data-testid="stMetric"] label {
        color: var(--muted) !important;
        font-family: "IBM Plex Mono", monospace;
        letter-spacing: 0.04em;
    }

    div[data-testid="stMetricValue"] {
        color: var(--ink) !important;
    }

    div[data-testid="stTextInputRootElement"] > div,
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stFileUploader"] section {
        background: rgba(255, 250, 243, 0.94) !important;
        border-radius: 18px !important;
        border: 1px solid rgba(71, 53, 35, 0.14) !important;
    }

    div[data-testid="stFileUploader"] section,
    div[data-testid="stFileUploader"] section * {
        color: var(--ink) !important;
    }

    label,
    div[data-testid="stWidgetLabel"],
    div[data-testid="stFileUploader"] label,
    div[data-testid="stTextInput"] label,
    div[data-testid="stTextArea"] label,
    div[data-testid="stSlider"] label,
    div[data-testid="stToggle"] label,
    div.row-widget label,
    .stMarkdown p,
    .stCaptionContainer,
    small {
        color: var(--ink) !important;
        opacity: 1 !important;
    }

    div[data-testid="stTextInputRootElement"] input,
    div[data-testid="stTextArea"] textarea {
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
    }

    div[data-testid="stTextInputRootElement"] input::placeholder,
    div[data-testid="stTextArea"] textarea::placeholder {
        color: #8f8173 !important;
    }

    div[data-testid="stFileUploaderDropzoneInstructions"] span,
    div[data-testid="stFileUploaderDropzoneInstructions"] small,
    div[data-testid="stFileUploaderDropzoneInstructions"] div,
    div[data-testid="stTextInputInstructions"],
    div[data-testid="stTextInputInstructions"] * {
        color: var(--muted) !important;
        opacity: 1 !important;
    }

    div[data-testid="stFileUploader"] button {
        background: #1a2030 !important;
        color: #fff8f0 !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
    }

    div[data-testid="stFileUploader"] button * {
        color: #fff8f0 !important;
    }

    div[data-testid="stTextInputRootElement"] > div:focus-within,
    div[data-testid="stTextArea"] textarea:focus {
        box-shadow: 0 0 0 3px rgba(201, 106, 66, 0.14) !important;
        border-color: rgba(201, 106, 66, 0.35) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 999px;
        background: rgba(255, 250, 243, 0.85);
        border: 1px solid rgba(71, 53, 35, 0.10);
        padding: 8px 16px;
        transition: all 180ms ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        transform: translateY(-1px);
        border-color: rgba(201, 106, 66, 0.22);
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--accent), var(--accent-dark));
        color: white !important;
        box-shadow: 0 10px 24px rgba(201, 106, 66, 0.24);
    }

    .stButton button,
    .stDownloadButton button {
        border-radius: 999px !important;
        min-height: 46px !important;
        font-weight: 700 !important;
        transition: transform 180ms ease, box-shadow 180ms ease !important;
    }

    .stButton button {
        background: linear-gradient(135deg, var(--accent), var(--accent-dark)) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 14px 30px rgba(201, 106, 66, 0.24);
    }

    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 18px 34px rgba(201, 106, 66, 0.30) !important;
    }

    .stDownloadButton button {
        background: var(--surface-strong) !important;
        color: var(--accent-dark) !important;
        border: 1px solid rgba(201, 106, 66, 0.22) !important;
        box-shadow: var(--shadow-soft);
    }

    .stDownloadButton button:hover {
        transform: translateY(-2px);
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 22px;
        overflow: hidden;
        box-shadow: var(--shadow);
        background: var(--surface-strong);
    }

    div[data-testid="stAlert"] {
        border-radius: 18px;
    }

    div[data-testid="stToggle"] span,
    div[data-testid="stToggle"] p,
    div[data-testid="stSlider"] span,
    div[data-testid="stSlider"] p {
        color: var(--ink) !important;
        opacity: 1 !important;
    }

    div[data-testid="stMarkdownContainer"] a {
        color: var(--accent-dark);
        text-decoration-thickness: 1px;
    }

    div[data-testid="stMarkdownContainer"] a:hover {
        color: var(--accent);
    }

    .hero-wrap {
        background:
            linear-gradient(135deg, rgba(255,252,246,0.96), rgba(246,235,219,0.90)),
            linear-gradient(120deg, rgba(201,106,66,0.04), rgba(93,140,122,0.03));
        border: 1px solid rgba(71, 53, 35, 0.10);
        border-radius: 28px;
        padding: 26px 28px;
        margin-bottom: 1rem;
        box-shadow: var(--shadow);
    }

    .hero-kicker {
        font-family: "IBM Plex Mono", monospace;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        font-size: 12px;
        color: #2c655d;
        margin-bottom: 10px;
    }

    .hero-title {
        font-size: 56px;
        line-height: 0.95;
        font-weight: 700;
        color: var(--ink);
        margin: 0 0 14px 0;
    }

    .hero-copy {
        color: var(--muted);
        font-size: 17px;
        max-width: 760px;
    }

    .hero-pills {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 18px;
    }

    .hero-pill {
        background: var(--accent-soft);
        color: var(--accent-dark);
        border: 1px solid rgba(201, 106, 66, 0.12);
        border-radius: 999px;
        padding: 8px 12px;
        font-size: 13px;
        font-weight: 500;
    }

    .suggestion-url {
        color: var(--muted);
        font-size: 12px;
        line-height: 1.45;
        margin: -6px 0 10px 18px;
        word-break: break-all;
    }

    @media (max-width: 900px) {
        .hero-title {
            font-size: 38px;
        }
        .hero-copy {
            font-size: 15px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _hero() -> None:
    st.markdown(
        """
        <div class="hero-wrap">
            <div class="hero-kicker">Pure Python Keyword Workspace</div>
            <div class="hero-title">KeywordHub</div>
            <div class="hero-copy">
                Matndan kalit so'zlarni ajrating, muhim iboralarni toping va
                Google, YouTube, Bing suggestion natijalarini bitta joyda ko'ring.
            </div>
            <div class="hero-pills">
                <span class="hero-pill">TF-IDF va N-gram</span>
                <span class="hero-pill">Live Suggestions</span>
                <span class="hero-pill">TXT va CSV eksport</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _load_text_input() -> str:
    uploaded = st.file_uploader("Fayl yuklash", type=["txt", "md", "csv"])
    text_value = st.text_area(
        "Tahlil uchun matn",
        height=280,
        placeholder="Bu yerga matn yozing yoki fayl yuklang...",
    )
    if uploaded is not None:
        try:
            text_value = extract_text_from_file(uploaded.name, uploaded.getvalue())
            st.success("Fayldagi matn muvaffaqiyatli o'qildi.")
        except ValueError as exc:
            st.error(str(exc))
    return text_value


def _render_metric_cards(result: AnalysisResult) -> None:
    col1, col2, col3 = st.columns(3)
    col1.metric("So'zlar soni", result.total_words)
    col2.metric("Unikal so'zlar", result.unique_words)
    col3.metric("Top kalitlar", len(result.top_keywords))


def _render_keyword_table(title: str, items: list, key_prefix: str) -> None:
    st.subheader(title)
    if not items:
        st.info("Hozircha natija topilmadi.")
        return
    frame = pd.DataFrame(
        [{"Term": item.term, "Score": item.score, "Source": item.source} for item in items]
    )
    st.dataframe(frame, use_container_width=True, hide_index=True)
    text_payload = keywords_to_text(title, items)
    csv_payload = rows_to_csv_bytes(frame.columns.tolist(), frame.astype(str).values.tolist())
    col1, col2 = st.columns(2)
    col1.download_button(
        "TXT yuklab olish",
        data=text_payload.encode("utf-8"),
        file_name=f"{key_prefix}.txt",
        mime="text/plain",
        use_container_width=True,
    )
    col2.download_button(
        "CSV yuklab olish",
        data=csv_payload,
        file_name=f"{key_prefix}.csv",
        mime="text/csv",
        use_container_width=True,
    )


def _render_analysis_mode() -> None:
    st.subheader("Matn Tahlili")
    st.caption("Matndan kalit so'zlar, n-gramlar va muhim iboralarni ajratish moduli.")
    left, right = st.columns([1.4, 0.6], gap="large")
    with left:
        text = _load_text_input()
    with right:
        top_k = st.slider("Natijalar soni", min_value=5, max_value=40, value=20, step=5)
        run_analysis = st.button("Matnni tahlil qilish", type="primary", use_container_width=True)
    if not run_analysis:
        return
    if not text.strip():
        st.warning("Tahlil qilish uchun matn kiriting.")
        return
    with st.spinner("Matn tahlil qilinmoqda..."):
        result = analyze_text(text, top_k=top_k)
    _render_metric_cards(result)
    tabs = st.tabs(["Kalit so'zlar", "N-gramlar", "Muhim iboralar"])
    with tabs[0]:
        _render_keyword_table("Kalit so'zlar", result.top_keywords, "keywords")
    with tabs[1]:
        _render_keyword_table("N-gramlar", result.top_ngrams, "ngrams")
    with tabs[2]:
        _render_keyword_table("Muhim iboralar", result.top_phrases, "phrases")
    combined_text = "\n\n".join(
        [
            keywords_to_text("Kalit so'zlar", result.top_keywords),
            keywords_to_text("N-gramlar", result.top_ngrams),
            keywords_to_text("Muhim iboralar", result.top_phrases),
        ]
    )
    combined_rows = [
        ["keyword", item.term, str(item.score), item.source] for item in result.top_keywords
    ] + [["ngram", item.term, str(item.score), item.source] for item in result.top_ngrams] + [
        ["phrase", item.term, str(item.score), item.source] for item in result.top_phrases
    ]
    st.subheader("Barchasi Bir Joyda")
    st.text_area("Nusxalash uchun tayyor matn", value=combined_text, height=220)
    col1, col2 = st.columns(2)
    col1.download_button(
        "Barchasini TXT yuklab olish",
        data=combined_text.encode("utf-8"),
        file_name="analysis_all.txt",
        mime="text/plain",
        use_container_width=True,
    )
    col2.download_button(
        "Barchasini CSV yuklab olish",
        data=rows_to_csv_bytes(["Type", "Term", "Score", "Source"], combined_rows),
        file_name="analysis_all.csv",
        mime="text/csv",
        use_container_width=True,
    )


def _render_panel(panel: SuggestionPanel) -> None:
    with st.container(border=True):
        st.markdown(f"### {panel.source}")
        if panel.error:
            st.warning(panel.error)
            return
        if not panel.suggestions:
            st.info("Taklif topilmadi.")
            return
        for item in panel.suggestions:
            st.markdown(f"- [{item.text}]({item.url})")
            st.markdown(
                f'<div class="suggestion-url">{item.url}</div>',
                unsafe_allow_html=True,
            )


def _render_suggestion_mode() -> None:
    st.subheader("Qidiruv Takliflari")
    st.caption("Google, YouTube va Bing dan suggestion natijalarini olish.")
    col1, col2 = st.columns([1.2, 0.8], gap="large")
    with col1:
        query = st.text_input("Qidiruv so'zi", placeholder="Masalan: sun'iy intellekt")
    with col2:
        auto_fetch = st.toggle("Yozish bilan jonli yangilash", value=True)
        manual_fetch = st.button("Takliflarni olish", type="primary", use_container_width=True)
    should_run = query.strip() and (auto_fetch or manual_fetch)
    if not should_run:
        st.info("So'zni yozing va natijalar shu yerda ko'rinadi.")
        return
    with st.spinner("Takliflar olinmoqda..."):
        panels = _run_async(fetch_suggestions(query.strip()))
    cols = st.columns(3)
    for col, panel in zip(cols, panels):
        with col:
            _render_panel(panel)

    all_rows = [[panel.source, item.text, item.url] for panel in panels for item in panel.suggestions]
    st.subheader("Eksport")
    col1, col2 = st.columns(2)
    col1.download_button(
        "TXT yuklab olish",
        data=suggestions_to_text(panels).encode("utf-8"),
        file_name="suggestions.txt",
        mime="text/plain",
        use_container_width=True,
    )
    col2.download_button(
        "CSV yuklab olish",
        data=rows_to_csv_bytes(["Source", "Suggestion", "URL"], all_rows),
        file_name="suggestions.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.text_area(
        "Nusxalash uchun tayyor ro'yxat",
        value=suggestions_to_text(panels),
        height=220,
    )


def _run_async(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


def main() -> None:
    _hero()
    st.sidebar.title("KeywordHub")
    st.sidebar.caption("Kalit so'z tahlili va live suggestion platformasi.")
    mode = st.sidebar.radio(
        "Bo'limni tanlang",
        ["Matn tahlili", "Qidiruv takliflari"],
    )
    if mode == "Matn tahlili":
        _render_analysis_mode()
    else:
        _render_suggestion_mode()


if __name__ == "__main__":
    main()
