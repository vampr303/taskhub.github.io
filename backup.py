#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для резервного копирования базы данных и файлов
"""

import os
import shutil
import datetime
import zipfile
from pathlib import Path

def create_backup():
    """Создает резервную копию базы данных и файлов"""

    # Создаем папку для бэкапов
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)

    # Генерируем имя файла с timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}"
    backup_path = backup_dir / backup_name

    print(f"Создание резервной копии: {backup_name}")

    try:
        with zipfile.ZipFile(f"{backup_path}.zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Добавляем базу данных
            if os.path.exists("instance/task_manager.db"):
                zipf.write("instance/task_manager.db", "database/task_manager.db")
                print("✓ База данных добавлена")

            # Добавляем файлы uploads
            if os.path.exists("uploads"):
                for root, dirs, files in os.walk("uploads"):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_path = os.path.join("uploads", os.path.relpath(file_path, "uploads"))
                        zipf.write(file_path, arc_path)
                print("✓ Файлы добавлены")

        # Удаляем старые бэкапы (оставляем последние 10)
        backups = sorted(backup_dir.glob("*.zip"), reverse=True)
        if len(backups) > 10:
            for old_backup in backups[10:]:
                old_backup.unlink()
                print(f"✓ Старый бэкап удален: {old_backup.name}")

        print(f"✅ Резервная копия создана: {backup_path}.zip")
        return True

    except Exception as e:
        print(f"❌ Ошибка при создании бэкапа: {e}")
        return False

def restore_backup(backup_file):
    """Восстанавливает данные из резервной копии"""

    if not os.path.exists(backup_file):
        print(f"❌ Файл бэкапа не найден: {backup_file}")
        return False

    try:
        with zipfile.ZipFile(backup_file, 'r') as zipf:
            # Восстанавливаем базу данных
            if "database/task_manager.db" in zipf.namelist():
                # Создаем папку instance
                os.makedirs("instance", exist_ok=True)
                zipf.extract("database/task_manager.db", "instance/")
                os.rename("instance/database/task_manager.db", "instance/task_manager.db")
                print("✓ База данных восстановлена")

            # Восстанавливаем файлы
            for file_info in zipf.filelist:
                if file_info.filename.startswith("uploads/"):
                    zipf.extract(file_info.filename, ".")
                    print(f"✓ Файл восстановлен: {file_info.filename}")

        print("✅ Данные восстановлены из бэкапа")
        return True

    except Exception as e:
        print(f"❌ Ошибка при восстановлении: {e}")
        return False

def list_backups():
    """Показывает список доступных бэкапов"""

    backup_dir = Path("backups")
    if not backup_dir.exists():
        print("Папка backups не существует")
        return

    backups = sorted(backup_dir.glob("*.zip"), reverse=True)
    if not backups:
        print("Бэкапы не найдены")
        return

    print("Доступные бэкапы:")
    for i, backup in enumerate(backups, 1):
        size_mb = backup.stat().st_size / (1024 * 1024)
        print(".1f")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Использование:")
        print("  python backup.py create          - создать бэкап")
        print("  python backup.py list            - список бэкапов")
        print("  python backup.py restore <file>  - восстановить из бэкапа")
        sys.exit(1)

    command = sys.argv[1]

    if command == "create":
        create_backup()
    elif command == "list":
        list_backups()
    elif command == "restore":
        if len(sys.argv) < 3:
            print("Укажите файл бэкапа: python backup.py restore <backup_file.zip>")
            sys.exit(1)
        restore_backup(sys.argv[2])
    else:
        print(f"Неизвестная команда: {command}")