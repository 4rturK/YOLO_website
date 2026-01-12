<div align="right">
<a href="../README.md">⬅️ Wróć</a>
</div>

# Instalacja

## Wymagania
- Python **3.10+** (zalecane)
- Zależności z `requirements.txt`
- Plik modelu: `yolov8n.pt` (musi znajdować się w repozytorium obok `app.py`)

## Klonowanie repozytorium
```bash
git clone https://github.com/4rturK/YOLO_website.git
cd YOLO_website
```

## Środowisko wirtualne
**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Instalacja zależności
```bash
pip install -r requirements.txt
```

## Uruchomienie
```bash
python app.py
```

Aplikacja uruchomi serwer Flask pod adresem:
- `http://127.0.0.1:5000/`

## Struktura katalogów po starcie
- Uploady i wyniki trafiają do: `static/uploads/`
- Historia analiz trafia do: `instance/history.json`

## Porty
- Backend/Frontend (Flask): **5000**
