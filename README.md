# Antrenor Virtual — Lucrare de Licență

Aplicație web pentru analiza formei la exerciții fizice folosind **MediaPipe Pose** și **Flask**.

## Funcționalități

- Încarcă un video cu squat și primește feedback automat
- Detectare și numărare repetări
- Scor formă 0–100 bazat pe unghiuri 3D (invariante față de unghiul camerei)
- Overlay vizual în timp real: schelet + unghiuri sincronizate cu videoul
- Culoare adaptivă a scheletului în funcție de calitatea formei

## Stack

- **Backend**: Python + Flask
- **Analiză**: MediaPipe Tasks API (pose_world_landmarks 3D)
- **Frontend**: HTML / CSS / JavaScript vanilla

## Instalare

```bash
pip install flask mediapipe opencv-python numpy
python app.py
```

Modelul MediaPipe (~5MB) se descarcă automat la prima analiză.

Deschide `http://127.0.0.1:5000` în browser.

## Structură

```
licenta/
├── app.py           # Server Flask, rute
├── analyzer.py      # Logică MediaPipe — detectare, unghiuri, scor
└── templates/
    └── index.html   # Interfață web
```

## Branches

| Branch | Descriere |
|---|---|
| `master` | Versiunea stabilă |
| `gemini-dev` | Teste și experimente vizuale |
| `baza_de_date` | Integrare SQLite (în dezvoltare) |
