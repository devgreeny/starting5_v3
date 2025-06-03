"""
app/main/routes.py
------------------
All quiz-related views wrapped in a Blueprint called `main`.
"""

import os, json, random
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, make_response
from flask_login import current_user, login_required
from app.models import db, GuessLog
from sqlalchemy import func
from urllib.parse import unquote

bp = Blueprint("main", __name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
QUIZ_DIR     = os.path.join(PROJECT_ROOT, "app", "static", "preloaded_quizzes")
CONFS        = os.path.join(PROJECT_ROOT, "college_confs.json")


def load_confs():
    with open(CONFS, encoding="utf-8") as f:
        d = json.load(f)
    return d, sorted(d.keys())


def normalise_usc(p, confs):
    if p.get("school") == "Southern California":
        p["school"]     = "USC"
        p["conference"] = confs.get("USC", "P12")


@bp.route("/")
def home():
    return render_template("welcome.html")


@bp.route("/quiz", methods=["GET", "POST"])
@login_required
def show_quiz():
    conf_map, colleges = load_confs()

    if request.method == "POST":
        qp = request.form.get("quiz_json_path", "")
        if not qp or not os.path.isfile(qp):
            return redirect(url_for("main.show_quiz"))

        with open(qp, encoding="utf-8") as f:
            data = json.load(f)
        for pl in data["players"]:
            normalise_usc(pl, conf_map)

        results, correct_answers = [], []
        score, max_points = 0.0, 0.0

        for idx, p in enumerate(data["players"]):
            name         = p["name"]
            school_type  = p["school_type"]
            team_name    = p["school"]
            country      = p["country"]
            guess        = request.form.get(name, "").strip()
            used_hint    = request.form.get(f"hint_used_{idx}", "0") == "1"

            is_correct = False
            pts = 0.0

            if school_type == "College":
                max_points += 1.0
                if guess.lower() == team_name.lower():
                    pts = 0.75 if used_hint else 1.0
                    is_correct = True
                score += pts
                results.append("✅" if is_correct else "❌")
                correct_answers.append(team_name)

            else:
                max_points += 1.25
                if guess.lower() == team_name.lower():
                    pts = 1.25
                    is_correct = True
                elif guess.lower() == country.lower():
                    pts = 1.0
                    is_correct = True
                elif guess.lower() == "other":
                    pts = 0.75
                    is_correct = True
                score += pts
                results.append("✅" if is_correct else "❌")
                correct_answers.append(team_name)

            # Log the guess in the database
            guess_log = GuessLog(
                user_id=current_user.id,
                player_name=name,
                school=team_name,
                guess=guess,
                is_correct=is_correct,
                used_hint=used_hint
            )
            db.session.add(guess_log)

        db.session.commit()

        return render_template(
            "quiz.html",
            data            = data,
            colleges        = colleges,
            college_confs   = conf_map,
            results         = results,
            correct_answers = correct_answers,
            score           = round(score, 2),
            max_points      = round(max_points, 2),
            quiz_json_path  = qp
        )

    # GET: serve a fresh quiz
    quiz_files = [f for f in os.listdir(QUIZ_DIR) if f.lower().endswith(".json")]
    if not quiz_files:
        return "No quiz JSONs in quiz_data/", 500

    chosen = os.path.join(QUIZ_DIR, random.choice(quiz_files))
    with open(chosen, encoding="utf-8") as f:
        data = json.load(f)
    for pl in data["players"]:
        normalise_usc(pl, conf_map)

    return render_template(
        "quiz.html",
        data            = data,
        colleges        = colleges,
        college_confs   = conf_map,
        results         = None,
        correct_answers = [],
        score           = None,
        max_points      = None,
        quiz_json_path  = chosen
    )

@bp.route("/player_accuracy/<player_name>")
def player_accuracy(player_name):
    safe_name = unquote(player_name)

    total = db.session.query(func.count(GuessLog.id)).filter_by(player_name=safe_name).scalar()
    correct = db.session.query(func.count(GuessLog.id)).filter_by(player_name=safe_name, is_correct=True).scalar()

    percent = round(100 * correct / total, 1) if total else 0

    response = make_response(jsonify({"player": safe_name, "accuracy": percent}))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response
