"""
Flask UI for collecting a user profile and running the personalized book pipeline.
"""
from __future__ import annotations

import os
import json
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from flask import (
    Flask,
    Response,
    redirect,
    render_template,
    request,
    send_from_directory,
    stream_with_context,
    url_for,
)

from questionnaire import UserProfile
from pipeline import (
    run_planning,
    run_drafting,
    run_editing,
    refine_with_critique,
)
from html_pdf import html_text_to_pdf
from artifact_utils import guess_book_title, make_pdf_path

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "outputs"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_FORM_VALUES = {
    "age": 20,
    "education_level": "",
    "preferred_theme": "",
    "purpose_of_reading": "",
    "mood_today": "",
    "favorite_author": "",
    "length_in_pages": 2,
    "special_request": "Feel free to be creative in your request",
}

PROGRESS_STAGES = ["plan", "draft", "final_text", "critique", "artifacts"]


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def save_artifacts(results: dict[str, str], prefix: str) -> dict[str, Path]:
    """
    Persist plan/draft/final/critique text files and a PDF of the final text.
    Returns the mapping of artifact names to paths for download.
    """
    files = {
        "plan": OUTPUT_DIR / f"{prefix}_plan.txt",
        "draft": OUTPUT_DIR / f"{prefix}_draft_raw.txt",
        "final_text": OUTPUT_DIR / f"{prefix}_book_final.txt",
        "critique": OUTPUT_DIR / f"{prefix}_critique.txt",
    }
    for key, path in files.items():
        _write_text(path, results[key])

    title = guess_book_title(results.get("plan", ""), results.get("final_text", ""))
    pdf_path = make_pdf_path(OUTPUT_DIR, title)
    html_text_to_pdf(results["final_text"], str(pdf_path))

    files["pdf"] = pdf_path
    return files


def _json_event(event_type: str, **payload: object) -> str:
    data = {"type": event_type, **payload}
    return json.dumps(data, ensure_ascii=False) + "\n"


def _progress_percent(completed: int) -> int:
    total = len(PROGRESS_STAGES)
    if total == 0:
        return 100
    return min(100, int((completed / total) * 100))


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", form_values=DEFAULT_FORM_VALUES)


@app.post("/generate")
def generate():
    form = request.form
    profile = UserProfile(
        age=int(form["age"]),
        preferred_theme=form["preferred_theme"],
        purpose_of_reading=form["purpose_of_reading"],
        mood_today=form["mood_today"],
        length_in_pages=int(form["length_in_pages"]),
        education_level=form.get("education_level", "").strip(),
        favorite_author=form.get("favorite_author", "").strip(),
        special_request=form.get("special_request", "").strip(),
    )

    def event_stream():
        completed = 0
        try:
            yield _json_event("progress", percent=0)
            yield _json_event("status", message="Planning outline...")
            plan = run_planning(profile)
            yield _json_event("plan", content=plan)
            completed += 1
            yield _json_event("progress", percent=_progress_percent(completed))

            yield _json_event("status", message="Drafting manuscript...")
            draft = run_drafting(profile, plan)
            yield _json_event("draft", content=draft)
            completed += 1
            yield _json_event("progress", percent=_progress_percent(completed))

            yield _json_event("status", message="Editing for polish...")
            edited_text = run_editing(profile, draft)

            yield _json_event("status", message="Iterating with critique loop...")
            final_text, critique = refine_with_critique(profile, edited_text)
            yield _json_event("final_text", content=final_text)
            completed += 1
            yield _json_event("progress", percent=_progress_percent(completed))

            yield _json_event("status", message="Summarizing critique insights...")
            yield _json_event("critique", content=critique)
            completed += 1
            yield _json_event("progress", percent=_progress_percent(completed))

            results = {
                "plan": plan,
                "draft": draft,
                "final_text": final_text,
                "critique": critique,
            }

            yield _json_event("status", message="Saving files...")
            prefix = f"session_{uuid4().hex[:8]}"
            artifact_paths = save_artifacts(results, prefix)
            artifacts = {name: path.name for name, path in artifact_paths.items()}
            yield _json_event("artifacts", files=artifacts)
            completed += 1
            yield _json_event("progress", percent=_progress_percent(completed))

            yield _json_event("complete", profile=vars(profile))
        except Exception as exc:
            yield _json_event("error", message=str(exc))

    return Response(stream_with_context(event_stream()), mimetype="text/plain")


@app.route("/download/<path:filename>")
def download(filename: str):
    """
    Serves generated artifacts from the outputs directory.
    """
    base = OUTPUT_DIR.resolve()
    safe_path = (OUTPUT_DIR / filename).resolve()
    if not safe_path.exists() or base not in safe_path.parents:
        return redirect(url_for("index"))
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", 5000)))
