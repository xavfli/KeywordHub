# KeywordHub

`KeywordHub` is a Streamlit-based keyword research workspace for analyzing text and collecting live search suggestions in one place.

It is designed for fast content research workflows:

- extract keywords from raw text
- detect 2-word and 3-word n-grams
- surface important phrases with RAKE and optional KeyBERT support
- fetch live suggestions from Google, YouTube, and Bing
- export results as `TXT` or `CSV`

## What It Does

KeywordHub has two main modules:

### 1. Text Analysis

Use this mode to process pasted text or uploaded files and identify meaningful terms.

Included analysis methods:

- frequency-based keyword scoring
- TF-IDF keyword extraction
- 2-gram and 3-gram detection
- RAKE phrase extraction
- optional KeyBERT phrase extraction with graceful fallback

Supported input files:

- `.txt`
- `.md`
- `.csv`

### 2. Search Suggestions

Use this mode to discover real-time suggestion ideas from:

- Google
- YouTube
- Bing

The app also builds clickable result URLs for each suggestion so you can continue research directly from the interface.

## Features

- Streamlit web interface with a polished responsive layout
- multilingual token handling for English, Uzbek, and Russian text
- built-in stopword filtering
- combined keyword scoring from frequency and TF-IDF
- phrase extraction with fallback behavior when optional NLP dependencies are unavailable
- parallel suggestion fetching with async requests
- export to `TXT` and `CSV`

## Project Structure

```text
.
|-- app.py
|-- requirements.txt
|-- keywordhub/
|   |-- __init__.py
|   |-- analyzer.py
|   |-- exporters.py
|   `-- suggestions.py
`-- README.md
```

## Installation

### 1. Clone the repository from GitHub

```powershell
git clone https://github.com/xavfli/KeywordHub.git
cd KeywordHub
```

### 2. Create a virtual environment

```powershell
python -m venv venv
```

### 3. Activate the virtual environment

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run The App

```powershell
python -m streamlit run app.py
```

Default local URL:

```text
http://localhost:8501
```

## Usage

### Text Analysis Workflow

1. Open the `Matn tahlili` section.
2. Paste text or upload a supported file.
3. Choose how many top results you want.
4. Run the analysis.
5. Export keyword, n-gram, or phrase results as `TXT` or `CSV`.

### Suggestion Research Workflow

1. Open the `Qidiruv takliflari` section.
2. Enter a seed query.
3. Let the app auto-refresh or click the fetch button.
4. Review suggestions from Google, YouTube, and Bing.
5. Export the combined list if needed.

## Dependencies

Main libraries used in this project:

- `streamlit`
- `httpx`
- `pandas`
- `scikit-learn`
- `rake-nltk`
- `keybert`
- `nltk`

## Notes

- `KeyBERT` is treated as optional at runtime. If it cannot be imported or its deep-learning dependencies are missing, the app still works with TF-IDF, n-grams, and RAKE.
- Search suggestion results depend on internet access and third-party service availability.
- Uploaded files are decoded as UTF-8 with graceful fallback behavior.

## Best For

KeywordHub is useful for:

- SEO keyword discovery
- content planning
- topic clustering
- blog outline preparation
- search intent exploration
- multilingual text analysis experiments

## Quick Start

If your environment is already prepared:

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m streamlit run app.py
```

## License

No license file is currently included in this repository. Add one if you want to define reuse terms explicitly.
