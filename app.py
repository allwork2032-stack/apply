from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
import sqlite3
import os
import hashlib
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}

# Initialize database
def init_db():
    conn = sqlite3.connect('government_jobs.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nid TEXT UNIQUE NOT NULL,
                  name TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  phone TEXT NOT NULL,
                  password TEXT NOT NULL,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # Create jobs table
    c.execute('''CREATE TABLE IF NOT EXISTS jobs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  department TEXT NOT NULL,
                  circular_no TEXT UNIQUE NOT NULL,
                  publish_date DATE NOT NULL,
                  deadline DATE NOT NULL,
                  description TEXT NOT NULL,
                  requirements TEXT NOT NULL,
                  salary TEXT,
                  application_fee DECIMAL(10,2) DEFAULT 0,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # Create applications table
    c.execute('''CREATE TABLE IF NOT EXISTS applications
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  job_id INTEGER NOT NULL,
                  nid TEXT NOT NULL,
                  name TEXT NOT NULL,
                  father_name TEXT NOT NULL,
                  mother_name TEXT NOT NULL,
                  dob DATE NOT NULL,
                  gender TEXT NOT NULL,
                  education TEXT NOT NULL,
                  experience TEXT NOT NULL,
                  photo_path TEXT NOT NULL,
                  signature_path TEXT NOT NULL,
                  resume_path TEXT NOT NULL,
                  nid_front_path TEXT NOT NULL,
                  nid_back_path TEXT NOT NULL,
                  payment_method TEXT,
                  transaction_id TEXT,
                  status TEXT DEFAULT 'pending',
                  applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id),
                  FOREIGN KEY (job_id) REFERENCES jobs (id))''')
    
    # Insert sample job
    try:
        c.execute('''INSERT INTO jobs 
                    (title, department, circular_no, publish_date, deadline, description, requirements, salary, application_fee)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 ('সহকারী প্রোগ্রামার', 'তথ্য ও যোগাযোগ প্রযুক্তি বিভাগ', 'ICT-01/2023', 
                  '2023-11-01', '2023-12-15', 
                  'তথ্য ও যোগাযোগ প্রযুক্তি বিভাগে সহকারী প্রোগ্রামার পদে আবেদন গ্রহণ।', 
                  'কম্পিউটার বিজ্ঞান/প্রকৌশলে স্নাতক ডিগ্রী, প্রোগ্রামিং ভাষায় অভিজ্ঞতা', 
                  '২৫,০০০ - ৬০,০০০', 500.00))
    except sqlite3.IntegrityError:
        pass  # Already exists
    
    conn.commit()
    conn.close()

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Routes
@app.route('/')
def index():
    conn = sqlite3.connect('government_jobs.db')
    c = conn.cursor()
    c.execute("SELECT * FROM jobs WHERE deadline >= date('now') ORDER BY publish_date DESC")
    jobs = c.fetchall()
    conn.close()
    
    return render_template('index.html', jobs=jobs)

