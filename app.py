import os
from flask import Flask, render_template, request, jsonify
from analyzer import analizeaza_squat

app = Flask(__name__)
FOLDER_UPLOAD = os.path.join("static", "uploads")
app.config["UPLOAD_FOLDER"] = FOLDER_UPLOAD

EXTENSII_PERMISE = {"mp4", "mov", "avi", "mkv"}


def fisier_valid(nume):
    return "." in nume and nume.rsplit(".", 1)[1].lower() in EXTENSII_PERMISE


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analizeaza", methods=["POST"])
def analizeaza():
    if "video" not in request.files:
        return jsonify({"eroare": "Niciun fișier încărcat."}), 400

    fisier = request.files["video"]
    if fisier.filename == "" or not fisier_valid(fisier.filename):
        return jsonify({"eroare": "Fișier invalid."}), 400

    cale = os.path.join(app.config["UPLOAD_FOLDER"], fisier.filename)
    fisier.save(cale)

    rezultat = analizeaza_squat(cale)
    return jsonify(rezultat)


if __name__ == "__main__":
    app.run(debug=True)
