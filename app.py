from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate 
from datetime import datetime
import os
import csv
from io import StringIO
from flask import Response
import pandas as pd
from flask import send_file
from io import BytesIO

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

@app.route("/export")
def export():
    month = request.args.get("month", datetime.now().strftime("%Y-%m"))
    
    work_entries = WorkFromOffice.query.filter_by(month=month).all()
    holiday_entries = Holiday.query.filter_by(month=month).all()


    work_data = [{"Date": entry.date, "Day": entry.day, "Type": "Work"} for entry in work_entries]
    holiday_data = [{"Date": entry.date, "Day": entry.day, "Type": "Holiday"} for entry in holiday_entries]


    df = pd.DataFrame(work_data + holiday_data)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Entries")

    output.seek(0)
    filename = f"entries_{month}.xlsx"
    return send_file(output, download_name=filename, as_attachment=True, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route("/export/csv")
def export_csv():
    month = request.args.get("month", datetime.now().strftime("%Y-%m"))
    work_entries = WorkFromOffice.query.filter_by(month=month).all()
    holiday_entries = Holiday.query.filter_by(month=month).all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Type", "Date", "Day"])

    for row in work_entries:
        writer.writerow(["Work", row.date, row.day])
    for row in holiday_entries:
        writer.writerow(["Holiday", row.date, row.day])

    output.seek(0)
    return Response(output, mimetype="text/csv", headers={
        "Content-Disposition": f"attachment;filename=report_{month}.csv"
    })


@app.route("/export/excel")
def export_excel():
    month = request.args.get("month", datetime.now().strftime("%Y-%m"))
    work_entries = WorkFromOffice.query.filter_by(month=month).all()
    holiday_entries = Holiday.query.filter_by(month=month).all()

    work_data = [{"Date": entry.date, "Day": entry.day, "Type": "Work"} for entry in work_entries]
    holiday_data = [{"Date": entry.date, "Day": entry.day, "Type": "Holiday"} for entry in holiday_entries]

    df = pd.DataFrame(work_data + holiday_data)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Entries")

    output.seek(0)
    filename = f"entries_{month}.xlsx"
    return send_file(output, download_name=filename, as_attachment=True, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.route("/view")
def view():
    month = request.args.get("month", datetime.now().strftime("%Y-%m"))
    work_entries = WorkFromOffice.query.filter_by(month=month).all()
    holiday_entries = Holiday.query.filter_by(month=month).all()
    
    work_count = len(work_entries)
    holiday_count = len(holiday_entries)

    return render_template(
        "view.html",
        work=work_entries,
        holidays=holiday_entries,
        month=month,
        work_count=work_count,
        holiday_count=holiday_count
    )


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
