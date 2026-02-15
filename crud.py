from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error


app = Flask(__name__)
app.secret_key = 'school_crud_secret_key_2024'


db_config = {
    'host': 'localhost',
    'database': 'Info_Man_Proj',
    'user': 'root',
    'password': 'SQL1234',
    'port': 3306
}



def get_db_connection():
    """Create and return database connection"""
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"❌ Connection error: {e}")
        return None



def get_all_teachers():
    """Get all teachers for dropdown"""
    connection = None
    cursor = None
    teachers = []

    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                           SELECT TeacherID,
                                  CONCAT(TeacherFN, ' ', TeacherLN) AS FullName
                           FROM Teachers
                           ORDER BY TeacherLN, TeacherFN
                           """)
            teachers = cursor.fetchall()
    except Error as e:
        print(f"Error fetching teachers: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return teachers



def get_all_sections():
    """Get all sections for dropdown"""
    connection = None
    cursor = None
    sections = []

    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                           SELECT SectionID, SectionName, GradeLevel
                           FROM Sections
                           ORDER BY GradeLevel, SectionName
                           """)
            sections = cursor.fetchall()
    except Error as e:
        print(f"Error fetching sections: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return sections



def get_all_subjects():
    """Get all subjects with teacher names"""
    connection = None
    cursor = None
    subjects = []

    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                           SELECT s.SubjectID,
                                  s.SubjectName,
                                  s.Units,
                                  s.TeacherID,
                                  CONCAT(t.TeacherFN, ' ', t.TeacherLN) AS TeacherFullName
                           FROM Subjects s
                                    LEFT JOIN Teachers t ON s.TeacherID = t.TeacherID
                           ORDER BY s.SubjectID DESC
                           """)
            subjects = cursor.fetchall()
    except Error as e:
        print(f"Error fetching subjects: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return subjects


@app.route('/')
def index():
    """Display subjects page (default home)"""
    subjects = get_all_subjects()
    teachers = get_all_teachers()

    return render_template('subjects.html',
                           subjects=subjects,
                           teachers=teachers)


@app.route('/add_subject', methods=['POST'])
def add_subject():
    """Add a new subject"""
    connection = None
    cursor = None

    try:
        subject_name = request.form['SubjectName'].strip()
        units = request.form['Units'].strip()
        teacher_id = request.form.get('TeacherID', '')

        # Validation
        if not subject_name:
            flash('Subject name is required!', 'error')
            return redirect(url_for('index'))

        try:
            units_int = int(units)
            if units_int < 1 or units_int > 10:
                flash('Units must be between 1 and 10!', 'error')
                return redirect(url_for('index'))
        except ValueError:
            flash('Units must be a valid number!', 'error')
            return redirect(url_for('index'))

        teacher_id_int = None
        if teacher_id and teacher_id.strip():
            try:
                teacher_id_int = int(teacher_id)
            except ValueError:
                flash('Invalid teacher selection!', 'error')
                return redirect(url_for('index'))

        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("""
                           INSERT INTO Subjects (SubjectName, Units, TeacherID)
                           VALUES (%s, %s, %s)
                           """, (subject_name, units_int, teacher_id_int))
            connection.commit()
            flash(f'✅ Subject "{subject_name}" added successfully!', 'success')

    except mysql.connector.IntegrityError:
        flash(f'❌ Subject already exists!', 'error')
        if connection:
            connection.rollback()
    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'error')
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return redirect(url_for('index'))


@app.route('/delete_subject/<int:subject_id>')
def delete_subject(subject_id):
    """Delete a subject"""
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()


            cursor.execute("SELECT COUNT(*) FROM Enrollment WHERE SubjectID = %s", (subject_id,))
            count = cursor.fetchone()[0]

            if count > 0:
                flash('❌ Cannot delete subject with existing enrollments!', 'error')
                return redirect(url_for('index'))

            cursor.execute("SELECT SubjectName FROM Subjects WHERE SubjectID = %s", (subject_id,))
            result = cursor.fetchone()

            if result:
                subject_name = result[0]
                cursor.execute("DELETE FROM Subjects WHERE SubjectID = %s", (subject_id,))
                connection.commit()
                flash(f'✅ Subject "{subject_name}" deleted successfully!', 'success')
            else:
                flash(f'❌ Subject not found!', 'error')

    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'error')
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return redirect(url_for('index'))


@app.route('/edit_subject/<int:subject_id>')
def edit_subject(subject_id):
    """Show edit form for subject"""
    connection = None
    cursor = None
    subject = None

    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Subjects WHERE SubjectID = %s", (subject_id,))
            subject = cursor.fetchone()

            if not subject:
                flash(f'Subject not found!', 'error')
                return redirect(url_for('index'))

    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('index'))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    teachers = get_all_teachers()
    return render_template('edit_subject.html', subject=subject, teachers=teachers)


@app.route('/update_subject/<int:subject_id>', methods=['POST'])
def update_subject(subject_id):
    """Update a subject"""
    connection = None
    cursor = None

    try:
        subject_name = request.form['SubjectName'].strip()
        units = request.form['Units'].strip()
        teacher_id = request.form.get('TeacherID', '')

        try:
            units_int = int(units)
        except ValueError:
            flash('Units must be a valid number!', 'error')
            return redirect(url_for('edit_subject', subject_id=subject_id))

        teacher_id_int = None
        if teacher_id and teacher_id.strip():
            try:
                teacher_id_int = int(teacher_id)
            except ValueError:
                flash('Invalid teacher selection!', 'error')
                return redirect(url_for('edit_subject', subject_id=subject_id))

        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("""
                           UPDATE Subjects
                           SET SubjectName = %s,
                               Units       = %s,
                               TeacherID   = %s
                           WHERE SubjectID = %s
                           """, (subject_name, units_int, teacher_id_int, subject_id))
            connection.commit()
            flash(f'✅ Subject updated successfully!', 'success')

    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return redirect(url_for('index'))



def get_all_students():
    """Get all students with section info"""
    connection = None
    cursor = None
    students = []

    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                           SELECT s.StudentID,
                                  s.StudFirstName,
                                  s.StudLastName,
                                  s.MiddleInitial,
                                  s.Bday,
                                  s.Address,
                                  sec.SectionName,
                                  sec.GradeLevel
                           FROM Students s
                                    LEFT JOIN Sections sec ON s.SectionID = sec.SectionID
                           ORDER BY s.StudLastName, s.StudFirstName
                           """)
            students = cursor.fetchall()
    except Error as e:
        print(f"Error fetching students: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return students


def get_student_by_id(student_id):
    """Get a specific student by ID"""
    connection = None
    cursor = None
    student = None

    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                           SELECT s.StudentID,
                                  s.StudFirstName,
                                  s.StudLastName,
                                  s.MiddleInitial,
                                  s.Bday,
                                  s.Address,
                                  s.SectionID,
                                  sec.SectionName,
                                  sec.GradeLevel
                           FROM Students s
                                    LEFT JOIN Sections sec ON s.SectionID = sec.SectionID
                           WHERE s.StudentID = %s
                           """, (student_id,))
            student = cursor.fetchone()
    except Error as e:
        print(f"Error fetching student: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return student


@app.route('/students')
def students_page():
    """Display students page"""
    students = get_all_students()
    sections = get_all_sections()

    return render_template('students.html',
                           students=students,
                           sections=sections)


@app.route('/add_student', methods=['POST'])
def add_student():
    """Add a new student"""
    connection = None
    cursor = None

    try:
        first_name = request.form['StudFirstName'].strip()
        last_name = request.form['StudLastName'].strip()
        middle_initial = request.form.get('MiddleInitial', '').strip().upper()
        bday = request.form['Bday']
        address = request.form.get('Address', '').strip()
        section_id = request.form.get('SectionID', '')


        if not first_name or not last_name:
            flash('First name and last name are required!', 'error')
            return redirect(url_for('students_page'))

        if not bday:
            flash('Birthday is required!', 'error')
            return redirect(url_for('students_page'))


        section_id_int = None
        if section_id and section_id.strip():
            try:
                section_id_int = int(section_id)
            except ValueError:
                flash('Invalid section selection!', 'error')
                return redirect(url_for('students_page'))

        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("""
                           INSERT INTO Students
                               (StudFirstName, StudLastName, MiddleInitial, Bday, Address, SectionID)
                           VALUES (%s, %s, %s, %s, %s, %s)
                           """, (first_name, last_name, middle_initial or None, bday, address or None, section_id_int))
            connection.commit()
            flash(f'✅ Student {first_name} {last_name} added successfully!', 'success')

    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'error')
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return redirect(url_for('students_page'))


@app.route('/delete_student/<int:student_id>')
def delete_student(student_id):
    """Delete a student"""
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()


            cursor.execute("SELECT COUNT(*) FROM Enrollment WHERE StudentID = %s", (student_id,))
            count = cursor.fetchone()[0]

            if count > 0:
                flash('❌ Cannot delete student with existing enrollments!', 'error')
                return redirect(url_for('students_page'))

            cursor.execute("SELECT StudFirstName, StudLastName FROM Students WHERE StudentID = %s", (student_id,))
            result = cursor.fetchone()

            if result:
                first_name, last_name = result
                cursor.execute("DELETE FROM Students WHERE StudentID = %s", (student_id,))
                connection.commit()
                flash(f'✅ Student {first_name} {last_name} deleted successfully!', 'success')
            else:
                flash(f'❌ Student not found!', 'error')

    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'error')
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return redirect(url_for('students_page'))


@app.route('/edit_student/<int:student_id>')
def edit_student(student_id):
    """Show edit form for student"""
    student = get_student_by_id(student_id)

    if not student:
        flash(f'Student not found!', 'error')
        return redirect(url_for('students_page'))

    sections = get_all_sections()

    return render_template('edit_student.html',
                           student=student,
                           sections=sections)


@app.route('/update_student/<int:student_id>', methods=['POST'])
def update_student(student_id):
    """Update a student"""
    connection = None
    cursor = None

    try:
        first_name = request.form['StudFirstName'].strip()
        last_name = request.form['StudLastName'].strip()
        middle_initial = request.form.get('MiddleInitial', '').strip().upper()
        bday = request.form['Bday']
        address = request.form.get('Address', '').strip()
        section_id = request.form.get('SectionID', '')

        # Validation
        if not first_name or not last_name:
            flash('First name and last name are required!', 'error')
            return redirect(url_for('edit_student', student_id=student_id))

        if not bday:
            flash('Birthday is required!', 'error')
            return redirect(url_for('edit_student', student_id=student_id))


        section_id_int = None
        if section_id and section_id.strip():
            try:
                section_id_int = int(section_id)
            except ValueError:
                flash('Invalid section selection!', 'error')
                return redirect(url_for('edit_student', student_id=student_id))

        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("""
                           UPDATE Students
                           SET StudFirstName = %s,
                               StudLastName  = %s,
                               MiddleInitial = %s,
                               Bday          = %s,
                               Address       = %s,
                               SectionID     = %s
                           WHERE StudentID = %s
                           """, (first_name, last_name, middle_initial or None, bday, address or None, section_id_int,
                                 student_id))
            connection.commit()
            flash(f'✅ Student updated successfully!', 'success')

    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'error')
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return redirect(url_for('students_page'))



@app.route('/teachers')
def teachers_page():
    """Display all teachers (view only)"""
    connection = None
    cursor = None
    teachers = []

    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                           SELECT TeacherID,
                                  TeacherFN,
                                  TeacherLN,
                                  Department
                           FROM Teachers
                           ORDER BY Department, TeacherLN, TeacherFN
                           """)
            teachers = cursor.fetchall()
    except Error as e:
        flash(f'Error loading teachers: {str(e)}', 'error')
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return render_template('teachers.html', teachers=teachers)


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("🚀 Starting School Management System")
    print("📍 Subjects CRUD: http://localhost:5000")
    print("📍 Students CRUD: http://localhost:5000/students")
    print("=" * 50)
    app.run(debug=True, port=5000)