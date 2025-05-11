from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  # إضافة مكتبة Migrate
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///local.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#SQLAlchemy
db = SQLAlchemy(app)

#Flask-Migrate
migrate = Migrate(app, db)

class WorkFromOffice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)
    day = db.Column(db.String(10), nullable=False)
    month = db.Column(db.String(7), nullable=False)

class Holiday(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)
    day = db.Column(db.String(10), nullable=False)
    month = db.Column(db.String(7), nullable=False)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/view")
def view():
    month = request.args.get("month", datetime.now().strftime("%Y-%m"))
    work_entries = WorkFromOffice.query.filter_by(month=month).all()
    holiday_entries = Holiday.query.filter_by(month=month).all()
    return render_template("view.html", work=work_entries, holidays=holiday_entries, month=month)

@app.route("/edit/<entry_type>/<int:entry_id>", methods=["GET", "POST"])
def edit(entry_type, entry_id):
    Model = WorkFromOffice if entry_type == "work" else Holiday
    entry = Model.query.get_or_404(entry_id)

    if request.method == "POST":
        new_date = request.form.get("date")
        try:
            date_obj = datetime.strptime(new_date, "%Y-%m-%d")
            if date_obj.year != datetime.now().year:
                return "Year must match the current year."
            if date_obj.strftime("%A") in ["Saturday", "Sunday"]:
                return "Cannot use weekends."

            entry.date = date_obj.date()
            entry.day = date_obj.strftime("%A")
            entry.month = date_obj.strftime("%Y-%m")
            db.session.commit()
            return redirect(url_for("view"))
        except ValueError:
            return "Invalid date format."

    return render_template("edit.html", entry=entry, entry_type=entry_type)

@app.route("/delete/<entry_type>/<int:entry_id>", methods=["POST"])
def delete(entry_type, entry_id):
    Model = WorkFromOffice if entry_type == "work" else Holiday
    entry = Model.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    return redirect(url_for("view"))

@app.route("/add", methods=["POST"])
def add():
    date_input = request.form.get("date")
    entry_type = request.form.get("type")

    try:
        date_obj = datetime.strptime(date_input, "%Y-%m-%d")
        if date_obj.year != datetime.now().year:
            return "Year must match the current year."

        day_name = date_obj.strftime("%A")
        if day_name in ["Saturday", "Sunday"]:
            return "Cannot add entries for weekends."

        entry_data = {
            'date': date_obj.date(),
            'day': day_name,
            'month': date_obj.strftime("%Y-%m")
        }

        if entry_type == "work":
            if WorkFromOffice.query.filter_by(date=entry_data['date']).first():
                return "Date already exists in work."
            db.session.add(WorkFromOffice(**entry_data))
        else:
            if Holiday.query.filter_by(date=entry_data['date']).first():
                return "Date already exists in holidays."
            db.session.add(Holiday(**entry_data))

        db.session.commit()
        return redirect(url_for("view"))

    except ValueError:
        return "Invalid date format."

if __name__ == "__main__":
    app.run(debug=True)