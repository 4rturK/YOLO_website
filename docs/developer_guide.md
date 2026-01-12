<div align="right">
<a href="../README.md">⬅️ Wróć</a>
</div>

# Developer Guide

## Struktura projektu (kluczowe pliki)
- `app.py`
  - inicjalizacja Flask (`create_app`)
  - ładowanie modelu `YOLO("yolov8n.pt")`
  - helpery: walidacja plików, przetwarzanie obrazu/wideo, obsługa historii, serwowanie plików z Range

- `routes.py`
  - endpoint `/` (GET/POST) – UI + logika uploadu i historii
  - endpoint `/uploads/<filename>` – podgląd plików (obsługa HTTP Range)
  - endpoint `/download/<filename>` – pobieranie wyników jako załącznik

- `templates/index.html`
  - formularz analizy, wybór klas, overlay „Trwa analiza…”
  - panel historii (sidebar) + wykres kołowy klas

- `static/styles.css`
  - stylowanie historii, overlay analizy, layout komponentów UI

- `instance/history.json`
  - trwała historia uruchomień: `{"limit": ..., "runs": [...]}`

## Konfiguracja formatów wejściowych
Aplikacja dopuszcza pliki:
- obrazy: `png, jpg, jpeg, gif`
- wideo: `mp4, avi, mov, mkv, webm, m4v`

Walidacja wykonywana jest po rozszerzeniu pliku (whitelist).


## Przepływ logiki (end-to-end)

### 1) Wejście użytkownika (formularz)
UI wysyła `multipart/form-data` z:
- `image` (plik obrazu lub wideo)
- `classes` (opcjonalnie, lista ID klas – checkboxy)

### 2) Routing i walidacja
W `routes.py`:
- weryfikowane jest istnienie pliku i dozwolone rozszerzenie,
- pobierane są zaznaczone klasy (`request.form.getlist("classes")`),
- obsługiwane są akcje historii (`action=set_history_limit`, `action=clear_history`).

### 3) Zapis pliku i uruchomienie analizy
- upload zapisywany jest jako `uuid + secure_filename(...)` do `static/uploads/`
- dla obrazu: wywołanie przetwarzania obrazu (YOLO na całym obrazie)
- dla wideo: przetwarzanie klatka po klatce + zapis `pred_<nazwa>.avi` i `thumb_<nazwa>.jpg`

### 4) Wynik przetwarzania (struktury danych)
**Obraz**
- `detections[]`: `name`, `class_id`, `confidence` (%), `box` (`xyxyn`, znormalizowane współrzędne)
- `summary`: `total`, `num_classes`, `avg_conf`, `max_conf`

**Wideo**
- pliki: `pred_<nazwa>.avi`, `thumb_<nazwa>.jpg`
- `video_rows[]`: `class_id`, `name`, `count`, `avg_conf`, `max_conf`
- `summary`: `total`, `num_classes`, `avg_conf`, `max_conf`

### 5) Historia analiz
- wpis dopisywany jest do `instance/history.json`
- historia przycinana jest do `limit` (1–500)
- przy usuwaniu najstarszych wpisów usuwane są także powiązane pliki (uploaded/processed/thumb), żeby nie zapełniać dysku.

## Serwowanie plików wynikowych (HTTP Range)
Endpoint `/uploads/<filename>` obsługuje nagłówek `Range`:
- `200 OK` – gdy pobierany jest cały plik,
- `206 Partial Content` – gdy pobierany jest fragment (np. odtwarzanie wideo),
- `416 Range Not Satisfiable` – gdy zakres jest błędny,
- `404 Not Found` – gdy plik nie istnieje.