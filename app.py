# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///idcards.db'
app.config['SECRET_KEY'] = 'change_this_to_a_random_secret'
db = SQLAlchemy(app)

# --------- Models ----------
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    division = db.Column(db.String(20))
    year = db.Column(db.String(20))
    status = db.Column(db.String(50))          # "Ready", "Not Ready", "Missing Details", "Collected"
    missing_fields = db.Column(db.String(200)) # optional short text

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

# --------- Routes ----------
@app.route('/', methods=['GET', 'POST'])
def index():
    student = None
    if request.method == 'POST':
        roll_no = request.form.get('roll_no', '').strip()
        student = Student.query.filter_by(roll_no=roll_no).first()
    return render_template('index.html', student=student)

@app.route('/idcard/<int:student_id>')
def idcard(student_id):
    student = Student.query.get_or_404(student_id)
    return render_template('id_card.html', student=student)

# ---- Admin ----
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('admin_login.html')

def admin_required():
    return session.get('admin_logged_in', False)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not admin_required():
        return redirect(url_for('admin_login'))
    students = Student.query.order_by(Student.roll_no).all()
    return render_template('admin_dashboard.html', students=students)

@app.route('/admin/add', methods=['GET', 'POST'])
def admin_add():
    if not admin_required():
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        roll_no = request.form['roll_no'].strip()
        name = request.form['name'].strip()
        division = request.form.get('division','').strip()
        year = request.form.get('year','').strip()
        status = request.form.get('status','Not Ready').strip()
        missing_fields = request.form.get('missing_fields','').strip()
        if Student.query.filter_by(roll_no=roll_no).first():
            flash('Roll No already exists', 'warning')
        else:
            s = Student(roll_no=roll_no, name=name, division=division, year=year, status=status, missing_fields=missing_fields)
            db.session.add(s)
            db.session.commit()
            flash('Student added', 'success')
            return redirect(url_for('admin_dashboard'))
    return render_template('admin_form.html', student=None)

@app.route('/admin/edit/<int:sid>', methods=['GET', 'POST'])
def admin_edit(sid):
    if not admin_required():
        return redirect(url_for('admin_login'))
    student = Student.query.get_or_404(sid)
    if request.method == 'POST':
        student.roll_no = request.form['roll_no'].strip()
        student.name = request.form['name'].strip()
        student.division = request.form.get('division','').strip()
        student.year = request.form.get('year','').strip()
        student.status = request.form.get('status','Not Ready').strip()
        student.missing_fields = request.form.get('missing_fields','').strip()
        db.session.commit()
        flash('Updated', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_form.html', student=student)

@app.route('/admin/delete/<int:sid>')
def admin_delete(sid):
    if not admin_required():
        return redirect(url_for('admin_login'))
    student = Student.query.get_or_404(sid)
    db.session.delete(student)
    db.session.commit()
    flash('Deleted', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/mark_collected/<int:sid>')
def mark_collected(sid):
    if not admin_required():
        return redirect(url_for('admin_login'))
    student = Student.query.get_or_404(sid)
    student.status = 'Collected'
    db.session.commit()
    flash('Marked as collected', 'success')
    return redirect(url_for('admin_dashboard'))

# --------- DB setup + seed ----------
def seed_initial_data():
    if Admin.query.count() == 0:
        a = Admin(username='admin', password_hash=generate_password_hash('admin123'))
        db.session.add(a)
    if Student.query.count() == 0:
        sample = [
            ('SP04230001','Anita Patil','A','TY','Ready',''),
            ('SP04230002','Bhavna Shinde','A','TY','Not Ready',''),
            ('SP04230003','Chitra More','A','TY','Missing Details','photo missing'),
            ('SP04230004','Deepa Kulkarni','A','TY','Ready',''),
            ('SP04230005','Esha Joshi','A','TY','Not Ready',''),
        ]
        for r,name,div,yr,status,miss in sample:
            s = Student(roll_no=r, name=name, division=div, year=yr, status=status, missing_fields=miss)
            db.session.add(s)
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_initial_data()
    app.run(debug=True)
