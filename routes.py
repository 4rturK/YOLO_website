from __future__ import annotations

import os
import uuid
import datetime
from typing import Any, Dict, List, Optional

from flask import (
    Blueprint,
    current_app,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    abort,
    send_from_directory,
)
from werkzeug.utils import secure_filename


bp = Blueprint("main", __name__)


@bp.route("/", methods=["GET", "POST"])
def index():
    uploaded_image: Optional[str] = None
    processed_video: Optional[str] = None
    video_thumb: Optional[str] = None
    video_rows: List[Dict[str, Any]] = []
    detections: List[Dict[str, Any]] = []
    summary: Dict[str, Any] = {"total": 0, "num_classes": 0, "avg_conf": 0, "max_conf": 0}
    media_type: Optional[str] = None

    model = current_app.extensions["yolo_model"]
    helpers = current_app.extensions["yolo_helpers"]

    all_classes = model.names
    sorted_classes = sorted(all_classes.items(), key=lambda x: x[1].lower())
    categories = current_app.config["CATEGORIES"]

    history_data = helpers["load_history"]()

    if request.method == "POST" and request.form.get("action") in {"set_history_limit", "clear_history"}:
        action = request.form.get("action")

        if action == "set_history_limit":
            try:
                new_limit = int(request.form.get("history_limit", 10))
            except ValueError:
                new_limit = 10
            new_limit = max(1, min(new_limit, 500))
            history_data["limit"] = new_limit
            helpers["trim_history"](history_data)
            helpers["save_history"](history_data)
            flash(f"Zapis historii ustawiony na {new_limit}.", "success")
            return redirect(url_for("main.index"))

        if action == "clear_history":
            for run in history_data.get("runs", []):
                helpers["safe_delete"](run.get("uploaded"))
                helpers["safe_delete"](run.get("processed"))
                helpers["safe_delete"](run.get("thumb"))
            history_data["runs"] = []
            helpers["save_history"](history_data)
            flash("Historia została wyczyszczona.", "success")
            return redirect(url_for("main.index"))

    run_id = request.args.get("run")
    if request.method == "GET" and run_id:
        for run in history_data.get("runs", []):
            if run.get("id") == run_id:
                media_type = run.get("media_type")
                if media_type == "video":
                    processed_video = run.get("processed")
                    video_thumb = run.get("thumb")
                    video_rows = run.get("video_rows", []) or []
                    summary = run.get("summary", summary) or summary
                else:
                    uploaded_image = run.get("uploaded")
                    detections = run.get("detections", []) or []
                    summary = run.get("summary", summary) or summary
                    media_type = "image"
                break

    if request.method == "POST" and request.form.get("action") is None:
        file = request.files.get("image")

        if not file or file.filename == "":
            flash("Błąd: Nie wybrano pliku!", "danger")
            return redirect(url_for("main.index"))

        if not helpers["allowed_file"](file.filename):
            flash("Błąd: Niedozwolony format pliku!", "danger")
            return redirect(url_for("main.index"))

        selected_class_ids = request.form.getlist("classes")
        classes_to_detect = [int(cls_id) for cls_id in selected_class_ids] if selected_class_ids else None

        original_name = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{original_name}"
        input_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_filename)
        file.save(input_path)

        run_entry: Dict[str, Any] = {
            "id": uuid.uuid4().hex,
            "created_at": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "uploaded": unique_filename,
        }

        try:
            if helpers["is_video"](unique_filename):
                media_type = "video"
                processed_filename, thumb_filename, rows, vid_summary = helpers["process_video"](input_path, classes_to_detect)

                processed_video = processed_filename
                video_thumb = thumb_filename
                video_rows = rows
                summary = vid_summary

                run_entry.update(
                    {
                        "media_type": "video",
                        "processed": processed_filename,
                        "thumb": thumb_filename,
                        "video_rows": rows,
                        "summary": summary,
                    }
                )
            else:
                media_type = "image"
                uploaded_image = unique_filename
                dets, img_summary = helpers["process_image"](input_path, classes_to_detect)
                detections = dets
                summary = img_summary

                run_entry.update(
                    {
                        "media_type": "image",
                        "processed": None,
                        "thumb": unique_filename,
                        "detections": dets,
                        "summary": summary,
                    }
                )

        except Exception:
            helpers["safe_delete"](unique_filename)
            flash("Błąd: Nie udało się przetworzyć pliku.", "danger")
            return redirect(url_for("main.index"))

        history_data = helpers["load_history"]()
        history_data.setdefault("runs", []).append(run_entry)
        helpers["trim_history"](history_data)
        helpers["save_history"](history_data)

    runs_desc = list(reversed(history_data.get("runs", [])))
    history_limit = int(history_data.get("limit") or 10)
    history_count = len(history_data.get("runs", []))

    return render_template(
        "index.html",
        uploaded_image=uploaded_image,
        processed_video=processed_video,
        video_thumb=video_thumb,
        video_rows=video_rows,
        detections=detections,
        summary=summary,
        media_type=media_type,
        all_classes=all_classes,
        sorted_classes=sorted_classes,
        categories=categories,
        history_runs=runs_desc,
        history_limit=history_limit,
        history_count=history_count,
    )


@bp.route("/uploads/<path:filename>")
def uploaded_file(filename: str):
    helpers = current_app.extensions["yolo_helpers"]
    return helpers["send_with_range"](filename)


@bp.route("/download/<path:filename>")
def download_file(filename: str):
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    base = os.path.basename(filename)
    full = os.path.join(upload_folder, base)
    if not os.path.isfile(full):
        abort(404)
    return send_from_directory(upload_folder, base, as_attachment=True, download_name=base)
