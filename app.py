import os
import sys
from datetime import datetime, date, timedelta

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

# -----------------------------------------------------------------------------
# a. Determine the absolute path of the executable or script
# Check if the application is run as a bundled executable (e.g., PyInstaller)
# -----------------------------------------------------------------------------
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable) # bundled executable
else:
    application_path = os.path.dirname(os.path.abspath(__file__)) # normal Python environment

os.chdir(application_path) # Change working directory to ensure Flask finds templates and static files

# -----------------------------------------------------------------------------
# b. Load environment variables from .env file manually
# Parses key-value pairs and sets them in os.environ
# -----------------------------------------------------------------------------
env_path = os.path.join(application_path, '.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ[k.strip()] = v.strip()

# -----------------------------------------------------------------------------
# c. Initialize Flask Application
# Configure template and static folders based on the application path
# -----------------------------------------------------------------------------
app = Flask(__name__, 
            template_folder=os.path.join(application_path, 'templates'),
            static_folder=os.path.join(application_path, 'static'))

app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_key') # Set secret key for session management (fallback to default if not set)

# -----------------------------------------------------------------------------
# d. Configure SQLite Database
# Create 'instance' folder to store the database file securely
# -----------------------------------------------------------------------------
instance_path = os.path.join(application_path, 'instance')
os.makedirs(instance_path, exist_ok=True)
db_file_path = os.path.join(instance_path, 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_file_path.replace('\\', '/') # Normalize path separators for SQLite URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# -----------------------------------------------------------------------------
# e. Configure File Uploads
# Set upload folder for avatars and limit maximum file size to 5MB
# -----------------------------------------------------------------------------
upload_path = os.path.join(application_path, 'static', 'avatars')
os.makedirs(upload_path, exist_ok=True)
app.config['UPLOAD_FOLDER'] = upload_path
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

db = SQLAlchemy(app) # Initialize SQLAlchemy database instance


# ==========================================
# 1. Tables' Definition (Database Models)
# ==========================================

# Representative Table (業務代表表)
class Representative(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)    # representative name

# Personnel Table (參與人員表)
class Personnel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)    # personnel name
    display_name = db.Column(db.String(50), nullable=True)          # display name
    avatar_filename = db.Column(db.String(255), nullable=True)      # avatar image filename

# Category Table (專案種類表)
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)    # category name/value


# Project Table (專案總表)
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)                # project name
    status = db.Column(db.String(20), nullable=False)               # project status
    rep = db.Column(db.String(50), nullable=False)                  # representative
    equipment = db.Column(db.String(100), nullable=True)            # equipment
    category = db.Column(db.String(50), nullable=False)             # project category
    description = db.Column(db.Text, nullable=True)                 # project description
    start_date = db.Column(db.Date, nullable=False)                 # start date
    end_date = db.Column(db.Date, nullable=True)                    # end date
    notes = db.Column(db.Text, nullable=True)                       # notes
    
    tasks = db.relationship('Task', backref='project', lazy=True, cascade='all, delete-orphan') # relationship with Task

# Task Table (工作紀錄表)
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    personnel = db.Column(db.String(50), nullable=False)            # personnel
    date = db.Column(db.Date, nullable=False)                       # work date
    work_days = db.Column(db.Float, nullable=False)                 # work days (support decimal)
    description = db.Column(db.Text, nullable=False)                # work description
    notes = db.Column(db.Text, nullable=True)                       # notes
    
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False) # relationship with Project

# ==========================================
# 2. Routes
# ==========================================

# -----------------------------------------------------------------------------
# Index Page: Dashboard showing stats (active projects, personnel, monthly work)
# -----------------------------------------------------------------------------
@app.route('/')
def index():
    # Calculate Dashboard Stats
    active_projects_count = Project.query.filter_by(status='進行中').count()
    total_personnel = Personnel.query.count()
    
    # Calculate total work days for current month
    today = date.today()
    start_of_month = date(today.year, today.month, 1)
    if today.month == 12:
        end_of_month = date(today.year + 1, 1, 1)
    else:
        end_of_month = date(today.year, today.month + 1, 1)
        
    tasks_this_month = Task.query.filter(Task.date >= start_of_month, Task.date < end_of_month).all()
    monthly_work_days = sum(t.work_days for t in tasks_this_month)
    
    return render_template('index.html', 
                           active_projects=active_projects_count,
                           total_personnel=total_personnel,
                           monthly_work_days=monthly_work_days)

