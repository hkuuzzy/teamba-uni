from flask import Flask, render_template, request, redirect, url_for
from db import get_db_connection

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # TEMPORARY LOGIN CHECK (for demo)
        if username == "CedsParty67" and password == "Welcome2CiddysParty":
            return redirect(url_for("button"))
        else:
            return render_template("Login_page.html", error=True)

    return render_template("Login_page.html")
@app.route("/button")
def button():
    return render_template("button.html")

@app.route("/about")
def about():
    return render_template("About_page.html")


@app.route("/subjects")
def subjects():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT Subjects.SubjectID, SubjectName, Units,
               CONCAT(TeacherFN, ' ', TeacherLN) AS Teacher
        FROM Subjects
        LEFT JOIN Teachers ON Subjects.TeacherID = Teachers.TeacherID
    """)

    subjects = cursor.fetchall()
    conn.close()

    return render_template("Subject_Table.html", subjects=subjects)

@app.route("/students")
def students():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()

    conn.close()
    return render_template("Student_Table.html", students=students)

@app.route("/teachers")
def teachers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM teachers")
    teachers = cursor.fetchall()

    conn.close()
    return render_template("Teacher_Table.html", teachers=teachers)




if __name__ == "__main__":
    app.run(debug=True)

