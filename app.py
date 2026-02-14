from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error


app = Flask(__name__)
app.secret_key = 'subject_crud_secret_key_2024'

#database configuration
db_config = {
    'host': 'localhost',
    'database': 'Info_Man_Proj',  # USE YOUR DATABASE NAME
    'user': 'root',  # USE YOUR USERNAME
    'password': 'SQL1234',  # USE YOUR PASSWORD
    'port': 3306
}


#connection db helper
def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Connection error: {e}")
        return None


#get teacher helper
def get_all_teachers():
    """Get all teachers for the dropdown menu"""
    connection = None
    cursor = None
    teachers = []

    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                           SELECT TeacherID, CONCAT(TeacherFN, ' ', TeacherLN) AS FullName
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


#show subjects
@app.route('/')
def index():
    """Display all subjects with teacher names"""
    connection = None
    cursor = None
    subjects = []

    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)

            # Get subjects with teacher names
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
        print(f"Database error: {e}")
        flash(f'Error loading subjects: {str(e)}', 'error')
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    #get teachers from teacher table
    teachers = get_all_teachers()

    return render_template('test.html',
                           subjects=subjects,
                           teachers=teachers)


#create
@app.route('/add_subject', methods=['POST'])
def add_subject():
    """Add a new subject to the database"""
    connection = None
    cursor = None

    try:
        # Get form data
        subject_name = request.form['SubjectName'].strip()
        units = request.form['Units'].strip()
        teacher_id = request.form.get('TeacherID', '')

        # Validation
        if not subject_name:
            flash('Subject name is required!', 'error')
            return redirect(url_for('index'))

        if len(subject_name) < 2:
            flash('Subject name must be at least 2 characters!', 'error')
            return redirect(url_for('index'))

        try:
            units_int = int(units)
            if units_int < 1 or units_int > 10:
                flash('Units must be between 1 and 10!', 'error')
                return redirect(url_for('index'))
        except ValueError:
            flash('Units must be a valid number!', 'error')
            return redirect(url_for('index'))

        # Handle teacher ID (can be empty)
        teacher_id_int = None
        if teacher_id and teacher_id.strip():
            try:
                teacher_id_int = int(teacher_id)
            except ValueError:
                flash('Invalid teacher selection!', 'error')
                return redirect(url_for('index'))

        # Insert into database
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
        flash(f'❌ Subject "{subject_name}" already exists!', 'error')
        if connection:
            connection.rollback()
    except Exception as e:
        flash(f'❌ Error adding subject: {str(e)}', 'error')
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return redirect(url_for('index'))


#delete subject
@app.route('/delete_subject/<int:subject_id>')
def delete_subject(subject_id):
    """Delete a subject from the database"""
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()

            # Get subject name for flash message
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
        flash(f'❌ Error deleting subject: {str(e)}', 'error')
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return redirect(url_for('index'))


#edit function
@app.route('/edit_subject/<int:subject_id>')
def edit_subject(subject_id):
    """Display edit form for a subject"""
    connection = None
    cursor = None
    subject = None

    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)

            # Get subject details
            cursor.execute("""
                           SELECT s.SubjectID,
                                  s.SubjectName,
                                  s.Units,
                                  s.TeacherID,
                                  CONCAT(t.TeacherFN, ' ', t.TeacherLN) AS TeacherFullName
                           FROM Subjects s
                                    LEFT JOIN Teachers t ON s.TeacherID = t.TeacherID
                           WHERE s.SubjectID = %s
                           """, (subject_id,))

            subject = cursor.fetchone()

            if not subject:
                flash(f'❌ Subject not found!', 'error')
                return redirect(url_for('index'))

    except Exception as e:
        flash(f'❌ Error loading subject: {str(e)}', 'error')
        return redirect(url_for('index'))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    # Get teachers for dropdown
    teachers = get_all_teachers()

    return render_template('testedit.html',
                           subject=subject,
                           teachers=teachers)

#update subject
@app.route('/update_subject/<int:subject_id>', methods=['POST'])
def update_subject(subject_id):
    """Update an existing subject"""
    connection = None
    cursor = None

    try:
        # Get form data
        subject_name = request.form['SubjectName'].strip()
        units = request.form['Units'].strip()
        teacher_id = request.form.get('TeacherID', '')

        # Validation
        if not subject_name:
            flash('Subject name is required!', 'error')
            return redirect(url_for('edit_subject', subject_id=subject_id))

        try:
            units_int = int(units)
            if units_int < 1 or units_int > 10:
                flash('Units must be between 1 and 10!', 'error')
                return redirect(url_for('edit_subject', subject_id=subject_id))
        except ValueError:
            flash('Units must be a valid number!', 'error')
            return redirect(url_for('edit_subject', subject_id=subject_id))

        # Handle teacher ID
        teacher_id_int = None
        if teacher_id and teacher_id.strip():
            try:
                teacher_id_int = int(teacher_id)
            except ValueError:
                flash('Invalid teacher selection!', 'error')
                return redirect(url_for('edit_subject', subject_id=subject_id))

        # Update database
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

    except mysql.connector.IntegrityError:
        flash(f'❌ Subject name already exists!', 'error')
        if connection:
            connection.rollback()
    except Exception as e:
        flash(f'❌ Error updating subject: {str(e)}', 'error')
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return redirect(url_for('index'))

#run app
if __name__ == '__main__':
    app.run(debug=True, port=5000)