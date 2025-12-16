#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# Добавляем текущую папку в Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, User, init_db

def init_database():
    """Инициализация базы данных"""
    with app.app_context():
        print("Создание таблиц базы данных...")
        db.create_all()
        
        print("Создание админ пользователя...")
        admin = User.query.filter_by(username='Tural Jafarov').first()
        if not admin:
            admin = User(
                username='Tural Jafarov',
                email='admin@company.com',
                full_name='Tural Jafarov',
                is_admin=True
            )
            admin.set_password('Riza0707756600..')
            db.session.add(admin)
            db.session.commit()
            print("✅ Админ пользователь создан: Tural Jafarov")
        else:
            print("ℹ️ Админ пользователь уже существует")
        
        print("✅ База данных инициализирована успешно!")

if __name__ == '__main__':
    init_database()