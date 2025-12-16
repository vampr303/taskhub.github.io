from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import os
import uuid
from datetime import datetime

from config import Config
from models import db, User, Task, File, Comment, init_db
from forms import LoginForm, RegistrationForm, TaskForm, CommentForm

def get_mimetype(filename):
    """Определение mimetype по расширению файла"""
    import mimetypes
    mimetype, _ = mimetypes.guess_type(filename)
    return mimetype or 'application/octet-stream'

app = Flask(__name__, template_folder='.')
app.config.from_object(Config)

# Инициализация расширений
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Создание папки для загрузок
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    print(f"Папка загрузок создана: {app.config['UPLOAD_FOLDER']}")
except Exception as e:
    print(f"Ошибка создания папки загрузок: {e}")

# Главная страница
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('employee_dashboard'))
    return redirect(url_for('login'))

# Авторизация
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('index')
            return redirect(next_page)
        else:
            flash('Неверный логин или пароль', 'error')
    
    return render_template('login.html', form=form)

# Регистрация (только для админа)
@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if not current_user.is_admin:
        flash('У вас нет прав для регистрации пользователей', 'error')
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            is_admin=form.is_admin.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Пользователь успешно зарегистрирован!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('register.html', form=form)

# Выход
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Панель администратора
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('У вас нет доступа к админ панели', 'error')
        return redirect(url_for('index'))
    
    users = User.query.filter_by(is_admin=False).all()
    tasks = Task.query.all()
    
    # Подсчет общей суммы оплаты
    total_payment = sum([task.payment_amount for task in tasks if task.payment_amount])
    
    # Подсчет оплаченных заданий
    paid_tasks = sum([1 for task in tasks if task.is_paid])
    
    return render_template('admin_dashboard.html', 
                         users=users, 
                         tasks=tasks, 
                         total_payment=total_payment,
                         paid_tasks=paid_tasks)

