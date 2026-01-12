<div align="right">
<a href="../README.md">⬅️ Wróć</a>
</div>

# Opis aplikacji

Aplikacja webowa we **Flasku** umożliwiająca analizę **obrazu lub wideo** z użyciem modelu **YOLOv8**. Użytkownik przesyła plik, opcjonalnie wybiera klasy do detekcji, a następnie otrzymuje wyniki w postaci:
- tabeli wykryć (dla obrazu) lub tabeli statystyk klas (dla wideo),
- podsumowania (liczba wykryć, liczba klas, średnia i maksymalna pewność),
- wykresu kołowego klas w UI,
- historii analiz z miniaturami i możliwością powrotu do wybranego uruchomienia.

## Główne funkcje
- Upload obrazu/wideo i uruchomienie detekcji YOLOv8.
- Opcjonalny wybór klas do analizy (checkboxy + wyszukiwarka w UI).
- Wyniki dla wideo: generowanie pliku wynikowego `pred_<nazwa>.avi` oraz miniatury `thumb_<nazwa>.jpg`.
- Historia analiz zapisywana do `instance/history.json` z konfigurowalnym limitem (1–500).
- Pobieranie wyników (`/download/<filename>`) oraz serwowanie plików z obsługą **HTTP Range** (`/uploads/<filename>`) – przydatne do odtwarzania wideo.

## Architektura
- **Backend:** Flask (routing + obsługa uploadu + uruchamianie YOLO)
- **Model:** Ultralytics YOLO (plik `yolov8n.pt` ładowany przy starcie aplikacji)
- **Wideo/obrazy:** OpenCV (odczyt/zapis wideo, miniatura)
- **Frontend:** HTML (Jinja2) + Bootstrap (CDN) + wykres kołowy (canvas)

## Wejścia/Wyjścia (skrót)
- **Wejście:** obraz/wideo + opcjonalna lista klas
- **Wyjście (obraz):** lista wykryć + podsumowanie
- **Wyjście (wideo):** plik wynikowy `.avi` + miniatura `.jpg` + statystyki klas + podsumowanie