# -----------------------------------------------------------------------------
# Add Task Page: Form to create a new work log entry
# Validates input data and saves to database
# -----------------------------------------------------------------------------
@app.route('/add-task', methods=['GET', 'POST'])
def add_task():
    if request.method == 'POST':
        personnel = request.form.get('personnel')
        project_id = request.form.get('project_id')
        date_str = request.form.get('date')
        work_days_str = request.form.get('work_days')
        description = request.form.get('description')
        notes = request.form.get('notes')

        # Validate date format
        try:
            task_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
        except ValueError:
            flash('日期格式錯誤', 'error')
            return redirect(url_for('add_task'))

        # Validate required fields
        if not personnel or not project_id or not task_date or not description or not work_days_str:
            flash('請填寫所有必填欄位', 'error')
            return redirect(url_for('add_task'))

        # Validate work days number
        try:
            work_days = float(work_days_str)
        except (ValueError, TypeError):
            flash('工作天數格式錯誤', 'error')
            return redirect(url_for('add_task'))

        # Create new Task object
        new_task = Task(
            personnel=personnel,
            project_id=int(project_id),
            date=task_date,
            work_days=work_days,
            description=description,
            notes=notes
        )

        # Save to database
        try:
            db.session.add(new_task)
            db.session.commit()
            flash('✅ 工作紀錄已新增！', 'success')
            return redirect(url_for('employee_case', person=personnel))
        except Exception as e:
            db.session.rollback()
            flash(f'發生錯誤：{str(e)}', 'error')

    projects = Project.query.order_by(Project.name).all()
    personnel_list = [p.name for p in Personnel.query.order_by(Personnel.name).all()]
    return render_template('add_task.html', projects=projects, personnel_list=personnel_list)

# -----------------------------------------------------------------------------
# Add Project Page: Form to create a new project
# Automatically creates new Representative/Category if they don't exist
# -----------------------------------------------------------------------------
@app.route('/add-project', methods=['GET', 'POST'])
def add_proj():
    if request.method == 'POST':
        name = request.form.get('name')
        status = request.form.get('status')
        category = request.form.get('category')
        rep = request.form.get('rep')
        equipment = request.form.get('equipment')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        description = request.form.get('description')
        notes = request.form.get('notes')

        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
        except ValueError:
            flash('日期格式錯誤', 'error')
            return redirect(url_for('add_proj'))

        if not name or not status or not category or not rep or not start_date:
            flash('請填寫所有必填欄位', 'error')
            return redirect(url_for('add_proj'))

        # Create Project object
        new_project = Project(
            name=name,
            status=status,
            category=category,
            rep=rep,
            equipment=equipment,
            description=description,
            start_date=start_date,
            end_date=end_date,
            notes=notes
        )

        try:
            db.session.add(new_project)
            # Auto-save new representative if not exists
            if rep and not Representative.query.filter_by(name=rep).first():
                db.session.add(Representative(name=rep))
            # Auto-save new category if not exists
            if category and not Category.query.filter_by(name=category).first():
                db.session.add(Category(name=category))
            db.session.commit()
            flash('✅ 專案已新增！', 'success')
            return redirect(url_for('proj_timeline'))
        except Exception as e:
            db.session.rollback()
            flash(f'發生錯誤：{str(e)}', 'error')
        
    # Load dropdown options
    reps = Representative.query.order_by(Representative.name).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template('add_proj.html', reps=reps, categories=categories)

