from flask import Flask, render_template, request, redirect, jsonify
import sqlite3

app = Flask(__name__)

conn = sqlite3.connect("gym.db", check_same_thread=False)
cur = conn.cursor()

# ================= DB =================

cur.execute("""
CREATE TABLE IF NOT EXISTS athletes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    club TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    athlete_id INTEGER,
    judge TEXT,
    d_score REAL,
    e_score REAL,
    penalty REAL
)
""")

conn.commit()

# ================= ADMIN =================

@app.route("/")
def index():
    athletes = cur.execute("SELECT * FROM athletes").fetchall()
    return render_template("index.html", athletes=athletes)

@app.route("/add", methods=["POST"])
def add():
    name = request.form["name"]
    club = request.form["club"]

    cur.execute("INSERT INTO athletes VALUES (NULL,?,?)", (name, club))
    conn.commit()
    return redirect("/")

# ================= JUDGE PAGE (SEPARAT) =================

@app.route("/judge/<judge_id>/<athlete_id>")
def judge_page(judge_id, athlete_id):
    athlete = cur.execute("SELECT * FROM athletes WHERE id=?", (athlete_id,)).fetchone()
    return render_template("judge.html", judge=judge_id, athlete=athlete)

# ================= SUBMIT SCORE =================

@app.route("/submit", methods=["POST"])
def submit():
    athlete_id = request.form["athlete_id"]
    judge = request.form["judge"]
    d = float(request.form["d"])
    e = float(request.form["e"])
    penalty = float(request.form["penalty"])

    cur.execute("""
        INSERT INTO scores VALUES (NULL,?,?,?,?,?)
    """, (athlete_id, judge, d, e, penalty))

    conn.commit()
    return redirect("/judge/" + judge + "/" + athlete_id)

# ================= LIVE RANKING =================

@app.route("/api/rankings")
def rankings():

    data = cur.execute("""
        SELECT 
            a.name,
            a.club,
            AVG(s.d_score),
            AVG(s.e_score),
            SUM(s.penalty)
        FROM athletes a
        LEFT JOIN scores s ON a.id = s.athlete_id
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

    # 🏆 FIG TIEBREAK: E → D → egal
    result.sort(key=lambda x: (x[3], x[4]), reverse=True)

    return jsonify(result)

# ================= RUN =================

if __name__ == "__main__":
    app.run()