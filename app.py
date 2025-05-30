import os
import json
import random
from pathlib import Path
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "my_retro_quiz_game"

BASE_DIR = Path(__file__).resolve().parent
QUIZ_FOLDER = BASE_DIR / "quiz_data"

# Load college-to-conference mapping
with open(BASE_DIR / "college_confs.json") as f:
    college_confs = json.load(f)

@app.route("/", methods=["GET", "POST"])
def index():
    quiz_file = session.get("quiz_file")
    if not quiz_file or not (QUIZ_FOLDER / quiz_file).exists():
        return redirect("/new")

    with open(QUIZ_FOLDER / quiz_file) as f:
        data = json.load(f)

    results = []
    if request.method == "POST":
        for player in data["players"]:
            guess = request.form.get(player["name"])
            correct = player["school"]
            if guess and guess.lower().strip() == correct.lower().strip():
                result = f"✅ {guess}"
            else:
                result = f"❌ {guess}" if guess else "❌ (No guess)"
            player["result"] = result
            player["correct"] = correct
            results.append(result)

    colleges = sorted(set(college_confs.keys()) | {"Other"})
    return render_template("quiz.html", data=data, colleges=colleges, results=results, college_confs=college_confs)

@app.route("/new")
def new_game():
    quiz_files = list(QUIZ_FOLDER.glob("*.json"))
    if not quiz_files:
        return "No quizzes available."
    selected_file = random.choice(quiz_files)
    session["quiz_file"] = selected_file.name
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
