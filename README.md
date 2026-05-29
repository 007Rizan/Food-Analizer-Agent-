# PaketLens — Ürün İçerik Analizi

Ürün paketinin fotoğrafını yükle, yapay zeka içindeki bileşenleri okusun ve zararlı mı yararlı mı söylesin.

## Kurulum

```bash
# 1. Sanal ortam oluştur
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Bağımlılıkları yükle
pip install -r requirements.txt

# 3. Anthropic API anahtarını ayarla
export ANTHROPIC_API_KEY="sk-ant-..."   # Windows: set ANTHROPIC_API_KEY=sk-ant-...

# 4. Uygulamayı başlat
python app.py
```

Tarayıcıda `http://localhost:5000` adresine git.

## Nasıl Çalışır?

1. Ürün paketinin fotoğrafını yükle (PNG/JPG/WEBP)
2. "Analiz Et" butonuna tıkla
3. Claude Vision API paketteki bileşenleri okur
4. Sonuç: Sağlık skoru, zararlı/yararlı maddeler listesi, genel değerlendirme

## Dosya Yapısı

```
paket-analiz/
├── app.py              # Flask uygulaması
├── requirements.txt    # Bağımlılıklar
├── templates/
│   └── index.html      # Arayüz
└── README.md
```
# Food-Analizer-Agent-
