from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, Routine

app = Flask(__name__)
app.config['SECRET_KEY'] = "SUPER_SECRET_KEY"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///gym.db"

db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

login_manager = LoginManager()
login_manager.init_app(app)


# =====================
# INIT DB
# =====================
with app.app_context():
    db.create_all()


# =====================
# LOGIN SYSTEM
# =====================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()

        if user and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            session["role"] = user.role
            return redirect("/judge")

    return render_template("login.html")


# =====================
# DASHBOARD
# =====================
@app.route("/")
def dashboard():
    return render_template("dashboard.html")


# =====================
# JUDGE PANEL
# =====================
@app.route("/judge")
@login_required
def judge():
    return render_template("judge.html", role=current_user.role)


# =====================
# CONTROL ROOM
# =====================
@app.route("/control")
@login_required
def control():
    if current_user.role != "ADMIN":
        return "Forbidden"

    pending = Routine.query.filter_by(status="PENDING").all()
    return render_template("control_room.html", routines=pending)


# =====================
# TV WALL
# =====================
@app.route("/tv")
def tv():
    return render_template("tv_wall.html")


# =====================
# FIG CALCULATION
# =====================
def calc_final(D, e_list, penalty):
    e_list.sort()
    middle = e_list[1:4]
    E_avg = sum(middle) / 3
    return D + E_avg - penalty


# =====================
# SUBMIT SCORE (ANTI CHEAT)
# =====================
submitted_users = set()

@app.route("/submit", methods=["POST"])
@login_required
def submit():
    if current_user.username in submitted_users:
        return {"error": "Already submitted"}, 403

    data = request.json

    e_list = [
        float(data["E1"]),
        float(data["E2"]),
        float(data["E3"]),
        float(data["E4"]),
        float(data["E5"])
    ]

    final = calc_final(float(data["D"]), e_list, float(data["penalty"]))

    routine = Routine(
        nume=data["nume"],
        club=data["club"],
        aparat=data["aparat"],
        D=float(data["D"]),
        E1=e_list[0],
        E2=e_list[1],
        E3=e_list[2],
        E4=e_list[3],
        E5=e_list[4],
        penalty=float(data["penalty"]),
        final=final,
        status="PENDING"
    )

    db.session.add(routine)
    db.session.commit()

    submitted_users.add(current_user.username)

    return {"status": "PENDING"}


# =====================
# APPROVAL SYSTEM
# =====================
@app.route("/approve/<int:id>")
@login_required
def approve(id):
    if current_user.role != "ADMIN":
        return "Forbidden"

    r = Routine.query.get(id)
    r.status = "APPROVED"
    db.session.commit()

    update_board()

    return redirect("/control")


# =====================
# LIVE SCOREBOARD UPDATE
# =====================
def update_board():
    approved = Routine.query.filter_by(status="APPROVED").all()

    data = [{
        "nume": r.nume,
        "club": r.club,
        "final": r.final
    } for r in approved]

    data.sort(key=lambda x: -x["final"])

    socketio.emit("update", data)


# =====================
# RESET ROUND
# =====================
@app.route("/reset")
def reset():
    global submitted_users
    submitted_users = set()

    Routine.query.delete()
    db.session.commit()

    return {"reset": True}


# =====================
# RUN
# =====================
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)