# -----------------------------------------------------------------------------
# Edit Project: Update existing project details
# Similar logic to add_proj but updates an existing record
# -----------------------------------------------------------------------------
@app.route('/edit-project/<int:id>', methods=['GET', 'POST'])
def edit_project(id):
    project = Project.query.get_or_404(id)
    if request.method == 'POST':
        project.name = request.form.get('name')
        project.status = request.form.get('status')
        project.category = request.form.get('category')
        project.rep = request.form.get('rep')
        project.equipment = request.form.get('equipment')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        project.description = request.form.get('description')
        project.notes = request.form.get('notes')

        # Parse and update dates
        try:
            project.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
            project.end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
        except ValueError:
            flash('日期格式錯誤', 'error')
            return redirect(url_for('edit_project', id=id))

        try:
            # Auto-save new rep/category if changed to new values
            if project.rep and not Representative.query.filter_by(name=project.rep).first():
                db.session.add(Representative(name=project.rep))
            if project.category and not Category.query.filter_by(name=project.category).first():
                db.session.add(Category(name=project.category))
            db.session.commit()
            flash('✅ 專案已更新！', 'success')
            return redirect(url_for('proj_timeline'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失敗：{str(e)}', 'error')

    reps = Representative.query.order_by(Representative.name).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template('edit_proj.html', project=project, reps=reps, categories=categories)

# -----------------------------------------------------------------------------
# Delete Project: Remove project and associated tasks (cascade)
# -----------------------------------------------------------------------------
@app.route('/delete-project/<int:id>', methods=['POST'])
def delete_project(id):
    project = Project.query.get_or_404(id)
    try:
        db.session.delete(project)
        db.session.commit()
        flash('✅ 專案已刪除！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'刪除失敗：{str(e)}', 'error')
    return redirect(url_for('manage_db'))

# -----------------------------------------------------------------------------
# Manage Representatives: Add or delete business representatives
# -----------------------------------------------------------------------------
@app.route('/manage-reps', methods=['GET', 'POST'])
def manage_reps():
    if request.method == 'POST':
        action = request.form.get('action')
        rep_id = request.form.get('rep_id')
        rep_name = request.form.get('rep_name')

        if action == 'add' and rep_name:
            if not Representative.query.filter_by(name=rep_name).first():
                db.session.add(Representative(name=rep_name))
                db.session.commit()
                flash('✅ 業務代表已新增！', 'success')
            else:
                flash('該業務代表已經存在！', 'error')
        elif action == 'delete' and rep_id:
            rep = Representative.query.get(rep_id)
            if rep:
                db.session.delete(rep)
                db.session.commit()
                flash('✅ 業務代表已刪除！', 'success')
        
        return redirect(url_for('manage_reps'))
            
    reps = Representative.query.order_by(Representative.name).all()
    return render_template('manage_reps.html', reps=reps)

# Helper function to validate file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -----------------------------------------------------------------------------
# Manage Personnel: Add, edit, delete staff including avatar upload
# Handles file security and cleanup on deletion
# -----------------------------------------------------------------------------
@app.route('/manage-personnel', methods=['GET', 'POST'])
def manage_personnel():
    if request.method == 'POST':
        action = request.form.get('action')
        p_id = request.form.get('id')
        name = request.form.get('name')
        display_name = request.form.get('display_name')
        
        if action == 'add' and name:
            if not Personnel.query.filter_by(name=name).first():
                new_p = Personnel(name=name, display_name=display_name)
                # Handle avatar upload
                file = request.files.get('avatar')
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(f"avatar_{name}_{file.filename}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    new_p.avatar_filename = filename
                
                db.session.add(new_p)
                db.session.commit()
                flash('✅ 人員已新增！', 'success')
            else:
                flash('該人員已經存在！', 'error')
                
        elif action == 'edit' and p_id and name:
            p = Personnel.query.get(p_id)
            if p:
                p.name = name
                p.display_name = display_name
                # Handle avatar upload (overwrite existing)
                file = request.files.get('avatar')
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(f"avatar_{p.id}_{file.filename}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    p.avatar_filename = filename
                db.session.commit()
                flash('✅ 人員資料已更新！', 'success')
                
        elif action == 'delete' and p_id:
            p = Personnel.query.get(p_id)
            if p:
                # Delete associated avatar file from disk
                if p.avatar_filename:
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], p.avatar_filename)
                    if os.path.exists(filepath):
                        os.remove(filepath)
                db.session.delete(p)
                db.session.commit()
                flash('✅ 人員已刪除！', 'success')
                
        return redirect(url_for('manage_personnel'))
            
    personnel_list = Personnel.query.order_by(Personnel.name).all()
    return render_template('manage_personnel.html', personnel_list=personnel_list)

# -----------------------------------------------------------------------------
# Manage Categories: Add or delete project categories
# -----------------------------------------------------------------------------
@app.route('/manage-categories', methods=['GET', 'POST'])
def manage_categories():
    if request.method == 'POST':
        action = request.form.get('action')
        cat_id = request.form.get('cat_id')
        cat_name = request.form.get('cat_name')

        if action == 'add' and cat_name:
            if not Category.query.filter_by(name=cat_name).first():
                db.session.add(Category(name=cat_name))
                db.session.commit()
                flash('✅ 專案種類已新增！', 'success')
            else:
                flash('該種類已經存在！', 'error')
        elif action == 'delete' and cat_id:
            cat = Category.query.get(cat_id)
            if cat:
                db.session.delete(cat)
                db.session.commit()
                flash('✅ 專案種類已刪除！', 'success')
        
        return redirect(url_for('manage_categories'))
            
    categories = Category.query.order_by(Category.name).all()
    return render_template('manage_categories.html', categories=categories)

# -----------------------------------------------------------------------------
# Admin Authentication: Simple password protection for DB management
# -----------------------------------------------------------------------------
DB_ADMIN_PASSWORD = os.environ.get('DB_ADMIN_PASSWORD', 'admin123')

@app.route('/manage-db-login', methods=['GET', 'POST'])
def manage_db_login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == DB_ADMIN_PASSWORD:
            from flask import session
            session['db_admin_auth'] = True
            return redirect(url_for('manage_db'))
        else:
            flash('密碼錯誤，請重新輸入', 'error')
            return redirect(url_for('manage_db_login'))
    return render_template('manage_db_login.html')

# -----------------------------------------------------------------------------
# Manage DB Page: Overview of all tables (requires authentication)
# -----------------------------------------------------------------------------
@app.route('/manage-db')
def manage_db():
    from flask import session
    if not session.get('db_admin_auth'):
        return redirect(url_for('manage_db_login'))
    projects = Project.query.order_by(Project.id.desc()).all()
    tasks = Task.query.order_by(Task.id.desc()).all()
    reps = Representative.query.order_by(Representative.name).all()
    personnel_list = Personnel.query.order_by(Personnel.name).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template('manage_db.html', projects=projects, tasks=tasks, reps=reps, personnel=personnel_list, categories=categories)

# ==========================================
# Export / Import Project database
# ==========================================
@app.route('/api/export-db')
def export_db():
    import csv
    import io
    from flask import Response
    
    projects = Project.query.order_by(Project.start_date.desc()).all()
    
    output = io.StringIO()
    output.write('\ufeff') # Add BOM
    writer = csv.writer(output)
    writer.writerow(['專案名稱', '狀態', '業務代表', '設備', '專案種類', '內容敘述', '起始日', '結束日', '參與人員', '備註'])
    
    for p in projects:
        task_personnel = list(set([t.personnel for t in p.tasks]))
        personnel_str = ', '.join(task_personnel)
        writer.writerow([
            p.name, p.status, p.rep, p.equipment, p.category, p.description,
            p.start_date.strftime('%Y/%m/%d') if p.start_date else '',
            p.end_date.strftime('%Y/%m/%d') if p.end_date else '',
            personnel_str, p.notes
        ])
    
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=projects_export.csv"})

@app.route('/api/import-db', methods=['POST'])
def import_db():
    from flask import session
    if not session.get('db_admin_auth'):
        flash('未授權，請先登入', 'error')
        return redirect(url_for('manage_db_login'))

    import csv
    import io

    file = request.files.get('csv_file')
    if not file or file.filename == '':
        flash('請選擇 CSV 檔案', 'error')
        return redirect(url_for('manage_db'))

    mode = request.form.get('import_mode', 'skip')

    try:
        content = file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(content))

        imported = 0
        skipped = 0
        error_list = []

        for i, row in enumerate(reader, start=2):
            name = row.get('專案名稱', '').strip()
            if not name:
                continue

            status    = row.get('狀態', '').strip()
            rep       = row.get('業務代表', '').strip()
            equipment = row.get('設備', '').strip() or None
            category  = row.get('專案種類', '').strip()
            description = row.get('內容敘述', '').strip() or None
            start_date_str = row.get('起始日', '').strip()
            end_date_str   = row.get('結束日', '').strip()
            notes     = row.get('備註', '').strip() or None

            # Parse date
            try:
                start_date = datetime.strptime(start_date_str, '%Y/%m/%d').date() if start_date_str else None
                end_date   = datetime.strptime(end_date_str,   '%Y/%m/%d').date() if end_date_str   else None
            except ValueError:
                error_list.append(f'第 {i} 行「{name}」日期格式錯誤（需為 YYYY/MM/DD）')
                continue

            if not start_date:
                error_list.append(f'第 {i} 行「{name}」缺少起始日，已略過')
                continue

            existing = Project.query.filter_by(name=name).first()

            if existing:
                if mode == 'skip':
                    skipped += 1
                    continue
                else:
                    existing.status      = status
                    existing.rep         = rep
                    existing.equipment   = equipment
                    existing.category    = category
                    existing.description = description
                    existing.start_date  = start_date
                    existing.end_date    = end_date
                    existing.notes       = notes
                    imported += 1
            else:
                new_proj = Project(
                    name=name, status=status, rep=rep,
                    equipment=equipment, category=category,
                    description=description, start_date=start_date,
                    end_date=end_date, notes=notes
                )
                db.session.add(new_proj)
                imported += 1

            # Auto-create rep and category if not exists
            if rep and not Representative.query.filter_by(name=rep).first():
                db.session.add(Representative(name=rep))
            if category and not Category.query.filter_by(name=category).first():
                db.session.add(Category(name=category))

        db.session.commit()

        action_label = '更新' if mode == 'overwrite' else '新增'
        msg = f'✅ 匯入完成！{action_label} {imported} 筆，略過重複 {skipped} 筆。'
        if error_list:
            msg += f'（{len(error_list)} 筆錯誤）'
        flash(msg, 'success')

        for err in error_list[:5]:
            flash(err, 'error')

    except Exception as e:
        db.session.rollback()
        flash(f'匯入失敗：{str(e)}', 'error')

    return redirect(url_for('manage_db'))

# ==========================================
# Export / Import work tasks
# ==========================================
@app.route('/api/export-tasks')
def export_tasks():
    import csv, io
    from flask import Response, session
    if not session.get('db_admin_auth'):
        return redirect(url_for('manage_db_login'))
    tasks = Task.query.order_by(Task.id).all()
    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(['所屬專案', '人員', '日期', '工作天數', '工作描述', '備註'])
    for t in tasks:
        writer.writerow([
            t.project.name if t.project else '',
            t.personnel,
            t.date.strftime('%Y/%m/%d') if t.date else '',
            t.work_days,
            t.description,
            t.notes or ''
        ])
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment;filename=tasks_export.csv'})

@app.route('/api/import-tasks', methods=['POST'])
def import_tasks():
    from flask import session
    if not session.get('db_admin_auth'):
        flash('未授權，請先登入', 'error')
        return redirect(url_for('manage_db_login'))
    import csv, io
    file = request.files.get('csv_file')
    if not file or file.filename == '':
        flash('請選擇 CSV 檔案', 'error')
        return redirect(url_for('manage_db'))
    try:
        content = file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(content))
        imported = 0
        error_list = []
        for i, row in enumerate(reader, start=2):
            proj_name   = row.get('所屬專案', '').strip()
            personnel   = row.get('人員', '').strip()
            date_str    = row.get('日期', '').strip()
            work_days_s = row.get('工作天數', '').strip()
            description = row.get('工作描述', '').strip()
            notes       = row.get('備註', '').strip() or None
            if not proj_name or not personnel or not description:
                error_list.append(f'第 {i} 行缺少必填欄位，已略過')
                continue
            project = Project.query.filter_by(name=proj_name).first()
            if not project:
                error_list.append(f'第 {i} 行找不到專案「{proj_name}」，已略過')
                continue
            try:
                task_date  = datetime.strptime(date_str, '%Y/%m/%d').date() if date_str else None
                work_days  = float(work_days_s) if work_days_s else 0.0
            except ValueError:
                error_list.append(f'第 {i} 行日期或工作天數格式錯誤，已略過')
                continue
            db.session.add(Task(project_id=project.id, personnel=personnel,
                                date=task_date, work_days=work_days,
                                description=description, notes=notes))
            imported += 1
        db.session.commit()
        msg = f'✅ 工作紀錄匯入完成！新增 {imported} 筆。'
        if error_list:
            msg += f'（{len(error_list)} 筆錯誤）'
        flash(msg, 'success')
        for err in error_list[:5]:
            flash(err, 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'匯入失敗：{str(e)}', 'error')
    return redirect(url_for('manage_db'))

# ==========================================
# Export / Import Representatives
# ==========================================
@app.route('/api/export-reps')
def export_reps():
    import csv, io
    from flask import Response, session
    if not session.get('db_admin_auth'):
        return redirect(url_for('manage_db_login'))
    reps = Representative.query.order_by(Representative.name).all()
    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(['名稱'])
    for r in reps:
        writer.writerow([r.name])
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment;filename=representatives_export.csv'})

@app.route('/api/import-reps', methods=['POST'])
def import_reps():
    from flask import session
    if not session.get('db_admin_auth'):
        flash('未授權，請先登入', 'error')
        return redirect(url_for('manage_db_login'))
    import csv, io
    file = request.files.get('csv_file')
    if not file or file.filename == '':
        flash('請選擇 CSV 檔案', 'error')
        return redirect(url_for('manage_db'))
    try:
        content = file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(content))
        imported = skipped = 0
        for row in reader:
            name = row.get('名稱', '').strip()
            if not name:
                continue
            if Representative.query.filter_by(name=name).first():
                skipped += 1
            else:
                db.session.add(Representative(name=name))
                imported += 1
        db.session.commit()
        flash(f'✅ 業務代表匯入完成！新增 {imported} 筆，略過重複 {skipped} 筆。', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'匯入失敗：{str(e)}', 'error')
    return redirect(url_for('manage_db'))

