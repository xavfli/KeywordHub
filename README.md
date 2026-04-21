# KeywordHub

`KeywordHub` bu `pure Python` asosida yozilgan kalit so'z tahlili va live search suggestion platformasi. Ilova `Streamlit` bilan ishlaydi va ikki asosiy bo'limdan iborat:

- `Matn tahlili` - matndan kalit so'zlar, n-gramlar va muhim iboralarni ajratadi
- `Qidiruv takliflari` - Google, YouTube va Bing dan live suggestion olib keladi

## Asosiy imkoniyatlar

- TF-IDF orqali kalit so'zlarni topish
- 2 va 3 so'zli n-gramlarni ajratish
- Stop-word filtrlash
- RAKE asosida muhim iboralarni topish
- KeyBERT mavjud bo'lsa, qo'shimcha semantik phrase extraction
- Google, YouTube, Bing suggestion API laridan parallel natija olish
- TXT va CSV formatda eksport
- Fayldan matn yuklash: `.txt`, `.md`, `.csv`

## Loyiha tuzilmasi

- `app.py` - Streamlit interfeys
- `keywordhub/analyzer.py` - matn tahlili logikasi
- `keywordhub/suggestions.py` - qidiruv takliflari uchun API chaqiriqlari
- `keywordhub/exporters.py` - TXT va CSV eksport yordamchilari
- `requirements.txt` - kerakli kutubxonalar ro'yxati

## O'rnatish

### 1. Virtual environment yaratish

```powershell
python -m venv venv
```

### 2. Virtual environment ni yoqish

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Kutubxonalarni o'rnatish

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Ilovani ishga tushirish

```powershell
python -m streamlit run app.py
```

Brauzerda odatda shu manzil ochiladi:

```text
http://localhost:8501
```

## Muhim eslatmalar

- `KeyBERT` importi endi `lazy load` qilingan. Agar u yoki unga bog'liq `torch/torchvision` kutubxonalari bo'lmasa ham, ilova ochiladi.
- `KeyBERT` ishlamasa, ilova TF-IDF, n-gram va RAKE bilan ishlashda davom etadi.
- Internet bo'lmasa yoki API cheklansa, `suggestion` bo'limida ayrim manbalardan natija chiqmasligi mumkin.

## Qisqa ishga tushirish

Agar `venv` allaqachon tayyor bo'lsa:

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m streamlit run app.py
```
