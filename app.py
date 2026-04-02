import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from analyzer import analizeaza_squat
from db import init_db, salveaza_sesiune, obtine_istoric, adauga_utilizator, verifica_utilizator

app = Flask(__name__)
app.secret_key = "cheie_secreta_licenta"  # Necesar pentru sesiuni
FOLDER_UPLOAD = os.path.join("static", "uploads")
app.config["UPLOAD_FOLDER"] = FOLDER_UPLOAD

EXTENSII_PERMISE = {"mp4", "mov", "avi", "mkv"}

# Inițializăm baza de date la pornire
init_db()


def fisier_valid(nume):
    return "." in nume and nume.rsplit(".", 1)[1].lower() in EXTENSII_PERMISE


@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username")
        parola = request.form.get("password")
        user_id = verifica_utilizator(user, parola)
        if user_id:
            session["user_id"] = user_id
            session["username"] = user
            return redirect(url_for("index"))
        return render_template("login.html", eroare="Utilizator sau parolă incorectă.")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = request.form.get("username")
        parola = request.form.get("password")
        if adauga_utilizator(user, parola):
            return redirect(url_for("login"))
        return render_template("login.html", eroare="Utilizatorul există deja.", register=True)
    return render_template("login.html", register=True)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/analizeaza", methods=["POST"])
def analizeaza():
    if "user_id" not in session:
        return jsonify({"eroare": "Trebuie să fii logat."}), 401
        
    if "video" not in request.files:
        return jsonify({"eroare": "Niciun fișier încărcat."}), 400

    fisier = request.files["video"]
    if fisier.filename == "" or not fisier_valid(fisier.filename):
        return jsonify({"eroare": "Fișier invalid."}), 400

    cale = os.path.join(app.config["UPLOAD_FOLDER"], fisier.filename)
    fisier.save(cale)

    rezultat = analizeaza_squat(cale)
    
    if "eroare" not in rezultat:
        salveaza_sesiune(
            rezultat["exercitiu"],
            rezultat["repetari"],
            rezultat["scor"],
            rezultat["feedback"]
        )
        
    return jsonify(rezultat)


@app.route("/istoric_date")
def istoric_date():
    if "user_id" not in session:
        return jsonify([]), 401
    return jsonify(obtine_istoric())


@app.route("/istoric")
def istoric():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("istoric.html")


if __name__ == "__main__":
    app.run(debug=True)
