from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from keywordhub.analyzer import AnalysisResult, KeywordItem, analyze_text, extract_text_from_file
from keywordhub.exporters import keywords_to_text, rows_to_csv_bytes


DEMO_USERS = {"admin": "12345", "demo": "demo123", "asad": "12345"}
KEYWORD_DISPLAY_LIMIT = 12
ANALYSIS_TOP_LIMIT = 40
METHODS = {
    "TF-IDF": ("Σ", "Eng muhim so'zlarni TF-IDF algoritmi yordamida topadi."),
    "N-gram": ("N", "So'z birikmalarini, bi-gram va tri-gramlarni aniqlaydi."),
    "TextRank": ("☆", "Matn ichidagi bog'liqlikka asoslangan usul."),
    "YAKE": ("Y", "Kalit so'zlarni avtomatik ajratib oladi."),
    "RAKE": ("R", "So'zlar orasidagi bog'lanishga asoslangan usul."),
}
SAMPLE_TEXT = (
    "Sun'iy intellekt zamonaviy texnologiyalarning eng muhim yo'nalishlaridan biridir. "
    "U katta hajmdagi ma'lumotlarni tahlil qilish, muammolarni hal etish va "
    "avtomatlashtirish jarayonlarini tezlashtirishga yordam beradi."
)


