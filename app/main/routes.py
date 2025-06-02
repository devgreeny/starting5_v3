"""
app/main/routes.py
------------------
All quiz-related views wrapped in a Blueprint called `main`.
The factory in app/__init__.py will register this blueprint.
"""

import os, json, random
from flask import Blueprint, render_template, request, redirect, url_for

bp = Blueprint("main", __name__)

# ───── Correct file locations ───────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
QUIZ_DIR     = os.path.join(PROJECT_ROOT, "quiz_data")
CONFS        = os.path.join(PROJECT_ROOT, "college_confs.json")


def load_confs():
    with open(CONFS, encoding="utf-8") as f:
        d = json.load(f)
    return d, sorted(d.keys())


def normalise_usc(p, confs):
    if p.get("school") == "Southern California":
        p["school"]     = "USC"
        p["conference"] = confs.get("USC", "P12")


# ────────────────────────────────────────────────────────────────
@bp.route("/")
def home():
    """Landing page (welcome screen)."""
    return render_template("welcome.html")


# ────────────────────────────────────────────────────────────────
@bp.route("/quiz", methods=["GET", "POST"])
def show_quiz():
    """Serve the daily quiz and grade submissions."""
    conf_map, colleges = load_confs()

    # ---------- POST: grade guesses -----------------------------------------
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
            team_name    = p["school"]      # e.g. “Fenerbahce” or “Louisville”
            country      = p["country"]     # e.g. “Croatia”
            guess        = request.form.get(name, "").strip()
            used_hint    = request.form.get(f"hint_used_{idx}", "0") == "1"

            # ------- COLLEGE PLAYERS -----------------------------------------
            if school_type == "College":
                max_points += 1.0                      # always 1.0 in tally
                if guess.lower() == team_name.lower():
                    pts = 0.75 if used_hint else 1.0   # hint penalty only here
                    score += pts
                    results.append("✅")
                else:
                    results.append("❌")
                correct_answers.append(team_name)

            # ------- NON-COLLEGE PLAYERS -------------------------------------
            else:
                max_points += 1.25
                pts = 0.0
                if guess.lower() == team_name.lower():        # exact club
                    pts = 1.25
                elif guess.lower() == country.lower():        # country
                    pts = 1.0
                elif guess.lower() == "other":                # generic “Other”
                    pts = 0.75
                score += pts
                results.append("✅" if pts else "❌")
                correct_answers.append(team_name)

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

    # ---------- GET: serve a fresh quiz -------------------------------------
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