@app.route('/job/<int:job_id>')
def job_details(job_id):
    conn = sqlite3.connect('government_jobs.db')
    c = conn.cursor()
    c.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    job = c.fetchone()
    conn.close()
    
    if job:
        return render_template('job_details.html', job=job)
    else:
        return "Job not found", 404

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nid = request.form['nid']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = hash_password(request.form['password'])
        
        conn = sqlite3.connect('government_jobs.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (nid, name, email, phone, password) VALUES (?, ?, ?, ?, ?)",
                     (nid, name, email, phone, password))
            conn.commit()
            conn.close()
            return jsonify({"message": "নিবন্ধন সফল হয়েছে! এখন লগইন করুন।", "status": "success"})
        except sqlite3.IntegrityError as e:
            conn.close()
            return jsonify({"message": "এই NID বা ইমেইল already registered!", "status": "error"})
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nid = request.form['nid']
        password = hash_password(request.form['password'])
        
        conn = sqlite3.connect('government_jobs.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE nid = ? AND password = ?", (nid, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['user_nid'] = user[1]
            session['user_name'] = user[2]
            return jsonify({"message": "লগইন সফল হয়েছে!", "status": "success", "redirect": "/"})
        else:
            return jsonify({"message": "ভুল NID বা পাসওয়ার্ড!", "status": "error"})
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
def apply_job(job_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get form data
        nid = session['user_nid']
        name = request.form['name']
        father_name = request.form['father_name']
        mother_name = request.form['mother_name']
        dob = request.form['dob']
        gender = request.form['gender']
        education = request.form['education']
        experience = request.form['experience']
        payment_method = request.form['payment_method']
        transaction_id = request.form.get('transaction_id', '')
        
        # File upload handling
        def save_upload(file_field, subfolder):
            if file_field not in request.files:
                return None
            file = request.files[file_field]
            if file.filename == '':
                return None
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{session['user_id']}_{file_field}_{file.filename}")
                path = os.path.join(app.config['UPLOAD_FOLDER'], subfolder, filename)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                file.save(path)
                return path
            return None
        
        photo_path = save_upload('photo', 'photos')
        signature_path = save_upload('signature', 'signatures')
        resume_path = save_upload('resume', 'resumes')
        nid_front_path = save_upload('nid_front', 'nids')
        nid_back_path = save_upload('nid_back', 'nids')
        
        # Save application to database
        conn = sqlite3.connect('government_jobs.db')
        c = conn.cursor()
        try:
            c.execute('''INSERT INTO applications 
                        (user_id, job_id, nid, name, father_name, mother_name, dob, gender, 
                         education, experience, photo_path, signature_path, resume_path, 
                         nid_front_path, nid_back_path, payment_method, transaction_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                     (session['user_id'], job_id, nid, name, father_name, mother_name, dob, gender,
                      education, experience, photo_path, signature_path, resume_path,
                      nid_front_path, nid_back_path, payment_method, transaction_id))
            conn.commit()
            conn.close()
            return jsonify({"message": "আবেদন সফলভাবে জমা হয়েছে!", "status": "success"})
        except Exception as e:
            conn.close()
            return jsonify({"message": f"ত্রুটি: {str(e)}", "status": "error"})
    
    # GET request - show application form
    conn = sqlite3.connect('government_jobs.db')
    c = conn.cursor()
    c.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    job = c.fetchone()
    conn.close()
    
    if job:
        return render_template('apply.html', job=job)
    else:
        return "Job not found", 404

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('government_jobs.db')
    c = conn.cursor()
    c.execute('''SELECT a.id, j.title, j.department, a.status, a.applied_at 
                 FROM applications a 
                 JOIN jobs j ON a.job_id = j.id 
                 WHERE a.user_id = ? 
                 ORDER BY a.applied_at DESC''', (session['user_id'],))
    applications = c.fetchall()
    conn.close()
    
    return render_template('dashboard.html', applications=applications, user_name=session['user_name'])

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    # Simple admin authentication (in production, use proper authentication)
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == 'admin' and password == 'admin123':
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='Invalid credentials')
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('government_jobs.db')
    c = conn.cursor()
    
    # Get stats
    c.execute("SELECT COUNT(*) FROM applications")
    total_applications = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM applications WHERE status = 'pending'")
    pending_applications = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM jobs")
    total_jobs = c.fetchone()[0]
    
    c.execute("SELECT j.title, COUNT(a.id) FROM jobs j LEFT JOIN applications a ON j.id = a.job_id GROUP BY j.id")
    applications_per_job = c.fetchall()
    
    conn.close()
    
    return render_template('admin_dashboard.html', 
                          total_applications=total_applications,
                          pending_applications=pending_applications,
                          total_jobs=total_jobs,
                          applications_per_job=applications_per_job)

if __name__ == '__main__':
    init_db()
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
