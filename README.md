# PaketLens — Ürün İçerik Analizi

Ürün paketinin fotoğrafını yükle, yapay zeka içindeki bileşenleri okusun ve zararlı mı yararlı mı söylesin.

## Kurulum



Tarayıcıda `(https://food-analizer-agent.onrender.com/)` adresine git.

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

