import os
import sys

from flask import Flask

# ── Path detection (works for both Python script and PyInstaller bundle) ──────
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

os.chdir(application_path)

# ── Load .env manually ────────────────────────────────────────────────────────
env_path = os.path.join(application_path, '.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ[k.strip()] = v.strip()

# ── Flask app setup ───────────────────────────────────────────────────────────
instance_dir = os.path.join(application_path, 'instance')
os.makedirs(instance_dir, exist_ok=True)
db_file_path = os.path.join(instance_dir, 'app.db')

upload_path = os.path.join(application_path, 'static', 'avatars')
os.makedirs(upload_path, exist_ok=True)

app = Flask(__name__,
            template_folder=os.path.join(application_path, 'templates'),
            static_folder=os.path.join(application_path, 'static'))

app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_file_path.replace('\\', '/')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = upload_path
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
app.config['DB_FILE_PATH'] = db_file_path
app.config['DB_INSTANCE_DIR'] = instance_dir
app.config['DB_ADMIN_PASSWORD'] = os.environ.get('DB_ADMIN_PASSWORD', 'admin123')

from core.extensions import db
db.init_app(app)

APP_VERSION = '1.3.1'
app.config['APP_VERSION'] = APP_VERSION
app.config['APPLICATION_PATH'] = application_path

@app.context_processor
def inject_app_version():
    return {'app_version': APP_VERSION}

# ── Register all routes ───────────────────────────────────────────────────────
from core.routes import register_routes
register_routes(app)

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    from core.helpers import backup_database, ensure_task_columns, ensure_personnel_columns, start_daily_backup_scheduler
    from core.models import Representative, Category, Personnel, Task

    with app.app_context():
        backup_database(reason='startup', once_per_day=True)
        db.create_all()
        ensure_task_columns()
        ensure_personnel_columns()

        if not Representative.query.first():
            for name in ["Leo/許仁豪", "Polly/林惠文", "Hannah/陳胤琦"]:
                db.session.add(Representative(name=name))
            db.session.commit()

        if not Category.query.first():
            for name in ["admin", "admin_reform", "project", "testing", "support"]:
                db.session.add(Category(name=name))
            db.session.commit()

        if not Personnel.query.first():
            for p in [
                {"name": "Jasper", "display_name": "Jasper"},
                {"name": "SeanDu", "display_name": "SeanDu"},
                {"name": "CingYang", "display_name": "Cing Yang"},
                {"name": "Alice", "display_name": "Alice"},
                {"name": "SeanC", "display_name": "SeanC"},
                {"name": "William", "display_name": "William"},
            ]:
                if not Personnel.query.filter_by(name=p['name']).first():
                    db.session.add(Personnel(**p))
            for (name,) in db.session.query(Task.personnel).distinct().all():
                if not Personnel.query.filter_by(name=name).first():
                    db.session.add(Personnel(name=name, display_name=name))
            db.session.commit()

    start_daily_backup_scheduler(app)

    print("系統已啟動，請開啟瀏覽器輸入 http://localhost:5001")
    from waitress import serve
    serve(app, host='0.0.0.0', port=5001)
