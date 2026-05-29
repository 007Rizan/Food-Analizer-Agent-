import os
import base64
import json
from flask import Flask, render_template, request, jsonify
import anthropic

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def analyze_package(image_data: bytes, media_type: str) -> dict:
    image_b64 = base64.standard_b64encode(image_data).decode("utf-8")

    prompt = """Sen bir beslenme ve gida guvenligi uzmanisın.
Sana bir urunun fotografı gonderildi.
Gorev:
1. Paketteki bilesen/icindekiler listesini oku (varsa)
2. Her bileseni degerlendir
3. Genel bir saglik skoru ver (0-100 arasi)
4. Turkce, net ve anlasilir bir analiz sun

Yanitini SADECE su JSON formatinda ver (baska hicbir sey yazma, markdown kullanma):
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
"sonuc" alani sadece "yararli", "zararli" veya "dikkatli" olabilir."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1500,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ],
            }
        ],
    )

    raw = message.content[0].text.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    return json.loads(raw)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    if "image" not in request.files:
        return jsonify({"error": "Gorsel yuklenmedi"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Dosya secilmedi"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Desteklenmeyen dosya turu"}), 400

    ext = file.filename.rsplit('.', 1)[1].lower()
    media_type_map = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "png": "image/png", "webp": "image/webp", "gif": "image/gif"
    }
    media_type = media_type_map.get(ext, "image/jpeg")
    image_data = file.read()

    try:
        result = analyze_package(image_data, media_type)
        return jsonify({"success": True, "data": result})
    except json.JSONDecodeError:
        return jsonify({"error": "AI yaniti islenemedi, tekrar deneyin"}), 500
    except Exception as e:
        return jsonify({"error": f"Analiz hatasi: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
