# Развертывание системы управления заданиями

## 🚀 Варианты развертывания

### 1. VPS сервер (Рекомендуется) ⭐⭐⭐⭐⭐

#### DigitalOcean Droplet
```bash
# 1. Создайте аккаунт на DigitalOcean
# 2. Создайте Droplet с Ubuntu 22.04 ($6/месяц)
# 3. Подключитесь по SSH

# Установите Docker и Docker Compose
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker

# Клонируйте проект (или загрузите файлы)
git clone https://github.com/your-repo/task-manager.git
cd task-manager

# Запустите приложение
docker-compose up -d

# Настройте Nginx (опционально)
sudo apt install nginx
sudo nano /etc/nginx/sites-available/task-manager
```

Nginx конфиг:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/task-manager /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

#### Преимущества:
- Полный контроль
- Неограниченное хранилище
- Масштабируемость
- Стоимость от $5/месяц

---

### 2. Railway (Простой и быстрый) ⭐⭐⭐⭐

#### Шаги:
1. **Регистрация:** https://railway.app
2. **Создайте проект:** "New Project" → "Deploy from GitHub"
3. **Подключите GitHub:** Авторизуйтесь и выберите репозиторий
4. **Настройки:**
   - **Root Directory:** `/` (корневая папка)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python app.py`
5. **Переменные окружения:**
   ```
   FLASK_APP=app.py
   FLASK_ENV=production
   SECRET_KEY=your-super-secret-key
   ```
6. **Deploy**

#### Преимущества:
- Бесплатный тариф (512MB RAM, 1GB storage)
- Автоматическое развертывание
- PostgreSQL база данных
- Простота использования

---

### 3. Render (Бесплатный с ограничениями) ⭐⭐⭐

#### Шаги:
1. **Регистрация:** https://render.com
2. **Создайте сервис:** "New" → "Web Service"
3. **Подключите GitHub:** Выберите репозиторий
4. **Настройки:**
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python app.py`
5. **Переменные окружения:**
   ```
   FLASK_APP=app.py
   FLASK_ENV=production
   SECRET_KEY=your-secret-key
   ```
6. **Deploy**

#### Преимущества:
- 750 часов бесплатного использования в месяц
- Автоматическое SSL
- Простой интерфейс

---

### 4. Heroku (Классика) ⭐⭐⭐

#### Шаги:
1. **Установите Heroku CLI:**
```bash
# Скачайте с https://devcenter.heroku.com/articles/heroku-cli
```

2. **Подготовьте приложение:**
```bash
# Создайте Procfile
echo "web: python app.py" > Procfile

# Создайте runtime.txt
echo "python-3.11.6" > runtime.txt
```

3. **Разверните:**
```bash
heroku create your-app-name
heroku config:set FLASK_APP=app.py
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=your-secret-key
git push heroku main
```

#### Преимущества:
- Надежная платформа
- Легко масштабировать
- PostgreSQL addon

---

## 🔧 Настройка для продакшена

### 1. Измените настройки в `config.py`:
```python
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'change-this-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///task_manager.db'

    # Для больших файлов используйте облачное хранилище
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
```

### 2. Используйте PostgreSQL вместо SQLite:
```bash
# На Railway/Render/Heroku PostgreSQL создается автоматически
# На VPS установите PostgreSQL:
sudo apt install postgresql postgresql-contrib
```

### 3. Настройте переменные окружения:
```bash
export FLASK_APP=app.py
export FLASK_ENV=production
export SECRET_KEY=your-super-secure-secret-key
export DATABASE_URL=postgresql://user:password@localhost/dbname
```

### 4. Запуск с Gunicorn (для продакшена):
```bash
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 app:app
```

---

## 📁 Управление файлами

### Для больших объемов используйте облачное хранилище:

#### AWS S3:
```python
import boto3

s3 = boto3.client('s3',
    aws_access_key_id=os.environ['AWS_ACCESS_KEY'],
    aws_secret_access_key=os.environ['AWS_SECRET_KEY']
)

# Загрузка файла
s3.upload_fileobj(file, 'your-bucket', filename)

# Скачивание файла
s3.download_file('your-bucket', filename, local_path)
```

#### Google Cloud Storage:
```python
from google.cloud import storage

client = storage.Client()
bucket = client.bucket('your-bucket')

# Загрузка
blob = bucket.blob(filename)
blob.upload_from_file(file)

# Скачивание
blob.download_to_file(local_file)
```

---

## 🔒 Безопасность

### 1. Измените SECRET_KEY:
```bash
# Сгенерируйте новый ключ
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Настройте HTTPS (важно!):
- Railway/Render/Heroku: Автоматически
- VPS: Используйте Let's Encrypt

### 3. Ограничьте загрузку файлов:
```python
# В config.py
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'pdf'}  # Только нужные форматы
```

---

## 💰 Стоимость

| Сервис | Бесплатно | Платно от |
|--------|-----------|-----------|
| Railway | 512MB RAM, 1GB storage | $5/месяц |
| Render | 750 часов/месяц | $7/месяц |
| DigitalOcean | - | $6/месяц |
| Heroku | - | $7/месяц |
| Vultr | - | $2.5/месяц |

---

## 🚀 Быстрый старт с Docker

```bash
# Локально
docker-compose up -d

# На сервере
docker build -t task-manager .
docker run -d -p 5000:5000 -v $(pwd)/uploads:/app/uploads task-manager
```

---

## 📞 Поддержка

Если возникнут проблемы:
1. Проверьте логи: `docker logs container_name`
2. Проверьте переменные окружения
3. Убедитесь, что порт 5000 открыт
4. Проверьте права доступа к папке uploads

**Рекомендую начать с Railway или DigitalOcean для простоты и надежности!** 🎉