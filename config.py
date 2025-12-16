import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///./task_manager.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Папка для загружаемых файлов
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB максимальный размер файла
    
    # Разрешенные расширения файлов
    ALLOWED_EXTENSIONS = {
        # Изображения
        'png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg', 'tiff', 'tif', 'webp', 'ico',
        # Видео
        'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', 'm4v', '3gp', 'mpg', 'mpeg',
        # Аудио
        'mp3', 'wav', 'flac', 'aac', 'ogg', 'wma',
        # Документы
        'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt', 'xls', 'xlsx', 'csv', 'ppt', 'pptx',
        # Архивы
        'zip', 'rar', '7z', 'tar', 'gz',
        # 3D файлы
        'stl', 'obj', '3ds', 'blend', 'ply', 'dae', 'fbx', 'gltf', 'glb',
        # Другие
        'json', 'xml', 'html', 'css', 'js', 'py', 'cpp', 'c', 'java'
    }