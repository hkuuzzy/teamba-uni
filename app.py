from flask import Flask, render_template, request, redirect
from db import get_connection

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("About_page.html")

@app.route("/login")
def login():
    return render_template("Login_page.html")

@app.route("/subjects")
def subjects():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT subjects.subject_id, subjects.subject_name, units,
               teachers.first_name, teachers.last_name
        FROM subjects
        LEFT JOIN teachers ON subjects.teacher_id = teachers.teacher_id
    """)

    data = cursor.fetchall()
    conn.close()

    return render_template("Subject_Table.html", subjects=data)


if __name__ == "__main__":
    app.run(debug=True)

