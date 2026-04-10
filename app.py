from flask import Flask, render_template, request, redirect, jsonify
import sqlite3

app = Flask(__name__)

conn = sqlite3.connect("world_champ.db", check_same_thread=False)
cur = conn.cursor()

# ================= TABLES =================

cur.execute("""
CREATE TABLE IF NOT EXISTS athletes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    club TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS performances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    athlete_id INTEGER,
    d_score REAL,
    e_score REAL,
    penalty REAL
)
""")

conn.commit()

# ================= HOME =================

@app.route("/")
def index():
    athletes = cur.execute("SELECT * FROM athletes").fetchall()
    return render_template("index.html", athletes=athletes)

# ================= ADD ATHLETE =================

@app.route("/add", methods=["POST"])
def add():
    name = request.form["name"]
    club = request.form["club"]

    cur.execute("INSERT INTO athletes VALUES (NULL,?,?)", (name, club))
    conn.commit()
    return redirect("/")

# ================= JUDGING =================

@app.route("/judge", methods=["POST"])
def judge():
    athlete_id = request.form["athlete_id"]
    d = float(request.form["d"])
    penalty = float(request.form["penalty"])

    # 7 E-scores
    e_scores = []
    for i in range(1, 8):
        val = request.form.get(f"e{i}")
        if val != "" and val is not None:
            e_scores.append(float(val))

    # safety
    if len(e_scores) < 3:
        return redirect("/")

    # ================= FIG RULE =================
    e_scores.sort()

    # ❌ eliminăm 2 mici + 2 mari
    trimmed = e_scores[2:-2]

    e_final = sum(trimmed) / len(trimmed)

    total = d + e_final - penalty

    cur.execute("""
        INSERT INTO performances VALUES (NULL,?,?,?,?)
    """, (athlete_id, d, e_final, penalty))

    conn.commit()

    return redirect("/")

# ================= LIVE RANKING =================

@app.route("/api/rankings")
def rankings():

    data = cur.execute("""
        SELECT 
            a.name,
            a.club,
            p.d_score,
            p.e_score,
            p.penalty
        FROM athletes a
        LEFT JOIN performances p ON a.id = p.athlete_id
        GROUP BY a.id
    """).fetchall()

    result = []

    for r in data:
        name, club, d, e, pen = r

        d = d or 0
        e = e or 0
        pen = pen or 0

        total = d + e - pen

        result.append([name, club, total, e, d])

    # 🏆 TIEBREAK: E → D → egal
    result.sort(key=lambda x: (x[3], x[4]), reverse=True)

    return jsonify(result)

# ================= RUN =================

if __name__ == "__main__":
    app.run()