# ==========================================
# Export / Import Personnel Data
# ==========================================
@app.route('/api/export-personnel')
def export_personnel():
    import csv, io
    from flask import Response, session
    if not session.get('db_admin_auth'):
        return redirect(url_for('manage_db_login'))
    personnel = Personnel.query.order_by(Personnel.name).all()
    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(['系統代號', '顯示名稱'])
    for p in personnel:
        writer.writerow([p.name, p.display_name or ''])
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment;filename=personnel_export.csv'})

@app.route('/api/import-personnel', methods=['POST'])
def import_personnel():
    from flask import session
    if not session.get('db_admin_auth'):
        flash('未授權，請先登入', 'error')
        return redirect(url_for('manage_db_login'))
    import csv, io
    file = request.files.get('csv_file')
    if not file or file.filename == '':
        flash('請選擇 CSV 檔案', 'error')
        return redirect(url_for('manage_db'))
    mode = request.form.get('import_mode', 'skip')
    try:
        content = file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(content))
        imported = skipped = 0
        for row in reader:
            name         = row.get('系統代號', '').strip()
            display_name = row.get('顯示名稱', '').strip() or None
            if not name:
                continue
            existing = Personnel.query.filter_by(name=name).first()
            if existing:
                if mode == 'overwrite':
                    existing.display_name = display_name
                    imported += 1
                else:
                    skipped += 1
            else:
                db.session.add(Personnel(name=name, display_name=display_name))
                imported += 1
        db.session.commit()
        action_label = '新增/更新' if mode == 'overwrite' else '新增'
        flash(f'✅ 參與人員匯入完成！{action_label} {imported} 筆，略過重複 {skipped} 筆。', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'匯入失敗：{str(e)}', 'error')
    return redirect(url_for('manage_db'))

