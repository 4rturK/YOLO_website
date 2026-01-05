from __future__ import annotations

import os
import json
import uuid
import datetime
import re
import mimetypes
from typing import Any, Dict, List, Tuple, Optional

import cv2
from flask import Flask, request, send_from_directory, Response, abort
from ultralytics import YOLO


IMG_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "mkv", "webm", "m4v"}
ALLOWED_EXTENSIONS = IMG_EXTENSIONS | VIDEO_EXTENSIONS
DEFAULT_HISTORY_LIMIT = 10

CATEGORIES = {
    "Pojazdy": [1, 2, 3, 4, 5, 6, 7, 8],
    "Zwierzęta": [14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
    "Jedzenie": [46, 47, 48, 49, 50, 51, 52, 53, 54, 55],
    "Ludzie": [0],
    "Przedmioty domowe": [39, 41, 42, 43, 44, 45, 56, 57, 58, 59, 60, 61, 62],
    "Elektronika": [62, 63, 64, 65, 66, 67, 73],
}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def is_video(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in VIDEO_EXTENSIONS


def is_image(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in IMG_EXTENSIONS


def _load_history(history_file: str) -> Dict[str, Any]:
    if not os.path.exists(history_file):
        return {"limit": DEFAULT_HISTORY_LIMIT, "runs": []}
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "limit" not in data:
            data["limit"] = DEFAULT_HISTORY_LIMIT
        if "runs" not in data or not isinstance(data["runs"], list):
            data["runs"] = []
        return data
    except Exception:
        return {"limit": DEFAULT_HISTORY_LIMIT, "runs": []}


def _save_history(history_file: str, data: Dict[str, Any]) -> None:
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _safe_delete_upload(upload_folder: str, filename: Optional[str]) -> None:
    if not filename:
        return
    base = os.path.basename(filename)
    if not base:
        return
    path = os.path.join(upload_folder, base)
    try:
        if os.path.isfile(path):
            os.remove(path)
    except Exception:
        pass


def _trim_history(upload_folder: str, data: Dict[str, Any]) -> None:
    try:
        limit = int(data.get("limit") or DEFAULT_HISTORY_LIMIT)
    except Exception:
        limit = DEFAULT_HISTORY_LIMIT

    if limit < 1:
        limit = 1
        data["limit"] = 1

    runs: List[Dict[str, Any]] = data.get("runs", [])
    while len(runs) > limit:
        oldest = runs.pop(0)
        _safe_delete_upload(upload_folder, oldest.get("uploaded"))
        _safe_delete_upload(upload_folder, oldest.get("processed"))
        _safe_delete_upload(upload_folder, oldest.get("thumb"))
    data["runs"] = runs


def _make_summary_from_detections(detections: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary = {"total": 0, "num_classes": 0, "avg_conf": 0, "max_conf": 0}
    if not detections:
        return summary
    total = len(detections)
    confs = [float(d["confidence"]) for d in detections]
    summary["total"] = total
    summary["num_classes"] = len({int(d["class_id"]) for d in detections})
    summary["avg_conf"] = round(sum(confs) / total, 2) if total else 0
    summary["max_conf"] = round(max(confs), 2) if total else 0
    return summary


def _make_video_rows_and_summary(stats: Dict[int, Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    total = 0
    sum_conf = 0.0
    max_conf = 0.0

    for class_id, s in stats.items():
        cnt = int(s["count"])
        total += cnt
        sum_conf += float(s["sum_conf"])
        max_conf = max(max_conf, float(s["max_conf"]))
        avg = (float(s["sum_conf"]) / cnt) if cnt else 0.0
        rows.append(
            {
                "class_id": int(class_id),
                "name": str(s["name"]),
                "count": cnt,
                "avg_conf": round(avg, 2),
                "max_conf": round(float(s["max_conf"]), 2),
            }
        )

    rows.sort(key=lambda r: r["count"], reverse=True)
    summary = {
        "total": total,
        "num_classes": len(stats),
        "avg_conf": round((sum_conf / total) if total else 0.0, 2),
        "max_conf": round(max_conf if total else 0.0, 2),
    }
    return rows, summary


def _process_image(model: YOLO, img_path: str, classes_to_detect: Optional[List[int]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    detections: List[Dict[str, Any]] = []

    results = model(img_path, conf=0.25, classes=classes_to_detect)
    result = results[0]

    for box in result.boxes:
        class_id = int(box.cls[0])
        class_name = model.names[class_id]
        confidence = float(box.conf[0])
        detections.append(
            {
                "name": class_name,
                "class_id": class_id,
                "confidence": round(confidence * 100, 2),
                "box": box.xyxyn[0].tolist(),
            }
        )

    summary = _make_summary_from_detections(detections)
    return detections, summary


def _process_video(
    model: YOLO,
    upload_folder: str,
    video_path: str,
    classes_to_detect: Optional[List[int]],
) -> Tuple[str, str, List[Dict[str, Any]], Dict[str, Any]]:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("Nie udało się otworzyć pliku wideo.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 25.0

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if w <= 0 or h <= 0:
        cap.release()
        raise RuntimeError("Nie udało się odczytać rozmiaru klatek wideo.")

    base = os.path.basename(video_path)
    stem = os.path.splitext(base)[0]

    processed_filename = f"pred_{stem}.avi"
    processed_path = os.path.join(upload_folder, processed_filename)

    thumb_filename = f"thumb_{stem}.jpg"
    thumb_path = os.path.join(upload_folder, thumb_filename)

    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    writer = cv2.VideoWriter(processed_path, fourcc, float(fps), (w, h))
    if not writer.isOpened():
        cap.release()
        raise RuntimeError("Nie udało się utworzyć pliku wynikowego AVI.")

    stats: Dict[int, Dict[str, Any]] = {}
    wrote_thumb = False

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        results = model(frame, conf=0.25, classes=classes_to_detect)
        result = results[0]

        plotted = result.plot()
        if plotted.shape[1] != w or plotted.shape[0] != h:
            plotted = cv2.resize(plotted, (w, h), interpolation=cv2.INTER_AREA)

        writer.write(plotted)

        if not wrote_thumb:
            try:
                cv2.imwrite(thumb_path, plotted)
            except Exception:
                pass
            wrote_thumb = True

        for box in result.boxes:
            class_id = int(box.cls[0])
            conf = float(box.conf[0]) * 100.0
            name = str(model.names[class_id])

            if class_id not in stats:
                stats[class_id] = {"name": name, "count": 0, "sum_conf": 0.0, "max_conf": 0.0}

            stats[class_id]["count"] += 1
            stats[class_id]["sum_conf"] += conf
            if conf > stats[class_id]["max_conf"]:
                stats[class_id]["max_conf"] = conf

    cap.release()
    writer.release()

    rows, summary = _make_video_rows_and_summary(stats)
    return processed_filename, thumb_filename, rows, summary


def _send_with_range(directory: str, filename: str):
    base = os.path.basename(filename)
    path = os.path.join(directory, base)

    if not os.path.isfile(path):
        abort(404)

    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
    range_header = request.headers.get("Range")

    if range_header:
        size = os.path.getsize(path)
        m = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if not m:
            return send_from_directory(directory, base, conditional=True)

        start = int(m.group(1))
        end = int(m.group(2)) if m.group(2) else size - 1
        end = min(end, size - 1)

        if start > end:
            return Response(status=416)

        length = end - start + 1

        with open(path, "rb") as f:
            f.seek(start)
            data = f.read(length)

        resp = Response(data, status=206, mimetype=mime, direct_passthrough=True)
        resp.headers["Content-Range"] = f"bytes {start}-{end}/{size}"
        resp.headers["Accept-Ranges"] = "bytes"
        resp.headers["Content-Length"] = str(length)
        return resp

    return send_from_directory(directory, base, conditional=True)


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "Coockies_key")

    upload_dir = os.path.join(app.root_path, "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_dir

    os.makedirs(app.instance_path, exist_ok=True)
    history_file = os.path.join(app.instance_path, "history.json")
    app.config["HISTORY_FILE"] = history_file

    model = YOLO("yolov8n.pt")

    app.extensions["yolo_model"] = model
    app.extensions["yolo_helpers"] = {
        "allowed_file": allowed_file,
        "is_video": is_video,
        "is_image": is_image,
        "load_history": lambda: _load_history(app.config["HISTORY_FILE"]),
        "save_history": lambda data: _save_history(app.config["HISTORY_FILE"], data),
        "trim_history": lambda data: _trim_history(app.config["UPLOAD_FOLDER"], data),
        "safe_delete": lambda filename: _safe_delete_upload(app.config["UPLOAD_FOLDER"], filename),
        "process_image": lambda path, classes: _process_image(model, path, classes),
        "process_video": lambda path, classes: _process_video(model, app.config["UPLOAD_FOLDER"], path, classes),
        "send_with_range": lambda filename: _send_with_range(app.config["UPLOAD_FOLDER"], filename),
    }
    app.config["CATEGORIES"] = CATEGORIES

    from routes import bp
    app.register_blueprint(bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
