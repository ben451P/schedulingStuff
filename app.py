from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from sqlalchemy import JSON
from sqlalchemy.orm.attributes import flag_modified
from dotenv import load_dotenv

from backend.utils import time_to_minutes
from backend.scheduler import Scheduler
from backend.xlsx_writer import XLSXWriter

ROTATION_CYCLE = {"data":[
    "Kiddie", "Dive", "Main", "Break", "First Aid", "Slide",
    "Main2", "Rover", "Lap", "See Manager", "Bathroom Break"
]}

STATION_IMPORTANCE_DESCENDING = {"data":[
    "Bathroom Break", "Rover", "Main2", "See Manager", "Slide",
    "Kiddie", "First Aid", "Dive", "Lap", "Main", "Break"
]}

SHIFTS = {"data":[
    ["Guard A", "09:45", "15:30", True, False],
    ["Guard B", "09:45", "15:30", True, False],
    ["Guard C", "10:30", "16:00", True, False],
    ["Guard D", "10:30", "16:00", True, False],
    ["Guard E", "11:00", "20:00", True, False],
    ["Guard F", "11:00", "20:00", True, False],
    ["Guard G", "11:00", "20:00", True, False],
    ["Guard H", "11:00", "20:00", True, False],
    ["Guard I", "13:00", "19:00", True, False],
    ["Guard J", "14:00", "20:00", True, False],
    ["Guard K", "14:00", "20:00", True, False],
    ["Guard L", "14:00", "20:00", True, False],
    ["Guard M", "15:30", "20:00", True, False],
]}
# Load environment variables
load_dotenv()


app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size


db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    preferences = db.relationship("Preferences", backref="user", lazy = True)