st.set_page_config(page_title="KeyWord AI", page_icon="KW", layout="wide", initial_sidebar_state="expanded")


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Material+Symbols+Rounded:wght@400;500;600;700&display=swap');

    :root {
        --ink: #111827;
        --muted: #667085;
        --line: #e7e7f1;
        --soft: #f7f7fe;
        --accent: #4f46e5;
        --accent-2: #635bff;
        --accent-soft: #f1efff;
        --success: #10b981;
        --warning: #f97316;
        --shadow: 0 16px 40px rgba(17, 24, 39, 0.08);
    }

    html, body, [class*="css"] {
        font-family: "Inter", sans-serif;
        color: var(--ink);
    }

    .stApp {
        background: #fbfcff;
    }

    header[data-testid="stHeader"],
    div[data-testid="stToolbar"],
    #MainMenu,
    footer {
        display: none !important;
    }

    .block-container {
        max-width: 1320px;
        padding: 1.25rem 2rem 2.5rem;
    }

    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid var(--line);
    }

    section[data-testid="stSidebar"] .stButton button {
        min-height: 48px !important;
        border-radius: 10px !important;
        background: transparent !important;
        color: #475467 !important;
        border: 1px solid transparent !important;
        box-shadow: none !important;
        justify-content: flex-start !important;
        padding-left: 16px !important;
        font-weight: 600 !important;
    }

    section[data-testid="stSidebar"] .stButton button:hover {
        background: var(--accent-soft) !important;
        color: var(--accent) !important;
        border-color: transparent !important;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 12px;
        color: #0b102d;
        font-size: 24px;
        font-weight: 800;
        padding: 8px 0 22px;
    }

    .brand-mark {
        width: 38px;
        height: 38px;
        border: 2px solid var(--accent);
        border-radius: 12px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        color: var(--accent);
        font-weight: 800;
        font-size: 13px;
    }

    .top-nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 24px;
        padding: 12px 0 20px;
        border-bottom: 1px solid var(--line);
        margin: -8px 0 38px;
    }

    .nav-links {
        display: flex;
        justify-content: center;
        gap: 38px;
        flex: 1;
    }

    .nav-links a {
        color: #111827 !important;
        text-decoration: none;
        font-weight: 700;
        padding: 18px 0;
    }

    .nav-links a.active {
        color: var(--accent) !important;
        border-bottom: 2px solid var(--accent);
    }

    .hero {
        display: grid;
        grid-template-columns: minmax(0, 0.92fr) minmax(0, 1.08fr);
        align-items: center;
        gap: 72px;
        min-height: 560px;
        padding: 28px 0 34px;
    }

    .pill {
        display: inline-flex;
        padding: 8px 16px;
        border-radius: 999px;
        background: var(--accent-soft);
        color: var(--accent);
        font-weight: 700;
        font-size: 15px;
        margin-bottom: 26px;
    }

    .hero h1 {
        margin: 0 0 24px;
        font-size: 64px;
        line-height: 1.12;
        letter-spacing: 0;
        color: #081033;
        font-weight: 800;
        max-width: 660px;
    }

    .hero h1 span {
        color: var(--accent);
    }

    .hero p {
        color: #475467;
        font-size: 21px;
        line-height: 1.65;
        margin-bottom: 34px;
        max-width: 580px;
    }

    .hero-demo {
        position: relative;
        min-height: 460px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .demo-blob {
        position: absolute;
        inset: 10px 0;
        border-radius: 42% 58% 44% 56%;
        background: #eeeafd;
    }

    .demo-card {
        position: relative;
        z-index: 1;
        width: min(690px, 100%);
        background: rgba(255,255,255,0.9);
        border: 1px solid var(--line);
        border-radius: 24px;
        padding: 24px;
        box-shadow: var(--shadow);
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 22px;
    }

    .demo-panel {
        background: #fff;
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 24px;
        min-height: 300px;
    }

    .demo-title {
        font-size: 22px;
        font-weight: 800;
        margin-bottom: 24px;
    }

    .line {
        height: 10px;
        background: #e7eaf2;
        border-radius: 999px;
        margin: 12px 0;
    }

    .chip-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 14px;
    }

    .demo-chip {
        background: #edeaff;
        color: #312e81;
        border-radius: 10px;
        padding: 12px 10px;
        font-weight: 800;
        text-align: center;
        font-size: 14px;
    }

    .arrow-bubble {
        position: absolute;
        z-index: 2;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        width: 46px;
        height: 46px;
        border-radius: 999px;
        background: var(--accent);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 26px;
        font-weight: 700;
    }

    .section-band {
        margin: 54px -2rem -2.5rem;
        padding: 56px 2rem 72px;
        background: #faf9ff;
        border-top: 1px solid #f0eefc;
    }

    .section-title {
        text-align: center;
        font-size: 34px;
        font-weight: 800;
        color: #081033;
        margin: 8px 0 42px;
    }

    .step-card {
        background: #fff;
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 28px;
        min-height: 220px;
        box-shadow: 0 12px 30px rgba(17,24,39,0.05);
    }

    .step-card h3 {
        color: #111827;
        font-size: 22px;
        font-weight: 800;
        margin: 0 0 10px;
    }

    .step-card p {
        color: #475467;
        font-size: 16px;
        line-height: 1.6;
        margin: 0;
    }

    .step-icon {
        width: 70px;
        height: 70px;
        border-radius: 999px;
        background: var(--accent-soft);
        color: var(--accent);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        font-weight: 800;
        margin-bottom: 22px;
    }

    .section-band .pill {
        color: var(--accent);
        background: var(--accent-soft);
    }

    .section-band ::selection,
    .hero ::selection,
    .auth-copy-panel ::selection {
        background: rgba(79,70,229,0.18);
        color: #111827;
    }

    .page-title {
        font-size: 30px;
        font-weight: 800;
        margin: 0;
        color: #111827;
    }

    .page-subtitle {
        color: var(--muted);
        font-size: 16px;
        margin: 8px 0 24px;
    }

    h1, h2, h3, h4, h5, h6,
    div[data-testid="stMarkdownContainer"] h1,
    div[data-testid="stMarkdownContainer"] h2,
    div[data-testid="stMarkdownContainer"] h3,
    div[data-testid="stMarkdownContainer"] h4,
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stRadio"] label,
    div[data-testid="stRadio"] label *,
    div[data-testid="stCheckbox"] label,
    div[data-testid="stCheckbox"] label * {
        color: var(--ink) !important;
        opacity: 1 !important;
        -webkit-text-fill-color: var(--ink) !important;
    }

    div[data-testid="stRadio"] [data-testid="stCaptionContainer"],
    div[data-testid="stRadio"] [data-testid="stCaptionContainer"] *,
    div[data-testid="stCaptionContainer"],
    div[data-testid="stCaptionContainer"] * {
        color: var(--muted) !important;
        opacity: 1 !important;
        -webkit-text-fill-color: var(--muted) !important;
    }

    .work-card {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 10px 28px rgba(17,24,39,0.04);
    }

    .dashboard-layout {
        margin-top: 4px;
    }

    .side-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        color: #0b102d;
        font-size: 24px;
        font-weight: 800;
        padding: 2px 0 26px;
    }

    .side-section {
        border-right: 1px solid var(--line);
        min-height: calc(100vh - 70px);
        padding-right: 14px;
    }

    .side-card {
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 18px;
        margin-top: 22px;
        background: #ffffff;
        box-shadow: 0 10px 24px rgba(17,24,39,0.035);
    }

    .side-card.pro {
        background: #f7f5ff;
        border-color: #edeaff;
    }

    .side-card-title {
        color: #111827;
        font-weight: 800;
        margin-bottom: 8px;
    }

    .side-card-copy {
        color: var(--muted);
        line-height: 1.6;
        font-size: 14px;
        margin: 0;
    }

    .side-nav-scope + div .stButton button {
        justify-content: flex-start !important;
        min-height: 48px !important;
        border-radius: 10px !important;
        border-color: transparent !important;
        background: transparent !important;
        color: #475467 !important;
        padding-left: 14px !important;
        font-weight: 700 !important;
    }

    .side-nav-scope + div .stButton button:hover {
        background: var(--accent-soft) !important;
        color: var(--accent) !important;
        border-color: transparent !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: var(--line) !important;
        border-radius: 14px !important;
        background: #ffffff !important;
        box-shadow: 0 10px 28px rgba(17,24,39,0.035) !important;
    }

    .dashboard-panel-title {
        font-size: 18px;
        font-weight: 800;
        color: #111827;
        margin: 4px 0 14px;
    }

    .input-tabs {
        display: grid;
        grid-template-columns: 1fr 1fr;
        align-items: center;
        border: 1px solid var(--line);
        border-bottom: 0;
        border-radius: 12px 12px 0 0;
        overflow: hidden;
        background: #ffffff;
        margin-top: 2px;
    }

    .input-tabs span {
        min-height: 48px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        color: #475467;
        font-weight: 700;
        border-bottom: 3px solid transparent;
    }

    .input-tabs .active {
        color: var(--accent);
        border-bottom-color: var(--accent);
        background: #fbfbff;
    }

    .tab-icon,
    .keyword-result-icon {
        font-family: "Material Symbols Rounded";
        font-weight: normal;
        font-style: normal;
        line-height: 1;
        letter-spacing: 0;
        text-transform: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        white-space: nowrap;
        word-wrap: normal;
        direction: ltr;
    }

    .method-card {
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 14px;
        min-height: 74px;
        background: #fff;
    }

    .method-card.active {
        border-color: var(--accent);
        background: #f8f7ff;
    }

    .method-row {
        display: flex;
        gap: 12px;
        align-items: center;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .method-badge {
        width: 34px;
        height: 34px;
        border-radius: 10px;
        background: var(--accent-soft);
        color: var(--accent);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
    }

    .method-copy {
        color: var(--muted);
        font-size: 13px;
        padding-left: 46px;
    }

    div[data-testid="stRadio"] > label {
        display: none !important;
    }

    div[data-testid="stRadio"] [role="radiogroup"] {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }

    div[data-testid="stRadio"] [role="radiogroup"] label {
        min-height: 64px;
        padding: 12px 14px !important;
        border: 1px solid var(--line) !important;
        border-radius: 12px !important;
        background: #ffffff !important;
        box-shadow: 0 6px 18px rgba(17,24,39,0.025);
        align-items: flex-start !important;
        width: 100% !important;
    }

    div[data-testid="stRadio"] [role="radiogroup"] label:hover {
        border-color: #c7c3ff !important;
        background: #fbfbff !important;
    }

    div[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {
        border-color: var(--accent) !important;
        background: #f8f7ff !important;
        box-shadow: 0 0 0 1px rgba(79,70,229,0.12);
    }

    div[data-testid="stRadio"] [role="radiogroup"] label > div:first-child {
        margin-top: 2px !important;
        margin-right: 10px !important;
    }

    div[data-testid="stTextArea"] textarea,
    div[data-testid="stFileUploader"] section,
    div[data-testid="stTextInputRootElement"] > div,
    div[data-baseweb="select"] > div {
        background: #ffffff !important;
        border-color: var(--line) !important;
        color: var(--ink) !important;
        border-radius: 10px !important;
    }

    div[data-testid="stTextArea"] textarea::placeholder,
    div[data-testid="stTextInputRootElement"] input::placeholder {
        color: #98a2b3 !important;
        opacity: 1 !important;
    }

    div[data-testid="stFileUploader"] section {
        background: #fbfbff !important;
        color: var(--ink) !important;
    }

    div[data-testid="stFileUploader"] section {
        min-height: 220px !important;
        border: 1px dashed #b8b4e8 !important;
        border-radius: 12px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    div[data-testid="stFileUploader"] section div,
    div[data-testid="stFileUploader"] section span,
    div[data-testid="stFileUploader"] section small {
        background: transparent !important;
        color: #475467 !important;
        -webkit-text-fill-color: #475467 !important;
        opacity: 1 !important;
    }

    div[data-testid="stFileUploader"] button {
        background: var(--accent) !important;
        border-color: var(--accent) !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        font-weight: 800 !important;
    }

    div[data-testid="stFileUploader"] button * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        background: transparent !important;
    }

    div[data-testid="stFileUploaderFile"],
    div[data-testid="stFileUploader"] [data-baseweb="tag"] {
        background: #ffffff !important;
        color: var(--ink) !important;
        border: 1px solid var(--line) !important;
    }

    .stButton button,
    .stDownloadButton button {
        border-radius: 10px !important;
        min-height: 46px !important;
        font-weight: 700 !important;
        box-shadow: none !important;
        border: 1px solid var(--line) !important;
        color: #111827 !important;
        background: #ffffff !important;
    }

    .stButton button[kind="primary"],
    .stDownloadButton button[kind="primary"],
    .stFormSubmitButton button[kind="primary"],
    button[data-testid="stBaseButton-primary"] {
        background: var(--accent) !important;
        border-color: var(--accent) !important;
        color: #ffffff !important;
    }

    .stButton button[kind="primary"] *,
    .stDownloadButton button[kind="primary"] *,
    .stFormSubmitButton button[kind="primary"] *,
    button[data-testid="stBaseButton-primary"] * {
        color: #ffffff !important;
        opacity: 1 !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    .stButton button:hover,
    .stDownloadButton button:hover,
    .stFormSubmitButton button:hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
    }

    .stButton button[kind="primary"]:hover,
    .stDownloadButton button[kind="primary"]:hover,
    .stFormSubmitButton button[kind="primary"]:hover,
    button[data-testid="stBaseButton-primary"]:hover {
        background: #4338ca !important;
        color: #ffffff !important;
    }

    .auth-page {
        min-height: 82vh;
        display: grid;
        grid-template-columns: minmax(0, 0.92fr) minmax(360px, 0.72fr);
        gap: 48px;
        align-items: center;
        padding: 28px 0 48px;
    }

    .auth-copy-panel {
        background:
            radial-gradient(circle at 82% 16%, rgba(79,70,229,0.14), transparent 32%),
            linear-gradient(135deg, #ffffff, #f6f4ff);
        border: 1px solid var(--line);
        border-radius: 28px;
        padding: 46px;
        min-height: 480px;
        box-shadow: var(--shadow);
    }

    .auth-copy-panel h1 {
        font-size: 46px;
        line-height: 1.15;
        margin: 20px 0 18px;
        color: #081033;
    }

    .auth-copy-panel p {
        color: var(--muted);
        font-size: 18px;
        line-height: 1.7;
        max-width: 520px;
    }

    .auth-card {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 22px;
        padding: 30px;
        box-shadow: var(--shadow);
    }

    .auth-card h2 {
        font-size: 28px;
        margin: 0 0 8px;
        color: #081033;
    }

    .auth-card .auth-muted {
        color: var(--muted);
        margin-bottom: 20px;
        line-height: 1.55;
    }

    div[data-testid="stTextInputRootElement"] > div {
        min-height: 48px !important;
        border-radius: 12px !important;
        border: 1px solid var(--line) !important;
        background: #ffffff !important;
        box-shadow: 0 8px 18px rgba(17,24,39,0.04) !important;
    }

    div[data-testid="stTextInputRootElement"] input {
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
    }

    div[data-testid="stTextInputRootElement"]:focus-within > div {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 4px rgba(79,70,229,0.12) !important;
    }

    label,
    div[data-testid="stMarkdownContainer"] p {
        color: #344054 !important;
    }

    div[data-testid="stForm"] {
        border: 0 !important;
        background: transparent !important;
        padding: 0 !important;
    }

    div[data-testid="stFormSubmitButton"] button {
        background: var(--accent) !important;
        border: 1px solid var(--accent) !important;
        color: #ffffff !important;
        min-height: 48px !important;
        border-radius: 10px !important;
        font-weight: 800 !important;
    }

    div[data-testid="stFormSubmitButton"] button * {
        color: #ffffff !important;
        opacity: 1 !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    div[data-testid="stFormSubmitButton"] button:hover {
        background: #4338ca !important;
        border-color: #4338ca !important;
        color: #ffffff !important;
    }

    .auth-form-heading {
        font-size: 30px;
        line-height: 1.15;
        color: #081033;
        font-weight: 800;
        margin: 0 0 8px;
    }

    .auth-form-copy {
        color: var(--muted);
        line-height: 1.55;
        margin-bottom: 22px;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 10px;
        overflow: hidden;
    }

    .keyword-result-card {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 26px;
        box-shadow: var(--shadow);
        margin: 18px 0 24px;
    }

    .keyword-result-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 18px;
        margin-bottom: 22px;
    }

    .keyword-result-title {
        display: flex;
        align-items: center;
        gap: 12px;
        color: #111827;
        font-size: 24px;
        font-weight: 800;
    }

    .keyword-result-icon {
        width: 34px;
        height: 34px;
        border-radius: 12px;
        background: var(--accent-soft);
        color: var(--accent);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
    }

    .keyword-result-count {
        color: var(--muted);
        font-size: 15px;
        font-weight: 600;
    }

    .keyword-result-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 14px;
    }

    .keyword-result-item {
        display: grid;
        grid-template-columns: 42px 1fr auto;
        align-items: center;
        gap: 12px;
        min-height: 58px;
        padding: 12px 16px;
        border: 1px solid var(--line);
        border-radius: 12px;
        background: #fbfbff;
    }

    .keyword-rank {
        width: 30px;
        height: 30px;
        border-radius: 999px;
        background: var(--accent-soft);
        color: var(--accent);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 14px;
    }

    .keyword-term {
        color: #1f2937;
        font-weight: 800;
        font-size: 16px;
        word-break: break-word;
    }

    .keyword-score {
        color: var(--accent);
        font-weight: 800;
        font-size: 15px;
    }

    @media (max-width: 900px) {
        .keyword-result-grid {
            grid-template-columns: 1fr;
        }
    }

    .upgrade-card,
    .helper-card {
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 18px;
        margin-top: 24px;
        background: #fff;
    }

    .upgrade-card {
        background: #f7f5ff;
    }

    @media (max-width: 900px) {
        .hero {
            grid-template-columns: 1fr;
        }
        .hero h1 {
            font-size: 42px;
        }
        .demo-card {
            grid-template-columns: 1fr;
        }
        .arrow-bubble {
            display: none;
        }
        .nav-links {
            display: none;
        }
        .auth-page {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_state() -> None:
    defaults = {
        "is_authenticated": False,
        "current_user": "",
        "users": dict(DEMO_USERS),
        "auth_view": "login",
        "show_auth_page": False,
        "page": "Asosiy sahifa",
        "method": "TF-IDF",
        "keywords_count": 20,
        "analysis_result": None,
        "analysis_text": "",
        "analysis_text_input": "",
        "pending_analysis_text": None,
        "last_uploaded_file_id": "",
        "analysis_history": [],
        "documents": [],
        "favorites": [],
        "language": "UZ",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def set_page(page: str) -> None:
    st.session_state["page"] = page


def login_user(username: str, password: str) -> bool:
    users = st.session_state.get("users", {})
    normalized = username.strip().lower()
    if users.get(normalized) == password.strip():
        st.session_state["is_authenticated"] = True
        st.session_state["current_user"] = normalized
        st.session_state["page"] = "Asosiy sahifa"
        return True
    return False


def register_user(username: str, password: str, confirm: str) -> tuple[bool, str]:
    normalized = username.strip().lower()
    if len(normalized) < 3:
        return False, "Login kamida 3 ta belgidan iborat bo'lsin."
    if len(password) < 5:
        return False, "Parol kamida 5 ta belgidan iborat bo'lsin."
    if password != confirm:
        return False, "Parollar mos emas."
    if normalized in st.session_state["users"]:
        return False, "Bu login allaqachon mavjud."
    st.session_state["users"][normalized] = password
    st.session_state["is_authenticated"] = True
    st.session_state["current_user"] = normalized
    st.session_state["page"] = "Asosiy sahifa"
    return True, "Ro'yxatdan o'tildi."


def result_items(result: AnalysisResult, section: str) -> list[KeywordItem]:
    if section == "Kalit so'zlar":
        return result.top_keywords
    if section == "N-gramlar":
        return result.top_ngrams
    return result.top_phrases


def items_frame(items: list[KeywordItem]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"№": index, "Natija": item.term, "Ball": item.score, "Manba": item.source}
            for index, item in enumerate(items, start=1)
        ]
    )


def all_result_rows(result: AnalysisResult) -> list[list[str]]:
    rows: list[list[str]] = []
    for label, items in [
        ("keyword", result.top_keywords),
        ("ngram", result.top_ngrams),
        ("phrase", result.top_phrases),
    ]:
        rows.extend([[label, item.term, str(item.score), item.source] for item in items])
    return rows


def result_text(result: AnalysisResult) -> str:
    return "\n\n".join(
        [
            keywords_to_text("Kalit so'zlar", result.top_keywords),
            keywords_to_text("N-gramlar", result.top_ngrams),
            keywords_to_text("Muhim iboralar", result.top_phrases),
        ]
    )


def keyword_summary(result: AnalysisResult, limit: int = 12) -> str:
    terms = [item.term for item in result.top_keywords[:limit]]
    return ", ".join(terms) if terms else "Topilmadi"


def analysis_limit(text: str) -> int:
    return st.session_state.get("keywords_count", ANALYSIS_TOP_LIMIT)


def normalized_keyword_score(item: KeywordItem, max_score: float) -> str:
    if max_score <= 0:
        value = 0.0
    else:
        value = max(0.0, min(float(item.score) / max_score, 1.0))
    return f"{value:.2f}"


def render_keyword_cards(items: list[KeywordItem]) -> None:
    visible_items = items[:KEYWORD_DISPLAY_LIMIT]
    max_score = max((float(item.score) for item in visible_items), default=1.0)
    cards = []
    for index, item in enumerate(visible_items, start=1):
        cards.append(
            '<div class="keyword-result-item">'
            f'<span class="keyword-rank">{index}</span>'
            f'<span class="keyword-term">{html.escape(item.term)}</span>'
            f'<span class="keyword-score">{normalized_keyword_score(item, max_score)}</span>'
            "</div>"
        )
    card_html = "".join(cards) if cards else '<div class="keyword-result-item"><span class="keyword-term">Kalit so\'z topilmadi</span></div>'
    st.markdown(
        '<div class="keyword-result-card">'
        '<div class="keyword-result-head">'
        '<div class="keyword-result-title"><span class="keyword-result-icon">key</span>Kalit so\'zlar</div>'
        f'<div class="keyword-result-count">{len(visible_items)} ta kalit so\'z topildi</div>'
        "</div>"
        f'<div class="keyword-result-grid">{card_html}</div>'
        "</div>",
        unsafe_allow_html=True,
    )


def render_landing() -> None:
    st.markdown(
        """
        <div class="top-nav">
            <div class="brand"><span class="brand-mark">KW</span><span>KeyWord <span style="color:#4f46e5">AI</span></span></div>
            <div class="nav-links">
                <a class="active" href="#home">Bosh sahifa</a>
                <a href="#features">Xususiyatlar</a>
                <a href="#steps">Qanday ishlaydi?</a>
                <a href="#about">About</a>
                <a href="#contact">Aloqa</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _, login_col, reg_col = st.columns([0.73, 0.12, 0.15])
    with login_col:
        if st.button("Kirish", icon=":material/login:", use_container_width=True):
            st.session_state["auth_view"] = "login"
            st.session_state["show_auth_page"] = True
            st.rerun()
    with reg_col:
        if st.button("Ro'yxatdan o'tish", type="primary", icon=":material/person_add:", use_container_width=True):
            st.session_state["auth_view"] = "register"
            st.session_state["show_auth_page"] = True
            st.rerun()

    st.markdown(
        """
        <div id="home" class="hero">
          <div>
            <div class="pill">AI yordamida kalit so'zlar</div>
            <h1>Matndan kalit so'zlarni avtomatik <span>ajratib oling!</span></h1>
            <p>Sun'iy intellekt yordamida matnlaringizdan eng muhim so'z va iboralarni aniqlang. Tez, aniq va oson.</p>
          </div>
          <div class="hero-demo">
            <div class="demo-blob"></div>
            <div class="demo-card">
                <div class="demo-panel">
                    <div class="demo-title">Matn</div>
                    <div class="line" style="width:78%"></div>
                    <div class="line" style="width:68%"></div>
                    <div class="line" style="width:76%"></div>
                    <div class="line" style="width:90%"></div>
                    <div class="line" style="width:70%"></div>
                    <div class="line" style="width:84%"></div>
                    <div class="line" style="width:64%"></div>
                    <div class="line" style="width:78%"></div>
                </div>
                <div class="demo-panel">
                    <div class="demo-title">Kalit so'zlar</div>
                    <div class="chip-grid">
                        <div class="demo-chip">sun'iy intellekt</div>
                        <div class="demo-chip">kalit so'z</div>
                        <div class="demo-chip">matn</div>
                        <div class="demo-chip">texnologiya</div>
                        <div class="demo-chip">avtomatik</div>
                        <div class="demo-chip">ajratish</div>
                        <div class="demo-chip">tizim</div>
                        <div class="demo-chip">analiz</div>
                    </div>
                </div>
                <div class="arrow-bubble">›</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, _ = st.columns([0.18, 0.22, 0.60])
    with c1:
        if st.button("Boshlash", type="primary", icon=":material/arrow_forward:", use_container_width=True):
            st.session_state["auth_view"] = "login"
            st.session_state["show_auth_page"] = True
            st.rerun()
    with c2:
        if st.button("Ko'proq ma'lumot", icon=":material/info:", use_container_width=True):
            st.info("Tizim matn yoki fayldan kalit so'zlar, n-gramlar va muhim iboralarni chiqaradi.")

    st.markdown('<div id="steps" class="section-band"><div class="pill" style="margin:auto;display:flex;width:max-content">Qanday ishlaydi?</div><div class="section-title">Juda oddiy 3 qadam</div>', unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3, gap="large")
    steps = [
        ("1", "Matn kiriting", "Tahlil qilish uchun matningizni kiriting yoki joylang."),
        ("2", "Tahlil qilinadi", "AI algoritm matnni tahlil qilib, muhim so'zlarni aniqlaydi."),
        ("3", "Kalit so'zlar tayyor!", "Eng muhim kalit so'z va iboralarni natija sifatida oling."),
    ]
    for col, (icon, title, copy) in zip([s1, s2, s3], steps):
        with col:
            st.markdown(f'<div class="step-card"><div class="step-icon">{icon}</div><h3>{title}</h3><p>{copy}</p></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_auth() -> None:
    if not st.session_state.get("show_auth_page", False):
        render_landing()
        return

    st.markdown('<div class="brand"><span class="brand-mark">KW</span><span>KeyWord <span style="color:#4f46e5">AI</span></span></div>', unsafe_allow_html=True)
    copy_col, form_col = st.columns([0.58, 0.42], gap="large")
    with copy_col:
        st.markdown(
            """
            <div class="auth-copy-panel">
              <div class="pill">Xavfsiz demo kirish</div>
              <h1>Matn tahlili paneliga xush kelibsiz</h1>
              <p>KeyWord AI matn va hujjatlardan kalit so'zlar, n-gramlar va muhim iboralarni tezda ajratadi. Demo uchun <b>admin / 12345</b> yoki <b>demo / demo123</b> ishlaydi.</p>
              <div class="demo-card" style="width:100%;margin-top:28px;padding:18px;grid-template-columns:1fr 1fr;box-shadow:none">
                <div class="demo-panel" style="min-height:160px">
                  <div class="demo-title">Matn</div>
                  <div class="line" style="width:88%"></div>
                  <div class="line" style="width:72%"></div>
                  <div class="line" style="width:80%"></div>
                </div>
                <div class="demo-panel" style="min-height:160px">
                  <div class="demo-title">Natija</div>
                  <div class="chip-grid">
                    <div class="demo-chip">kalit so'z</div>
                    <div class="demo-chip">analiz</div>
                    <div class="demo-chip">matn</div>
                    <div class="demo-chip">AI</div>
                  </div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with form_col:
        with st.container(border=True):
            if st.session_state["auth_view"] == "login":
                st.markdown(
                    "<div class='auth-form-heading'>Kirish</div><div class='auth-form-copy'>Akkauntingizga kiring yoki demo login bilan davom eting.</div>",
                    unsafe_allow_html=True,
                )
                with st.form("login_form"):
                    username = st.text_input("Login", value="admin")
                    password = st.text_input("Parol", type="password", value="12345")
                    submitted = st.form_submit_button("Kirish", type="primary", use_container_width=True)
                if submitted:
                    if login_user(username, password):
                        st.rerun()
                    st.error("Login yoki parol noto'g'ri.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Ro'yxatdan o'tish", icon=":material/person_add:", use_container_width=True):
                        st.session_state["auth_view"] = "register"
                        st.rerun()
                with c2:
                    if st.button("Bosh sahifa", icon=":material/home:", use_container_width=True):
                        st.session_state["show_auth_page"] = False
                        st.rerun()
            else:
                st.markdown(
                    "<div class='auth-form-heading'>Ro'yxatdan o'tish</div><div class='auth-form-copy'>Yangi lokal demo akkaunt yarating.</div>",
                    unsafe_allow_html=True,
                )
                with st.form("register_form"):
                    username = st.text_input("Yangi login")
                    password = st.text_input("Parol", type="password")
                    confirm = st.text_input("Parolni tasdiqlang", type="password")
                    submitted = st.form_submit_button("Ro'yxatdan o'tish", type="primary", use_container_width=True)
                if submitted:
                    ok, message = register_user(username, password, confirm)
                    if ok:
                        st.rerun()
                    st.error(message)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Kirishga qaytish", icon=":material/login:", use_container_width=True):
                        st.session_state["auth_view"] = "login"
                        st.rerun()
                with c2:
                    if st.button("Bosh sahifa", icon=":material/home:", use_container_width=True):
                        st.session_state["show_auth_page"] = False
                        st.rerun()


def render_sidebar() -> None:
    st.markdown('<div class="side-section">', unsafe_allow_html=True)
    st.markdown('<div class="side-brand"><span class="brand-mark">KW</span><span>KeyWord <span style="color:#4f46e5">AI</span></span></div>', unsafe_allow_html=True)
    st.markdown('<div class="side-nav-scope"></div>', unsafe_allow_html=True)
    nav = [
        ("Asosiy sahifa", ":material/home:"),
        ("Tarix", ":material/history:"),
        ("Hujjatlarim", ":material/description:"),
        ("Sevimlilar", ":material/star:"),
        ("Yordam", ":material/help:"),
    ]
    for page, icon in nav:
        if st.button(page, key=f"nav_{page}", icon=icon, use_container_width=True):
            set_page(page)
            st.rerun()
    st.markdown(
        """
        <div class="side-card pro">
            <div class="side-card-title">Pro versiyaga o'ting</div>
            <p class="side-card-copy">Cheksiz matn, ko'proq funksiyalar va ustuvor qo'llab-quvvatlash.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Pro versiyani ochish", type="primary", icon=":material/workspace_premium:", use_container_width=True):
        st.info("Pro versiya demo loyihada maket sifatida ko'rsatilgan.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_topbar() -> None:
    _, lang_col, account_col = st.columns([0.78, 0.08, 0.14], gap="small")
    with lang_col:
        st.selectbox("Til", ["UZ", "RU", "EN"], key="language", label_visibility="collapsed")
    with account_col:
        choice = st.selectbox(
            "Akkaunt",
            ["account", "logout"],
            format_func=lambda value: f"A  {st.session_state['current_user'].title()}" if value == "account" else "Chiqish",
            label_visibility="collapsed",
        )
    if choice == "logout":
        st.session_state["is_authenticated"] = False
        st.session_state["current_user"] = ""
        st.session_state["auth_view"] = "login"
        st.session_state["show_auth_page"] = False
        st.rerun()


def render_home() -> None:
    if st.session_state.get("pending_analysis_text") is not None:
        st.session_state["analysis_text"] = st.session_state["pending_analysis_text"]
        st.session_state["analysis_text_input"] = st.session_state["pending_analysis_text"]
        st.session_state["pending_analysis_text"] = None

    st.markdown('<div class="page-title">Asosiy sahifa</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Matn kiriting yoki fayl yuklab, eng muhim kalit so\'zlarni oling.</div>', unsafe_allow_html=True)
    with st.container(border=True):
        col_left, col_right = st.columns([0.42, 0.58], gap="large")
        with col_left:
            st.markdown('<div class="dashboard-panel-title">1. Matn tahlili usulini tanlang</div>', unsafe_allow_html=True)
            st.session_state["method"] = st.radio(
                "Tahlil usuli",
                list(METHODS.keys()),
                captions=[METHODS[name][1] for name in METHODS],
                key="method_radio",
                label_visibility="collapsed",
            )
            compare = st.checkbox("Uslubni solishtirish")
        with col_right:
            top_title, clear_col = st.columns([0.72, 0.28])
            with top_title:
                st.markdown('<div class="dashboard-panel-title">2. Matn kiriting yoki fayl yuklang</div>', unsafe_allow_html=True)
            with clear_col:
                if st.button("Tozalash", icon=":material/delete:", use_container_width=True):
                    st.session_state["analysis_text"] = ""
                    st.session_state["analysis_text_input"] = ""
                    st.session_state["analysis_result"] = None
                    st.session_state["last_uploaded_file_id"] = ""
                    st.rerun()
            st.markdown(
                '<div class="input-tabs"><span class="active"><i class="tab-icon">edit_note</i>Matn kiritish</span><span><i class="tab-icon">upload_file</i>Fayl yuklash</span></div>',
                unsafe_allow_html=True,
            )
            text_col, file_col = st.columns([0.58, 0.42], gap="medium")
            with text_col:
                text = st.text_area(
                    "Matn kiritish",
                    key="analysis_text_input",
                    height=245,
                    placeholder="Matningizni bu yerga kiriting...",
                )
                st.session_state["analysis_text"] = text
                st.caption(f"{len(text)} / 5000 belgi")
                if st.button("Namuna matn yuklash", icon=":material/upload_file:", use_container_width=True):
                    st.session_state["pending_analysis_text"] = SAMPLE_TEXT
                    st.rerun()
            with file_col:
                uploaded = st.file_uploader("Fayl yuklash", type=["txt", "md", "csv", "docx"])
                st.caption("TXT, MD, CSV va DOCX fayllar qo'llab-quvvatlanadi.")
            if uploaded is not None:
                uploaded_bytes = uploaded.getvalue()
                uploaded_id = f"{uploaded.name}:{len(uploaded_bytes)}"
                if uploaded_id != st.session_state.get("last_uploaded_file_id"):
                    try:
                        text = extract_text_from_file(uploaded.name, uploaded_bytes)
                        st.session_state["pending_analysis_text"] = text
                        st.session_state["last_uploaded_file_id"] = uploaded_id
                        docs = st.session_state["documents"]
                        if uploaded.name not in [doc["Hujjat nomi"] for doc in docs]:
                            docs.insert(
                                0,
                                {
                                    "Hujjat nomi": uploaded.name,
                                    "Turi": Path(uploaded.name).suffix.upper().lstrip("."),
                                    "Hajmi": f"{len(uploaded_bytes) / 1024:.1f} KB",
                                    "Yuklangan sana": datetime.now().strftime("%d.%m.%Y %H:%M"),
                                },
                            )
                        st.success("Fayldagi matn o'qildi.")
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
                else:
                    st.caption(f"Yuklangan fayl: {uploaded.name}")

    _, run_col, _ = st.columns([0.25, 0.5, 0.25])
    with run_col:
        st.markdown('<div class="dashboard-panel-title">3. Kalit so\'zlar sonini tanlang</div>', unsafe_allow_html=True)
        st.session_state["keywords_count"] = st.slider(
            "Necha ta kalit so'z kerak?",
            min_value=5,
            max_value=50,
            value=st.session_state.get("keywords_count", 20),
            step=5,
            label_visibility="collapsed",
        )
        st.caption(f"Tanlangan: {st.session_state['keywords_count']} ta kalit so'z (qo'shimcha so'zsiz)")
        
    _, run_col, _ = st.columns([0.25, 0.5, 0.25])
    with run_col:
        run = st.button("Kalit so'zlarni topish", type="primary", icon=":material/search:", use_container_width=True)
    if run:
        source_text = st.session_state.get("analysis_text", "")
        if not source_text.strip():
            st.warning("Tahlil qilish uchun matn kiriting yoki fayl yuklang.")
        else:
            with st.spinner("Matn tahlil qilinmoqda..."):
                result = analyze_text(source_text, top_k=analysis_limit(source_text))
            st.session_state["analysis_result"] = result
            st.session_state["analysis_history"].insert(
                0,
                {
                    "Matn sarlavhasi": source_text[:42] + ("..." if len(source_text) > 42 else ""),
                    "Usul": "Solishtirish" if compare else st.session_state["method"],
                    "Kalit so'zlar": keyword_summary(result),
                    "Sana": datetime.now().strftime("%d.%m.%Y %H:%M"),
                },
            )
            st.success("Tahlil tayyor.")

    if st.session_state.get("analysis_result") is not None:
        render_results(st.session_state["analysis_result"])
    else:
        render_recent()


def render_results(result: AnalysisResult) -> None:
    st.markdown("### Tahlil natijalari")
    m1, m2, m3 = st.columns(3)
    m1.metric("So'zlar soni", result.total_words)
    m2.metric("Unikal so'zlar", result.unique_words)
    m3.metric("Top kalitlar", len(result.top_keywords))

    render_keyword_cards(result.top_keywords)
    keyword_frame = items_frame(result.top_keywords[:KEYWORD_DISPLAY_LIMIT])
    d1, d2 = st.columns(2)
    d1.download_button(
        "Natijani TXT yuklab olish",
        data=keywords_to_text("Kalit so'zlar", result.top_keywords[:KEYWORD_DISPLAY_LIMIT]).encode("utf-8"),
        file_name="keywords.txt",
        mime="text/plain",
        icon=":material/download:",
        use_container_width=True,
    )
    d2.download_button(
        "Natijani CSV yuklab olish",
        data=rows_to_csv_bytes(keyword_frame.columns.tolist(), keyword_frame.astype(str).values.tolist()),
        file_name="keywords.csv",
        mime="text/csv",
        icon=":material/download:",
        use_container_width=True,
    )

    with st.expander("N-gramlar va muhim iboralar"):
        sections = [
            ("N-gramlar", result.top_ngrams),
            ("Muhim iboralar", result.top_phrases),
        ]
        for title, items in sections:
            st.markdown(f"#### {title}")
            frame = items_frame(items[:KEYWORD_DISPLAY_LIMIT])
            if frame.empty:
                st.info(f"{title} topilmadi.")
            else:
                st.table(frame.set_index("№"))

    st.markdown("#### Barcha natijalar")
    st.text_area("Nusxalash uchun tayyor matn", value=result_text(result), height=180)
    rows = all_result_rows(result)
    c1, c2, c3 = st.columns(3)
    c1.download_button("Barchasini TXT yuklab olish", data=result_text(result).encode("utf-8"), file_name="analysis_all.txt", mime="text/plain", icon=":material/download:", use_container_width=True)
    c2.download_button("Barchasini CSV yuklab olish", data=rows_to_csv_bytes(["Type", "Term", "Score", "Source"], rows), file_name="analysis_all.csv", mime="text/csv", icon=":material/download:", use_container_width=True)
    if c3.button("Sevimlilarga qo'shish", icon=":material/star:", use_container_width=True):
        if not result.top_keywords:
            st.warning("Sevimlilarga qo'shish uchun natija yo'q.")
        else:
            st.session_state["favorites"] = items_frame(result.top_keywords).head(10).to_dict("records")
            st.success("Natija sevimlilarga qo'shildi.")


def render_recent(show_button: bool = True) -> None:
    st.divider()
    st.markdown("### So'nggi tahlillar")
    history = st.session_state["analysis_history"]
    if not history:
        history = [
            {"Matn sarlavhasi": "Sun'iy intellekt haqida", "Usul": "TF-IDF", "Kalit so'zlar": "sun'iy, intellekt, texnologiya, ma'lumotlar", "Sana": "24.05.2024 15:30"},
            {"Matn sarlavhasi": "Ekologiya va atrof-muhit", "Usul": "TF-IDF", "Kalit so'zlar": "ekologiya, atrof-muhit, tabiat, himoya", "Sana": "23.05.2024 10:12"},
            {"Matn sarlavhasi": "Raqamli marketing strategiyalari", "Usul": "TextRank", "Kalit so'zlar": "marketing, strategiya, raqamli, reklama", "Sana": "22.05.2024 09:45"},
            {"Matn sarlavhasi": "Blockchain texnologiyasi", "Usul": "N-gram", "Kalit so'zlar": "blockchain, texnologiya, tarmoq, xavfsizlik", "Sana": "21.05.2024 18:20"},
        ]
    if show_button:
        top, btn = st.columns([0.82, 0.18])
        with btn:
            if st.button("Barchasini ko'rish", key="recent_show_all", icon=":material/arrow_forward:", use_container_width=True):
                set_page("Tarix")
                st.rerun()
    st.table(pd.DataFrame(history[:6]))


def render_history() -> None:
    st.markdown('<div class="page-title">Tarix</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Avval tahlil qilingan matnlar tarixi.</div>', unsafe_allow_html=True)
    render_recent(show_button=False)


def render_documents() -> None:
    st.markdown('<div class="page-title">Hujjatlarim</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Yuklangan hujjatlaringiz ro\'yxati.</div>', unsafe_allow_html=True)
    if st.button("Yangi hujjat yuklash", type="primary", icon=":material/upload_file:"):
        set_page("Asosiy sahifa")
        st.rerun()
    docs = st.session_state["documents"] or [
        {"Hujjat nomi": "suniy_intellekt.docx", "Turi": "DOCX", "Hajmi": "24.5 KB", "Yuklangan sana": "24.05.2024 15:28"},
        {"Hujjat nomi": "ekologiya.txt", "Turi": "TXT", "Hajmi": "8.2 KB", "Yuklangan sana": "23.05.2024 10:10"},
    ]
    st.dataframe(pd.DataFrame(docs), use_container_width=True, hide_index=True)


def render_favorites() -> None:
    st.markdown('<div class="page-title">Sevimlilar</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Sevimlilarga qo\'shilgan natijalar.</div>', unsafe_allow_html=True)
    favorites = st.session_state["favorites"]
    if favorites:
        st.dataframe(pd.DataFrame(favorites), use_container_width=True, hide_index=True)
    else:
        st.info("Hozircha sevimli natija yo'q.")


def render_help() -> None:
    st.markdown('<div class="page-title">Yordam</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Ko\'p beriladigan savollar va foydali ma\'lumotlar.</div>', unsafe_allow_html=True)
    questions = {
        "Hisob qanday yaratiladi?": "Ro'yxatdan o'tish oynasida login va parol kiriting. Demo uchun admin / 12345 ishlaydi.",
        "Matn qanday tahlil qilinadi?": "Asosiy sahifada matn kiriting yoki fayl yuklang va Kalit so'zlarni topish tugmasini bosing.",
        "Natijani qanday saqlayman?": "Natijalar bo'limida TXT yoki CSV yuklab olish tugmalaridan foydalaning.",
        "Qaysi fayllar qo'llab-quvvatlanadi?": "TXT, MD, CSV va DOCX fayllar qo'llab-quvvatlanadi.",
    }
    for question, answer in questions.items():
        with st.expander(question):
            st.write(answer)


def render_dashboard() -> None:
    st.markdown('<div class="dashboard-layout">', unsafe_allow_html=True)
    side_col, main_col = st.columns([0.18, 0.82], gap="large")
    with side_col:
        render_sidebar()
    with main_col:
        render_topbar()
        page = st.session_state["page"]
        if page == "Asosiy sahifa":
            render_home()
        elif page == "Tarix":
            render_history()
        elif page == "Hujjatlarim":
            render_documents()
        elif page == "Sevimlilar":
            render_favorites()
        else:
            render_help()
    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    init_state()
    if st.session_state["is_authenticated"]:
        render_dashboard()
    else:
        render_auth()


if __name__ == "__main__":
    main()
