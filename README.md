# YOLO_WEBSITE

Projekt zaliczeniowy z przedmiotów PPP, PAI, OirpOS. Aplikacja webowa we Flasku do analizy obrazu i wideo przy użyciu YOLOv8.

Aplikacja pozwala na analizę wysłanego pliku w odpowiednim formacie, a po analizie można zobaczyć statystyki projektu.

---

  ## Szczegółowa dokumentacja 
- [Opis aplikacji](docs/overview.md)
- [Instalacja](docs/installation.md)
- [Developer Guide](docs/developer_guide.md)
- [Instrukcja użytkowania](docs/user_guide.md)
- [API Reference](docs/api.md)
  
---

## Wymagania

- Python 3.10+ (zalecane)
- Pakiety z `requirements.txt`
- Plik modelu: `yolov8n.pt` (w projekcie)

---

## Instalacja

1) Środowisko wirtualne:

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

2) Zainstaluj zależności:

```bash
pip install -r requirements.txt
```

3) Uruchom aplikację:

```bash
python app.py
```

Po starcie wejdź w przeglądarce na adres wypisany w terminalu (zwykle `http://127.0.0.1:5000/`).

---

## Jak używać

1. Otwórz stronę główną.
2. Wybierz plik do analizy:
   - obraz (np. `.jpg`, `.png`)
   - wideo (np. `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`, `.m4v`)
3. Wybierz konkretne klasy do detekcji (jeżeli nic nie zostanie wybrane, to wszystko jest brane pod uwagę).
4. Wyślij plik.
5. Po analizie:
   - zobaczysz wynik (obraz lub miniaturę dla wideo),
   - zobaczysz statystyki / tabelę wykrytych klas,
   - wpis pojawi się w historii.

---

### Do czego służą najważniejsze elementy

- `app.py`  
  Konfiguracja Flask, inicjalizacja modelu YOLO, logika przetwarzania obrazu/wideo oraz helpery.

- `routes.py`  
  Routing aplikacji (strona główna, pobieranie plików, obsługa historii itp.).

- `templates/index.html`  
  Widok UI (formularz uploadu, wyniki, historia, statystyki).

- `static/uploads/`  
  Tu trafiają pliki wgrane oraz pliki wynikowe (np. `pred_*` i miniatury `thumb_*`).

- `instance/history.json`  
  Historia uruchomień (limit + lista runów). Plik tworzy się/aktualizuje automatycznie.
