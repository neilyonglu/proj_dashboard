from datetime import datetime

from flask import render_template, request, redirect, url_for, flash
from ..extensions import db
from ..models import Project, Representative, Category


def register(app):

    @app.route('/add-project', methods=['GET', 'POST'])
    def add_proj():
        if request.method == 'POST':
            name = request.form.get('name')
            status = request.form.get('status')
            category = request.form.get('category')
            rep = request.form.get('rep')
            equipment = request.form.get('equipment')
            description = request.form.get('description')
            notes = request.form.get('notes')
            start_date_str = request.form.get('start_date')
            end_date_str = request.form.get('end_date')

            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
            except ValueError:
                flash('日期格式錯誤', 'error')
                return redirect(url_for('add_proj'))

            if not name or not status or not category or not rep or not start_date:
                flash('請填寫所有必填欄位', 'error')
                return redirect(url_for('add_proj'))

            new_project = Project(name=name, status=status, category=category, rep=rep,
                                  equipment=equipment, description=description,
                                  start_date=start_date, end_date=end_date, notes=notes)
            try:
                db.session.add(new_project)
                if rep and not Representative.query.filter_by(name=rep).first():
                    db.session.add(Representative(name=rep))
                if category and not Category.query.filter_by(name=category).first():
                    db.session.add(Category(name=category))
                db.session.commit()
                flash('✅ 專案已新增！', 'success')
                return redirect(url_for('proj_timeline'))
            except Exception as e:
                db.session.rollback()
                flash(f'發生錯誤：{str(e)}', 'error')

        reps = Representative.query.order_by(Representative.name).all()
        categories = Category.query.order_by(Category.name).all()
        return render_template('add_proj.html', reps=reps, categories=categories)

    @app.route('/edit-project/<int:id>', methods=['GET', 'POST'])
    def edit_project(id):
        project = Project.query.get_or_404(id)
        if request.method == 'POST':
            project.name = request.form.get('name')
            project.status = request.form.get('status')
            project.category = request.form.get('category')
            project.rep = request.form.get('rep')
            project.equipment = request.form.get('equipment')
            project.description = request.form.get('description')
            project.notes = request.form.get('notes')
            start_date_str = request.form.get('start_date')
            end_date_str = request.form.get('end_date')

            try:
                project.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
                project.end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
            except ValueError:
                flash('日期格式錯誤', 'error')
                return redirect(url_for('edit_project', id=id))

            try:
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