# ==========================================
# Export / Import Category Data
# ==========================================
@app.route('/api/export-categories')
def export_categories():
    import csv, io
    from flask import Response, session
    if not session.get('db_admin_auth'):
        return redirect(url_for('manage_db_login'))
    categories = Category.query.order_by(Category.name).all()
    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(['種類名稱'])
    for c in categories:
        writer.writerow([c.name])
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment;filename=categories_export.csv'})

@app.route('/api/import-categories', methods=['POST'])
def import_categories():
    from flask import session
    if not session.get('db_admin_auth'):
        flash('未授權，請先登入', 'error')
        return redirect(url_for('manage_db_login'))
    import csv, io
    file = request.files.get('csv_file')
    if not file or file.filename == '':
        flash('請選擇 CSV 檔案', 'error')
        return redirect(url_for('manage_db'))
    try:
        content = file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(content))
        imported = skipped = 0
        for row in reader:
            name = row.get('種類名稱', '').strip()
            if not name:
                continue
            if Category.query.filter_by(name=name).first():
                skipped += 1
            else:
                db.session.add(Category(name=name))
                imported += 1
        db.session.commit()
        flash(f'✅ 專案種類匯入完成！新增 {imported} 筆，略過重複 {skipped} 筆。', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'匯入失敗：{str(e)}', 'error')
    return redirect(url_for('manage_db'))

