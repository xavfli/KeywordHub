# KeyWord AI

KeyWord AI - matn yoki fayldan kalit so'zlar, n-gramlar va muhim iboralarni avtomatik ajratib beruvchi Streamlit ilova.

## Nimalar Bor

- Landing sahifa: bosh sahifa, kirish va ro'yxatdan o'tish tugmalari
- Demo login/register
- Dashboard: asosiy sahifa, tarix, hujjatlar, sevimlilar va yordam
- Matn kiritish yoki `.txt`, `.md`, `.csv`, `.docx` fayl yuklash
- TF-IDF, N-gram, TextRank, YAKE va RAKE usul tanlovi
- Kalit so'zlar, n-gramlar va muhim iboralarni jadvalda ko'rish
- TXT va CSV eksport
- Yuklangan hujjatlar ro'yxati
- Sevimlilarga natija qo'shish

## Demo Login

```text
Login: admin
Parol: 12345
```

```text
Login: demo
Parol: demo123
```

```text
Login: asad
Parol: 12345
```

## O'rnatish

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Ishga Tushirish

```powershell
streamlit run app.py
```

Brauzerda:

```text
http://localhost:8501
```

## Loyiha Tuzilishi

```text
.
|-- app.py
|-- requirements.txt
|-- README.md
|-- LICENSE
|-- keywordhub/
|   |-- analyzer.py
|   |-- exporters.py
|   `-- suggestions.py
```

## License

MIT License. Batafsil: [LICENSE](LICENSE).
