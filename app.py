import os
import json
import random
from pathlib import Path
from flask import Flask, render_template, request, redirect, session
from generate_quiz import generate_and_save_quiz

app = Flask(__name__)
app.secret_key = "my_retro_quiz_game"

QUIZ_FOLDER = Path("quiz_data")

# Load college-to-conference mapping
with open("college_confs.json") as f:
    college_confs = json.load(f)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        quiz_file = session.get("quiz_file")
        if not quiz_file or not os.path.exists(QUIZ_FOLDER / quiz_file):
            return redirect("/")

        with open(QUIZ_FOLDER / quiz_file) as f:
            data = json.load(f)

        results = []
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

    else:
        quiz_file = session.get("quiz_file")
        if not quiz_file or not os.path.exists(QUIZ_FOLDER / quiz_file):
            return redirect("/new")

        with open(QUIZ_FOLDER / quiz_file) as f:
            data = json.load(f)

        colleges = sorted(set(college_confs.keys()) | {"Other"})
        return render_template("quiz.html", data=data, colleges=colleges, results=[], college_confs=college_confs)

@app.route("/new")
def new_game():
    try:
        new_file_path = generate_and_save_quiz()
        quiz_file = os.path.basename(new_file_path)
        session["quiz_file"] = quiz_file
    except Exception as e:
        return f"Failed to generate quiz: {e}"
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