class Preferences(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    schedule_start = db.Column(db.String)
    schedule_end = db.Column(db.String)
    acceptable_lunch_start = db.Column(db.String)
    acceptable_lunch_end = db.Column(db.String)

    rotation_cycle = db.Column(JSON) #, default=load_default_rotation
    station_importance = db.Column(JSON) #, default=load_default_importance
    station_coverage_times = db.Column(JSON)
    shifts = db.Column(JSON)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def initialize_default_data():
    demo_user = User.query.first()
    if not demo_user:
        user = User(
            email='benlozzano@gmail.com',
            password="123"
        )
        db.session.add(user)
        db.session.commit()

        preferences = Preferences(
            account = user.id,
            schedule_start = "11:00",
            schedule_end = "19:30",
            acceptable_lunch_start = "13:00",
            acceptable_lunch_end="16:00",
            rotation_cycle=ROTATION_CYCLE["data"],
            station_importance=STATION_IMPORTANCE_DESCENDING["data"],
            shifts=SHIFTS["data"]
        )
        db.session.add(preferences)
        db.session.commit()

    
# Routes
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login',methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if not user:
            flash("User does not exist","warning")
            return redirect(url_for('login'))

        if user.password.strip() == password.strip():
            login_user(user)
            flash("Successfully logged in","success")
        return redirect(url_for('index'))
    return render_template("login.html")

@app.route('/logout', methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/fixed-vars', methods=["GET","POST"])
@login_required
def fixed_vars():
    
    preferences = Preferences.query.filter_by(account=current_user.id).first()
    if request.method == "POST":
        preferences.schedule_start = request.form.get("Start Time")
        preferences.schedule_end = request.form.get("End Time")
        preferences.acceptable_lunch_start = request.form.get("Lunch Start Time")
        preferences.acceptable_lunch_end = request.form.get("Lunch End Time")
        db.session.commit()
    starts_and_ends = {}

    starts_and_ends["Start Time"] = preferences.schedule_start
    starts_and_ends["End Time"] = preferences.schedule_end
    starts_and_ends["Lunch Start Time"] = preferences.acceptable_lunch_start
    starts_and_ends["Lunch End Time"] = preferences.acceptable_lunch_end

    coverage_times = preferences.station_coverage_times

    return render_template('fixed_vars.html',vars_list=starts_and_ends,coverage_times=coverage_times)

@app.route('/rotation-cycle', methods=["GET", "POST"])
@login_required
def rotation_cycle():
    preferences = Preferences.query.filter_by(account=current_user.id).first()
    print(preferences.station_importance)
    if request.method == "POST":
        ids = request.form.getlist('station_id[]')
        names = request.form.getlist('station_name[]')

        if len(ids) != len(names):
            flash("Submitted data malformed (ids and names mismatch).", "danger")
            return redirect(url_for('rotation_cycle'))

        if len(set(names)) != len(names):
            flash("Cannot have 2 stations with the same name!", "danger")
            return redirect(url_for('rotation_cycle'))

        old_cycle = preferences.rotation_cycle or []
        station_importance = preferences.station_importance or []


        old_map = {}
        for item in old_cycle:
            if isinstance(item, dict):
                old_map[item.get('id', item.get('name'))] = item.get('name')
            else:
                old_map[item] = item

        new_cycle_dicts = []
        for sid, sname in zip(ids, names):
            name = (sname or "").strip() or "New Station"

            old_name = old_map.get(sid, sid)
            if name != old_name:
                if old_name in station_importance:
                    station_importance = [name if x == old_name else x for x in station_importance]
                else:
                    if name not in station_importance:
                        station_importance.insert(0, name)

            new_cycle_dicts.append({"id": sid, "name": name})

        if not new_cycle_dicts:
            flash("Cannot save empty rotation. Add at least one station.", "warning")
            return redirect(url_for('rotation_cycle'))

        new_names = [d["name"] for d in new_cycle_dicts]
        station_importance = [x for x in station_importance if x in new_names]


        preferences.station_importance = station_importance.copy()
        preferences.rotation_cycle = new_names.copy()
        flag_modified(preferences, "station_importance")

        try:
            db.session.commit()
            flash("Rotation saved.", "success")
        except Exception:
            db.session.rollback()
            app.logger.exception("Failed saving rotation cycle")
            flash("Failed to save rotation cycle.", "danger")

        return redirect(url_for('rotation_cycle'))

    # GET: prepare cycles for template (convert legacy strings to dicts for template)
    cycles = preferences.rotation_cycle or []
    if cycles and isinstance(cycles[0], str):
        cycles = [{"id": c, "name": c} for c in cycles]

    return render_template('rotation_cycle.html', cycles=cycles)


@app.route('/importance',methods=["GET","POST"])
@login_required
def importance():
    preferences = Preferences.query.filter_by(account=current_user.id).first()

    if request.method == "POST":
        new_order = request.form.getlist('station_id[]')

        if not new_order:
            flash("No stations received. Nothing saved.", "warning")
            return redirect(url_for('importance'))
        
        new_order = new_order[::-1]

        preferences.station_importance = new_order
        try:
            db.session.commit()
            flash("Rotation order saved.", "success")
        except Exception as e:
            db.session.rollback()
            app.logger.exception("Failed saving rotation order")
            flash("Failed to save rotation order.", "danger")

        return redirect(url_for('importance'))

    cycles = preferences.station_importance[::-1] or []
    print(cycles)
    return render_template('importance.html',cycles=cycles)

@app.route('/shifts',methods=["GET","POST"])
@login_required
def shifts():
    preferences = Preferences.query.filter_by(account=current_user.id).first()
    if request.method == "POST":
        guard_names = request.form.getlist("guard_name[]")
        start_times = request.form.getlist("start_time[]")
        end_times = request.form.getlist("end_time[]")

        attendance = request.form.getlist("attendance[]")
        print(attendance, len(attendance))
        attendance = [i == "true" for i in attendance]

        lunch_break = request.form.getlist("lunch_break[]")
        print(lunch_break, len(lunch_break))
        lunch_break = [i == "true" for i in lunch_break]

        for i in range(len(start_times)):
            if time_to_minutes(start_times[i]) > time_to_minutes(end_times[i]):
                flash("All start times must be before end times", "danger")
                return redirect(url_for("shifts"))

        shifts = [[g, s, e, a, lb] for g, s, e, a, lb in zip(guard_names, start_times, end_times, attendance,lunch_break)]
        preferences.shifts = shifts
        # print(shifts)
        flag_modified(preferences,"shifts")
        try:
            db.session.commit()
            flash("Rotation order saved.", "success")
        except Exception as e:
            db.session.rollback()
            app.logger.exception("Failed saving new shifts")
            flash("Failed to save rotation order.", "danger")
        return redirect(url_for("shifts"))

    shifts_list = preferences.shifts or []
    return render_template('shifts.html',shifts_list=shifts_list, enumerate=enumerate)

@app.route('/generate_schedule',methods=["POST"])
@login_required
def generate_schedule():
    preferences = Preferences.query.filter_by(account=current_user.id).first()

    start = preferences.schedule_start
    end = preferences.schedule_end
    lunch_start = preferences.acceptable_lunch_start
    lunch_end = preferences.acceptable_lunch_end

    cycle = preferences.rotation_cycle
    importance = preferences.station_importance
    coverage_times = {i:[("11:00", "20:00")] for i in cycle} #change later
    #essentially marks them abscent bc they can never be considered an available guard
    # start_time <= time < end_time
    shifts = [[a,b,c] if d else [a,"00:00","00:00"] for a,b,c,d,_ in preferences.shifts]
    lunches = [e for _,_,_,_,e in preferences.shifts]

    scheduler = Scheduler(start,
                          end,
                          lunch_start,
                          lunch_end,
                          cycle,
                          importance,
                          coverage_times,
                          shifts)
    scheduler.manually_override_lunches(lunches)
    scheduler.schedule_lunches()
    scheduler.create_base_schedule()

    writer = XLSXWriter(scheduler)
    excel_file = writer.convert_to_excel()
    
    return send_file(
        excel_file,
        as_attachment=True,
        download_name="schedule.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        initialize_default_data()    

    app.run(debug=True, host='0.0.0.0', port=5000)
