# KeyWord AI

KeyWord AI - matn yoki fayldan kalit so'zlar, n-gramlar va muhim iboralarni avtomatik ajratib beruvchi Streamlit dashboard.

Loyiha “Matnlardan kalit so'zlarni avtomatik ajratish” mavzusini amaliy ko'rinishda namoyish qiladi: foydalanuvchi matn kiritadi yoki fayl yuklaydi, tizim esa kalit so'zlar, n-gramlar va muhim iboralarni jadval ko'rinishida chiqaradi.

## Nimalar Bor

- Professional landing sahifa
- Kirish va ro'yxatdan o'tish oynalari
- Demo accountlar
- Sidebarli dashboard
- Matn kiritish yoki fayl yuklash
- `.txt`, `.md`, `.csv`, `.docx` fayllarni qo'llab-quvvatlash
- TF-IDF, N-gram, TextRank, YAKE va RAKE usul tanlovi
- Kalit so'zlar, n-gramlar va muhim iboralarni chiqarish
- Matndagi barcha topilgan kalit so'zlarni jadvalda ko'rsatish
- TXT va CSV eksport
- So'nggi tahlillar tarixi
- Yuklangan hujjatlar ro'yxati
- Sevimlilarga natija qo'shish
- O'zbek, rus va ingliz stopword/tokenlash qo'llab-quvvatlovi

## Qo'shimcha So'zlarni Filtrlash

Tizim matndan kalit so'zlarni ajratishda quyidagi qo'shimcha/auxilary so'zlarni avtomatik ravishda chiqarib tashlaydi:

- **Haqida**: "haqida", "haqidagi" - matn yoki mavzu haqida
- **O'lcham**: "kichik", "katta", "uzoq", "qisqa" - hajm va o'lcham xususiyatlari
- **Yo'nalish**: "tomonidan", "tomoni", "beri", "orta", "yuqori", "pastki" - joylashuv xususiyatlari
- **Savollar**: "savol", "savolli", "savollash" - so'roq xususiyatlari
- **Boshqa**: "kabi", "misol", "oddiy", "murakkab", "xusus", "umumiy" - taqqoslash va umumiy xususiyatlar

Bu filtrlash natijalarning sifatini yaxshilaydi va faqat haqiqiy muhim kalit so'zlarni ta'kidlaydi.

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

## Foydalanish

1. Ilovani ishga tushiring.
2. `Kirish` tugmasini bosing.
3. Demo accountlardan biri bilan tizimga kiring.
4. `Asosiy sahifa`da tahlil usulini tanlang.
5. Matn kiriting yoki fayl yuklang.
6. `Kalit so'zlarni topish` tugmasini bosing.
7. Natijalarni jadvalda ko'ring yoki TXT/CSV formatida yuklab oling.

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

## Asosiy Fayllar

- `app.py` - Streamlit interfeys, login/register, dashboard va natija chiqarish.
- `keywordhub/analyzer.py` - matnni tozalash, tokenlash, kalit so'z, n-gram va ibora ajratish.
- `keywordhub/exporters.py` - TXT va CSV eksport funksiyalari.
- `requirements.txt` - kerakli Python kutubxonalari.

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

## Texnik Eslatmalar

- Fayldagi HTML/CSS taglari analizdan oldin tozalanadi.
- Natijalar HTML sifatida emas, oddiy Streamlit jadvalida chiqadi.
- Tahlil natijasi 20 ta bilan cheklanmaydi; matndagi topilgan kalit so'zlar imkon qadar to'liq ko'rsatiladi.
- Demo login production xavfsizligi uchun emas, faqat test va taqdimot uchun.
- **Qo'shimcha Filtrlash**: Tizim qizil bilan ko'rsatilgan qo'shimcha so'zlarni (haqida, uzoq, tomonidan, kichik, beri, savol va shunga o'xshashlarni) avtomatik ravishda natijalardan chiqarib tashlaydi. Bu kalit so'zlarning sifatini oshiradi va faqat o'ziga xos muhim so'zlarni chiqaradi.
- **Automatik Kompensatsiya**: Filtrlashdan keyin natijalar 20 tadan kam bo'lsa, tizim qo'shimcha nomzodlarni tahlil qiladi va sifatli natijalarni to'ldiradi.

## License

MIT License. Batafsil: [LICENSE](LICENSE).
