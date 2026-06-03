import os
import base64
import json
import io
from flask import Flask, render_template, request, jsonify
import anthropic
from PIL import Image, ImageFilter, ImageOps, ImageEnhance

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def to_jpeg_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def filters(image_data: bytes) -> tuple[bytes, bytes, bytes]:
    """
    filtre fonksyonumuz filtrelerimiz sırasıyla şöyledir:

    Filtre 1 : Gaussian Blur filtresi + Sharpen gürültü azaltma (gürültü azalt, sonra keskinleştir)
    Filtre 2 :Histogram Equalization (kontrast iyileştirme)
    Filtre 3: Grayscale + Contrast Boost (siyah-beyaz + yüksek kontrast)
    """
    original = Image.open(io.BytesIO(image_data)).convert("RGB")

    # --- Filtre 1: Gaussian Blur ve Sharpen ---
    f1 = original.copy()
    f1 = f1.filter(ImageFilter.GaussianBlur(radius=1))
    f1 = f1.filter(ImageFilter.SHARPEN)
    f1 = f1.filter(ImageFilter.SHARPEN)

    # --- Filtre 2: Histogram Equalization (kontrast) ---
    f2 = original.copy()
    r, g, b = f2.split()
    f2 = Image.merge("RGB", (ImageOps.equalize(r), ImageOps.equalize(g), ImageOps.equalize(b)))

    # --- Filtre 3: Grayscale + Contrast Boost ---
    f3 = original.copy().convert("L")          # gri tonlama
    f3 = ImageOps.equalize(f3)                 # kontrast eşitleme
    f3 = ImageEnhance.Contrast(f3).enhance(2.5) # kontrast x2.5
    f3 = f3.convert("RGB")

    return to_jpeg_bytes(f1), to_jpeg_bytes(f2), to_jpeg_bytes(f3)


def analyze_package(f1: bytes, f2: bytes, f3: bytes) -> dict:
    def b64(data): return base64.standard_b64encode(data).decode("utf-8")

    prompt = """Sana aynı ürün paketinin 3 farklı görüntü işleme filtresi uygulanmış hali gönderildi:
- Görsel 1: Gaussian Blur + Keskinleştirme filtresi
- Görsel 2: Histogram Eşitleme (kontrast iyileştirme) filtresi  
- Görsel 3: Gri tonlama + Yüksek Kontrast filtresi

Görevin:
1. 3 görseldeki metinleri oku. Aynı kelime farklı okunuyorsa en anlamlı ve en muhtemel olanı kabul et.
2. İçindekiler/bileşenler listesini bu üç görselden en doğru şekilde derle.
3. Her bileşeni beslenme ve gıda güvenliği açısından değerlendir.
4. 0-100 arası sağlık skoru ver.
5. Türkçe analiz yap.

Yanıtını SADECE şu JSON formatında ver (başka hiçbir şey yazma, markdown kullanma):
{
  "urun_adi": "...",
  "tespit_edilen_icerik": ["madde1", "madde2"],
  "zararli_maddeler": [{"ad": "...", "aciklama": "..."}],
  "yararli_maddeler": [{"ad": "...", "aciklama": "..."}],
  "saglik_skoru": 75,
  "genel_degerlendirme": "...",
  "tavsiye": "...",
  "sonuc": "yararli"
}
"sonuc" alanı sadece "yararli", "zararli" veya "dikkatli" olabilir."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1500,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64(f1)}},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64(f2)}},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64(f3)}},
                    {"type": "text", "text": prompt}
                ],
            }
        ],
    )

    raw = message.content[0].text.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    if "image" not in request.files:
        return jsonify({"error": "Gorsel yuklenmedi"}), 400

    file = request.files["image"]
    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "Gecersiz dosya"}), 400

    image_data = file.read()

    try:
        f1, f2, f3 = filters(image_data)
        result = analyze_package(f1, f2, f3)
        return jsonify({"success": True, "data": result})
    except json.JSONDecodeError:
        return jsonify({"error": "AI yaniti islenemedi, tekrar deneyin"}), 500
    except Exception as e:
        return jsonify({"error": f"Analiz hatasi: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
