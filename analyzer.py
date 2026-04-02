import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import urllib.request
import os

MODEL_PATH = "pose_landmarker.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
)

# Indici landmark MediaPipe
UMAR_STANG     = 11
SOLD_STANG     = 23
GENUNCHI_STANG = 25
GLEZNA_STANGA  = 27

# Conexiuni schelet pentru desenat pe canvas (fără mâini)
CONEXIUNI = [
    (11, 12),           # Umeri
    (11, 23), (12, 24), # Torso (Umeri -> Șolduri)
    (23, 24),           # Șolduri
    (23, 25), (25, 27), # Picior stâng
    (24, 26), (26, 28), # Picior drept
]


def verifica_model():
    if not os.path.exists(MODEL_PATH):
        print("Se descarcă modelul de poză (doar la primul rulare)...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("Model descărcat.")


def calculeaza_unghi_3d(a, b, c):
    a = np.array([a.x, a.y, a.z])
    b = np.array([b.x, b.y, b.z])
    c = np.array([c.x, c.y, c.z])
    ba = a - b
    bc = c - b
    cos_unghi = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    return float(np.degrees(np.arccos(np.clip(cos_unghi, -1.0, 1.0))))


def corp_este_vertical(lm_world):
    umar = np.array([lm_world[UMAR_STANG].x, lm_world[UMAR_STANG].y])
    sold  = np.array([lm_world[SOLD_STANG].x,  lm_world[SOLD_STANG].y])
    diff = sold - umar
    return abs(diff[1]) > abs(diff[0])


def analizeaza_squat(cale_video):
    verifica_model()

    cap = cv2.VideoCapture(cale_video)
    if not cap.isOpened():
        return {"eroare": "Nu s-a putut deschide fișierul video."}

    fps = cap.get(cv2.CAP_PROP_FPS) or 30

    optiuni_baza = python.BaseOptions(model_asset_path=MODEL_PATH)
    optiuni = vision.PoseLandmarkerOptions(base_options=optiuni_baza)
    detector = vision.PoseLandmarker.create_from_options(optiuni)

    repetari = 0
    in_squat = False
    scoruri_cadre = []
    cadre_cu_persoana = 0
    cadre_cu_miscare_squat = 0
    total_cadre = 0
    date_cadre = []  # date schelet per cadru, trimise la frontend

    # Pentru stabilitate - memorăm ultima poziție validă
    last_lm_smooth = None
    last_world_smooth = None
    ALPHA = 0.2  # Factor de netezire (0.1 = foarte stabil/lent, 0.9 = reactiv/jittery)

    while cap.isOpened():
        ret, cadru = cap.read()
        if not ret:
            break

        total_cadre += 1
        cadru_rgb = cv2.cvtColor(cadru, cv2.COLOR_BGR2RGB)
        imagine = mp.Image(image_format=mp.ImageFormat.SRGB, data=cadru_rgb)
        rezultat = detector.detect(imagine)

        if not rezultat.pose_world_landmarks:
            date_cadre.append(None)
            continue

        cadre_cu_persoana += 1
        
        # Landmark-uri brute
        raw_world = rezultat.pose_world_landmarks[0]
        raw_img   = rezultat.pose_landmarks[0]

        # 1. Aplicăm filtrul EMA pe coordonatele de imagine (pentru desenat)
        current_img = np.array([[lm.x, lm.y] for lm in raw_img])
        if last_lm_smooth is None:
            last_lm_smooth = current_img
        else:
            last_lm_smooth = ALPHA * current_img + (1 - ALPHA) * last_lm_smooth
        
        pozitii_smooth = last_lm_smooth.tolist()

        # 2. Aplicăm filtrul EMA pe coordonatele WORLD (pentru calcule unghiuri)
        # Avem nevoie de x, y, z pentru unghiuri 3D
        current_world = np.array([[lm.x, lm.y, lm.z] for lm in raw_world])
        if last_world_smooth is None:
            last_world_smooth = current_world
        else:
            last_world_smooth = ALPHA * current_world + (1 - ALPHA) * last_world_smooth
        
        # Reconstruim obiecte compatibile cu calculeaza_unghi_3d
        class Point3D:
            def __init__(self, coords): self.x, self.y, self.z = coords
        
        lm_world_smooth = [Point3D(c) for c in last_world_smooth]

        if not corp_este_vertical(lm_world_smooth):
            date_cadre.append(None)
            continue

        unghi_genunchi = calculeaza_unghi_3d(lm_world_smooth[SOLD_STANG], lm_world_smooth[GENUNCHI_STANG], lm_world_smooth[GLEZNA_STANGA])
        unghi_spate    = calculeaza_unghi_3d(lm_world_smooth[UMAR_STANG], lm_world_smooth[SOLD_STANG], lm_world_smooth[GENUNCHI_STANG])

        # Numărare repetări
        if unghi_genunchi < 100:
            in_squat = True
        if in_squat and unghi_genunchi > 160:
            repetari += 1
            in_squat = False

        if unghi_genunchi < 130:
            cadre_cu_miscare_squat += 1
            scoruri_cadre.append(scor_cadru_squat(unghi_genunchi, unghi_spate))

        # Salvăm pozițiile netezite (0-1) ale tuturor landmark-urilor pentru canvas
        date_cadre.append({
            "lm": pozitii_smooth,
            "ug": round(unghi_genunchi, 1),
            "us": round(unghi_spate, 1),
        })

    cap.release()
    detector.close()

    if cadre_cu_persoana == 0:
        return {"eroare": "Nu a fost detectată nicio persoană în video. Încearcă din nou."}

    # Dacă scheletul lipsește în mai mult de 30% din cadre → obiecte în cale
    procent_lipsa = 1 - (cadre_cu_persoana / total_cadre) if total_cadre > 0 else 1
    if procent_lipsa > 0.30:
        return {"eroare": f"Scheletul s-a întrerupt în {int(procent_lipsa * 100)}% din video. Filmează fără obiecte sau haine largi care blochează corpul."}

    if cadre_cu_miscare_squat < 5:
        return {"eroare": "Nu a fost detectat niciun squat în video. Asigură-te că filmezi exercițiul corect și că tot corpul este vizibil."}

    scor_mediu = round(np.mean(scoruri_cadre)) if scoruri_cadre else 0
    feedback = genereaza_feedback(scoruri_cadre, repetari)

    return {
        "exercitiu": "Squat",
        "repetari": repetari,
        "scor": scor_mediu,
        "feedback": feedback,
        "fps": fps,
        "cadre": date_cadre,
        "conexiuni": CONEXIUNI,
    }


def scor_cadru_squat(unghi_genunchi, unghi_spate):
    scor = 100
    if unghi_genunchi > 110:
        scor -= (unghi_genunchi - 110) * 0.6
    if unghi_spate < 120:
        scor -= (120 - unghi_spate) * 0.5
    return max(0, min(100, scor))


def genereaza_feedback(scoruri, repetari):
    if repetari == 0:
        return ["Nicio repetare detectată. Asigură-te că tot corpul este vizibil în cadru."]
    if not scoruri:
        return ["Nu s-a putut analiza forma."]

    medie = np.mean(scoruri)
    feedback = []

    if medie >= 85:
        feedback.append("Formă excelentă la squat!")
    elif medie >= 65:
        feedback.append("Formă decentă, dar există loc de îmbunățiverire.")
    else:
        feedback.append("Forma necesită corecții — urmărește sfaturile de mai jos.")

    cadre_slabe = [s for s in scoruri if s < 60]
    if len(cadre_slabe) > len(scoruri) * 0.3:
        feedback.append("Încearcă să cobori mai mult — coapsele ar trebui să ajungă paralele cu podeaua.")

    return feedback
