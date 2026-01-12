<div align="right">
<a href="../README.md">⬅️ Wróć</a>
</div>

# API Reference (endpointy webowe)

Aplikacja nie posiada wydzielonego REST API – interfejs bazuje na endpointach webowych (Flask), które obsługują UI oraz udostępniają pliki wynikowe.

## Base URL
`http://127.0.0.1:5000/`

---

## GET
Renderuje stronę główną z formularzem uploadu, listą klas i historią.

### Query params
- `run` (opcjonalnie) – ID wpisu historii; powoduje wczytanie wyników konkretnej analizy.

### Przykład
`GET /?run=<RUN_ID>`

---

## POST `/` (analiza pliku)
### Opis
Przyjmuje upload, uruchamia detekcję YOLO i zwraca stronę HTML z wynikami.

### Content-Type
`multipart/form-data`

### Pola formularza
- `image` – plik obrazu/wideo (wymagane)
- `classes` – lista ID klas (opcjonalne; jeśli brak → wszystkie klasy)

### Dozwolone formaty
- obrazy: `png, jpg, jpeg, gif`
- wideo: `mp4, avi, mov, mkv, webm, m4v`

### Wyniki (logicznie, wykorzystywane przez UI)
**Obraz:**
- `detections[]`: `name`, `class_id`, `confidence` (%), `box` (`xyxyn`)
- `summary`: `total`, `num_classes`, `avg_conf`, `max_conf`

**Wideo:**
- generuje `pred_<nazwa>.avi` oraz `thumb_<nazwa>.jpg`
- `video_rows[]`: `class_id`, `name`, `count`, `avg_conf`, `max_conf`
- `summary`: `total`, `num_classes`, `avg_conf`, `max_conf`

### Przykład (curl)
```bash
# obraz
curl -F "image=@sample.jpg" http://127.0.0.1:5000/

# wideo + filtrowanie klas (np. 0 i 2)
curl -F "image=@sample.mp4" -F "classes=0" -F "classes=2" http://127.0.0.1:5000/
```

---

## POST `/` (akcje historii)
Endpoint `/` obsługuje również akcje historii przez pole `action`.

### `action=set_history_limit`
- pole: `history_limit` (1–500)

### `action=clear_history`
Czyści historię i usuwa powiązane pliki (upload/wynik/miniatura).

---

## GET `/uploads/<filename>`
### Opis
Zwraca plik z `static/uploads/`. Endpoint wspiera **HTTP Range** (np. do odtwarzania/wczytywania fragmentów wideo).

### Kody odpowiedzi
- `200` – pełny plik
- `206` – `Partial Content` (gdy wysłano `Range`)
- `404` – brak pliku
- `416` – niepoprawny zakres `Range`

### Przykład (Range)
```bash
curl -H "Range: bytes=0-999999" http://127.0.0.1:5000/uploads/pred_test.avi -o part.bin
```

---

## GET `/download/<filename>`
### Opis
Pobiera plik jako załącznik (`Content-Disposition: attachment`).

### Kody odpowiedzi
- `200` – pobranie OK
- `404` – brak pliku
p4" -F "classes=0" -F "classes=2" http://127.0.0.1:5000/