# Создание задания
@app.route('/admin/task/create', methods=['GET', 'POST'])
@login_required
def create_task():
    if not current_user.is_admin:
        flash('У вас нет прав для создания заданий', 'error')
        return redirect(url_for('index'))
    
    form = TaskForm()
    # Заполняем список пользователей для назначения
    form.assigned_to.choices = [(u.id, u.full_name) for u in User.query.filter_by(is_admin=False).all()]
    form.assigned_to.choices.insert(0, (0, 'Общее задание (для всех)'))
    
    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            description=form.description.data,
            task_type=form.task_type.data,
            payment_amount=form.payment_amount.data if form.payment_amount.data else None,
            assigned_to=None if form.assigned_to.data == 0 else form.assigned_to.data,
            created_by=current_user.id
        )
        db.session.add(task)
        db.session.commit()
        flash('Задание успешно создано!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('create_task.html', form=form)

# Панель работника
@app.route('/employee')
@login_required
def employee_dashboard():
    if current_user.is_admin:
        flash('Администраторы не могут использовать панель работника', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Личные задания
    personal_tasks = Task.query.filter_by(assigned_to=current_user.id, task_type='personal').all()
    
    # Общие задания
    general_tasks = Task.query.filter_by(task_type='general').all()
    
    return render_template('employee_dashboard.html', 
                         personal_tasks=personal_tasks, 
                         general_tasks=general_tasks)

# Просмотр задания
@app.route('/task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def view_task(task_id):
    task = Task.query.get_or_404(task_id)
    form = CommentForm()
    
    # Проверяем доступ к заданию
    has_access = False
    if current_user.is_admin:
        has_access = True
    elif task.task_type == 'general':
        has_access = True
    elif task.assigned_to == current_user.id:
        has_access = True
    
    if not has_access:
        flash('У вас нет доступа к этому заданию', 'error')
        return redirect(url_for('employee_dashboard'))
    
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            task_id=task.id,
            user_id=current_user.id
        )
        db.session.add(comment)
        db.session.commit()
        flash('Комментарий добавлен!', 'success')
        return redirect(url_for('view_task', task_id=task.id))
    
    comments = Comment.query.filter_by(task_id=task.id).order_by(Comment.created_at).all()
    files = File.query.filter_by(task_id=task.id).order_by(File.uploaded_at.desc()).all()
    
    return render_template('view_task.html', 
                         task=task, 
                         form=form, 
                         comments=comments, 
                         files=files)

# Загрузка файла
@app.route('/task/<int:task_id>/upload', methods=['POST'])
@login_required
def upload_file(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Проверяем доступ к заданию
    has_access = False
    if current_user.is_admin:
        has_access = True
    elif task.task_type == 'general':
        has_access = True
    elif task.assigned_to == current_user.id:
        has_access = True
    
    if not has_access:
        flash('У вас нет доступа к этому заданию', 'error')
        return redirect(url_for('employee_dashboard'))
    
    if 'file' not in request.files:
        flash('Файл не выбран', 'error')
        return redirect(url_for('view_task', task_id=task_id))
    
    file = request.files['file']
    if file.filename == '':
        flash('Файл не выбран', 'error')
        return redirect(url_for('view_task', task_id=task_id))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Генерируем уникальное имя файла
        file_extension = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        
        # Создаем папку для задания если её нет
        task_folder = os.path.join(app.config['UPLOAD_FOLDER'], f'task_{task_id}')
        os.makedirs(task_folder, exist_ok=True)
        
        file_path = os.path.join(task_folder, unique_filename)
        file.save(file_path)
        
        # Сохраняем информацию о файле в базу данных
        mime_type = file.content_type or get_mimetype(filename)
        file_record = File(
            filename=unique_filename,
            original_filename=filename,
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            mime_type=mime_type,
            task_id=task_id,
            uploaded_by=current_user.id
        )
        db.session.add(file_record)
        db.session.commit()
        
        flash('Файл успешно загружен!', 'success')
    else:
        flash('Неподдерживаемый формат файла', 'error')
    
    return redirect(url_for('view_task', task_id=task_id))

# Скачивание файла
@app.route('/file/<int:file_id>/download')
@login_required
def download_file(file_id):
    file_record = File.query.get_or_404(file_id)
    task = file_record.task
    
    # Проверяем доступ к файлу
    has_access = False
    if current_user.is_admin:
        has_access = True
    elif task.task_type == 'general':
        has_access = True
    elif task.assigned_to == current_user.id:
        has_access = True
    
    if not has_access:
        flash('У вас нет доступа к этому файлу', 'error')
        return redirect(url_for('employee_dashboard'))
    
    from flask import current_app
    import os
    
    # Проверяем, существует ли файл
    if not os.path.exists(file_record.file_path):
        flash('Файл не найден', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Получаем правильный mimetype
    mimetype = file_record.mime_type or get_mimetype(file_record.original_filename)
    
    return send_file(
        file_record.file_path,
        as_attachment=True,
        download_name=file_record.original_filename,
        mimetype=mimetype,
        max_age=0
    )

# Обновление статуса оплаты
@app.route('/admin/task/<int:task_id>/payment', methods=['POST'])
@login_required
def update_payment_status(task_id):
    if not current_user.is_admin:
        flash('У вас нет прав для обновления статуса оплаты', 'error')
        return redirect(url_for('index'))
    
    task = Task.query.get_or_404(task_id)
    payment_status = request.form.get('is_paid')
    task.is_paid = bool(payment_status)
    db.session.commit()
    
    flash('Статус оплаты обновлен!', 'success')
    return redirect(url_for('admin_dashboard'))

# Просмотр профиля работника (для админа)
@app.route('/admin/user/<int:user_id>')
@login_required
def view_employee_profile(user_id):
    if not current_user.is_admin:
        flash('У вас нет доступа к этой странице', 'error')
        return redirect(url_for('index'))

    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Нельзя просматривать профиль администратора', 'error')
        return redirect(url_for('admin_dashboard'))

    # Получаем задания работника
    personal_tasks = Task.query.filter_by(assigned_to=user_id, task_type='personal').all()
    general_tasks = Task.query.filter_by(task_type='general').all()

    return render_template('employee_profile.html',
                         employee=user,
                         personal_tasks=personal_tasks,
                         general_tasks=general_tasks)

# Редактирование данных работника
@app.route('/admin/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_employee(user_id):
    if not current_user.is_admin:
        flash('У вас нет прав для редактирования пользователей', 'error')
        return redirect(url_for('index'))

    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Нельзя редактировать администратора', 'error')
        return redirect(url_for('admin_dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        # Проверяем, не занят ли новый логин другим пользователем
        if form.username.data != user.username:
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user:
                flash('Пользователь с таким логином уже существует', 'error')
                return redirect(url_for('edit_employee', user_id=user_id))

        # Проверяем, не занят ли новый email другим пользователем
        if form.email.data != user.email:
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('Пользователь с таким email уже существует', 'error')
                return redirect(url_for('edit_employee', user_id=user_id))

        user.username = form.username.data
        user.email = form.email.data
        user.full_name = form.full_name.data

        if form.password.data:
            user.set_password(form.password.data)

        db.session.commit()
        flash('Данные работника обновлены!', 'success')
        return redirect(url_for('view_employee_profile', user_id=user_id))

    # Заполняем форму текущими данными
    form.username.data = user.username
    form.email.data = user.email
    form.full_name.data = user.full_name

    return render_template('edit_employee.html', form=form, employee=user)

# Удаление пользователя
@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('У вас нет прав для удаления пользователей', 'error')
        return redirect(url_for('index'))

    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Нельзя удалить администратора', 'error')
        return redirect(url_for('admin_dashboard'))

    # Удаляем связанные данные
    for task in user.assigned_tasks:
        task.assigned_to = None
    for file in user.uploaded_files:
        db.session.delete(file)
    for comment in user.comments:
        db.session.delete(comment)

    db.session.delete(user)
    db.session.commit()

    flash('Пользователь удален!', 'success')
    return redirect(url_for('admin_dashboard'))

# Редактирование задания
@app.route('/admin/task/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    if not current_user.is_admin:
        flash('У вас нет прав для редактирования заданий', 'error')
        return redirect(url_for('index'))

    task = Task.query.get_or_404(task_id)
    form = TaskForm()

    # Заполняем список пользователей для назначения
    form.assigned_to.choices = [(u.id, u.full_name) for u in User.query.filter_by(is_admin=False).all()]
    form.assigned_to.choices.insert(0, (0, 'Общее задание (для всех)'))

    if form.validate_on_submit():
        task.title = form.title.data
        task.description = form.description.data
        task.task_type = form.task_type.data
        task.payment_amount = form.payment_amount.data if form.payment_amount.data else None
        task.assigned_to = None if form.assigned_to.data == 0 else form.assigned_to.data

        db.session.commit()
        flash('Задание успешно обновлено!', 'success')
        return redirect(url_for('view_employee_profile', user_id=task.assigned_to) if task.assigned_to else url_for('admin_dashboard'))

    # Заполняем форму текущими данными
    form.title.data = task.title
    form.description.data = task.description
    form.task_type.data = task.task_type
    form.payment_amount.data = task.payment_amount
    form.assigned_to.data = task.assigned_to or 0

    return render_template('edit_task.html', form=form, task=task)

# Удаление задания
@app.route('/admin/task/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    if not current_user.is_admin:
        flash('У вас нет прав для удаления заданий', 'error')
        return redirect(url_for('index'))

    task = Task.query.get_or_404(task_id)

    # Удаляем связанные файлы
    for file in task.files:
        if os.path.exists(file.file_path):
            os.remove(file.file_path)

    db.session.delete(task)
    db.session.commit()

    flash('Задание удалено!', 'success')
    return redirect(url_for('admin_dashboard'))

def allowed_file(filename):
    if not filename or '.' not in filename:
        return False
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in app.config['ALLOWED_EXTENSIONS']

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)