# -----------------------------------------------------------------------------
# Delete Task: Remove a specific work log entry
# Supports redirecting back to the referring page
# -----------------------------------------------------------------------------
@app.route('/delete-task/<int:id>', methods=['POST'])
def delete_task(id):
    task = Task.query.get_or_404(id)
    redirect_to = request.form.get('redirect_to', url_for('manage_db'))
    try:
        db.session.delete(task)
        db.session.commit()
        flash('✅ 工作紀錄已刪除！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'刪除失敗：{str(e)}', 'error')
    return redirect(redirect_to)

# -----------------------------------------------------------------------------
# Edit Task: Update work log details
# Validates date and work days format
# -----------------------------------------------------------------------------
@app.route('/edit-task/<int:id>', methods=['GET', 'POST'])
def edit_task(id):
    task = Task.query.get_or_404(id)
    redirect_to = request.args.get('redirect_to', url_for('manage_db'))

    if request.method == 'POST':
        task.personnel = request.form.get('personnel')
        task.project_id = int(request.form.get('project_id'))
        date_str = request.form.get('date')
        work_days_str = request.form.get('work_days')
        task.description = request.form.get('description')
        task.notes = request.form.get('notes')
        redirect_to = request.form.get('redirect_to', url_for('manage_db'))

        # Validate Date
        try:
            task.date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
        except ValueError:
            flash('日期格式錯誤', 'error')
            return redirect(url_for('edit_task', id=id, redirect_to=redirect_to))
        
        # Validate Work Days
        try:
            task.work_days = float(work_days_str)
        except (ValueError, TypeError):
            flash('工作天數格式錯誤', 'error')
            return redirect(url_for('edit_task', id=id, redirect_to=redirect_to))

        try:
            db.session.commit()
            flash('✅ 工作紀錄已更新！', 'success')
            return redirect(redirect_to)
        except Exception as e:
            db.session.rollback()
            flash(f'更新失敗：{str(e)}', 'error')

    projects = Project.query.order_by(Project.name).all()
    personnel_list = [p.name for p in Personnel.query.order_by(Personnel.name).all()]
    return render_template('edit_task.html', task=task, projects=projects, personnel_list=personnel_list, redirect_to=redirect_to)

# -----------------------------------------------------------------------------
# Employee Case View: Display all tasks for a selected personnel
# Calculates total work days and project count
# -----------------------------------------------------------------------------
@app.route('/employee-case')
def employee_case():
    personnel_all = Personnel.query.order_by(Personnel.name).all()
    
    if not personnel_all:
        return render_template('employee_case.html',
                               personnel_list=[],
                               selected=None,
                               display_name='',
                               avatar_filename=None,
                               tasks=[],
                               total_days=0,
                               project_count=0)

    personnel_list = [(p.name, p.display_name or p.name) for p in personnel_all]

    selected = request.args.get('person', personnel_list[0][0])
    
    selected_p = Personnel.query.filter_by(name=selected).first()
    if not selected_p and personnel_all:
        selected_p = personnel_all[0]
        selected = selected_p.name
        
    display_name = selected_p.display_name or selected_p.name
    avatar_filename = selected_p.avatar_filename

    # Query tasks and calculate stats
    tasks = Task.query.filter_by(personnel=selected).order_by(Task.date.desc()).all()
    total_days = sum(t.work_days for t in tasks)
    project_count = len(set(t.project_id for t in tasks))

    return render_template('employee_case.html',
                           personnel_list=personnel_list,
                           selected=selected,
                           display_name=display_name,
                           avatar_filename=avatar_filename,
                           tasks=tasks,
                           total_days=total_days,
                           project_count=project_count)

# -----------------------------------------------------------------------------
# Project Timeline: Gantt chart view of all projects
# Calculates dynamic time markers (Month/Quarter/Year) based on range
# Renders project bars and task segments with percentage positioning
# -----------------------------------------------------------------------------
@app.route('/timeline')
def proj_timeline():
    projects = Project.query.order_by(Project.start_date.desc()).all() 
    
    # Calculate default view window (Current month ± 1 month)
    today = date.today()
    if today.month <= 1:
        default_start = date(today.year - 1, 12, 1)
    else:
        default_start = date(today.year, today.month - 1, 1)
    if today.month >= 11:
        default_end = date(today.year + 1, (today.month + 2) - 12, 1)
    else:
        default_end = date(today.year, today.month + 2, 1)

    if not projects:
        timeline_start = default_start
        timeline_end = default_end
    else:
        # Expand range to include all projects if they exceed default window
        proj_start = min(p.start_date for p in projects)
        proj_end = max((p.end_date or p.start_date) for p in projects)
        timeline_start = min(default_start, proj_start)
        timeline_end = max(default_end, proj_end)
        
    total_days = max(1, (timeline_end - timeline_start).days)

    # Calculate percentages for CSS positioning
    default_left_pct = ((default_start - timeline_start).days / total_days) * 100
    default_width_pct = ((default_end - default_start).days / total_days) * 100
    today_pct = ((today - timeline_start).days / total_days) * 100

    # Prepare timeline data structure for rendering
    timeline_data = []
    for p in projects:
        # Calculate project bar position (left % and width %)
        offset_days = (p.start_date - timeline_start).days
        left_percent = max(0, (offset_days / total_days) * 100)
        
        # Determine end date for width calculation
        if p.end_date:
            end_d = p.end_date
        else:
            end_d = max(date.today(), p.start_date + timedelta(days=1))
        
        duration_days = max(1, (end_d - p.start_date).days)
        width_percent = min(100 - left_percent, (duration_days / total_days) * 100)
        
        # Map status to Tailwind CSS color classes
        tag_class = "bg-slate-500"
        if p.status == '進行中':
            tag_class = "bg-amber-700/80"
        elif p.status == '暫緩中':
            tag_class = "bg-blue-600/80"
        elif p.status == '等待中':
            tag_class = "bg-pink-700/80"
        elif p.status == '已結案':
            tag_class = "bg-green-700/80"

        # Calculate task segments within the project bar
        segments = []
        for t in p.tasks:
            if not t.date:
                continue
            
            task_days = max(1, int(t.work_days)) if t.work_days else 1
            task_start = t.date
            task_end = task_start + timedelta(days=task_days)
            
            t_offset_days = (task_start - timeline_start).days
            t_left_percent = max(0, (t_offset_days / total_days) * 100)
            t_duration_days = max(1, (task_end - task_start).days)
            t_width_percent = min(100 - t_left_percent, (t_duration_days / total_days) * 100)
            
            segments.append({
                'left': t_left_percent,
                'width': t_width_percent,
                'personnel': t.personnel,
                'work_days': t.work_days,
                'desc': t.description
            })

        timeline_data.append({
            'proj': p,
            'left': left_percent,
            'width': width_percent,
            'tag_class': tag_class,
            'segments': segments
        })

    # Generate time markers (labels for the timeline axis)
    time_markers = []
    scale = 'month'
    if total_days > 365 * 3:
        scale = 'year'
    elif total_days > 365:
        scale = 'quarter'
        
    current_date = date(timeline_start.year, timeline_start.month, 1)
    if scale == 'year':
        current_date = date(timeline_start.year, 1, 1)
    elif scale == 'quarter':
        quarter_start_month = ((timeline_start.month - 1) // 3) * 3 + 1
        current_date = date(timeline_start.year, quarter_start_month, 1)

    while current_date < timeline_end:
        if scale == 'month':
            marker_label = current_date.strftime('%Y/%m')
            next_month = current_date.month + 1 if current_date.month < 12 else 1
            next_year = current_date.year + 1 if current_date.month == 12 else current_date.year
            next_date = date(next_year, next_month, 1)
        elif scale == 'quarter':
            quarter = (current_date.month - 1) // 3 + 1
            marker_label = f"{current_date.year} Q{quarter}"
            next_month = current_date.month + 3
            next_year = current_date.year
            if next_month > 12:
                next_month -= 12
                next_year += 1
            next_date = date(next_year, next_month, 1)
        else:
            marker_label = str(current_date.year)
            next_date = date(current_date.year + 1, 1, 1)
            
        marker_start = max(current_date, timeline_start)
        marker_end_exclusive = min(next_date, timeline_end)
        
        marker_days = (marker_end_exclusive - marker_start).days
        if marker_days > 0:
            width_percent = (marker_days / total_days) * 100
            time_markers.append({
                'label': marker_label,
                'width_percent': width_percent
            })
            
        current_date = next_date

    return render_template('proj_timeline.html', 
                           projects=projects, 
                           timeline_data=timeline_data,
                           time_markers=time_markers,
                           timeline_start=timeline_start,
                           timeline_end=timeline_end,
                           default_left_pct=default_left_pct,
                           default_width_pct=default_width_pct,
                           today_pct=today_pct)


# -----------------------------------------------------------------------------
# Main Entry Point
# Initializes database tables and seed data if empty
# Starts the Waitress WSGI server on port 5001
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    with app.app_context():
        # Create all database tables
        db.create_all()

        # Initialize default representatives if table is empty
        if not Representative.query.first():
            default_reps = ["Leo/許仁豪", "Polly/林惠文", "Hannah/陳胤琦"]
            for r in default_reps:
                db.session.add(Representative(name=r))
            db.session.commit()
            
        # Initialize default categories if table is empty
        if not Category.query.first():
            default_cats = ["admin", "admin_reform", "project", "testing", "support"]
            for c in default_cats:
                db.session.add(Category(name=c))
            db.session.commit()
            
        # Initialize default personnel if table is empty
        if not Personnel.query.first():
            known_people = [
                {"name": "Jasper", "display_name": "Jasper"},
                {"name": "SeanDu", "display_name": "SeanDu"},
                {"name": "CingYang", "display_name": "Cing Yang"}, 
                {"name": "Alice", "display_name": "Alice"}, 
                {"name": "SeanC", "display_name": "SeanC"}, 
                {"name": "William", "display_name": "William"}
            ]
            
            for p_data in known_people:
                if not Personnel.query.filter_by(name=p_data['name']).first():
                    db.session.add(Personnel(**p_data))
                    
            # Migrate existing personnel from Task table
            personnel_rows = db.session.query(Task.personnel).distinct().all()
            for p in personnel_rows:
                name = p[0]
                if not Personnel.query.filter_by(name=name).first():
                    db.session.add(Personnel(name=name, display_name=name))
                    
            db.session.commit()
        
    print("系統已啟動，請開啟瀏覽器輸入 http://localhost:5001")
    # Use Waitress for production-ready serving
    from waitress import serve
    serve(app, host='0.0.0.0', port=5001)