#ngrok

import sys
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QLineEdit, QLabel,
                           QTableWidget, QTableWidgetItem, QGroupBox,
                           QTextEdit, QMessageBox, QFormLayout, QDialog,
                           QDialogButtonBox, QDateEdit)
from PyQt5.QtCore import Qt


class ScoreTrackerDB:
    def __init__(self, db_name="score_tracker.db"):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                score INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deleted_users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                score INTEGER DEFAULT 0,
                deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                original_created_at TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_user(self, username, score=0):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, score) VALUES (?, ?)",
                (username, score)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_all_users(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.id, u.username, u.score, 
                   COUNT(p.id) as posts_count,
                   GROUP_CONCAT(p.title, '; ') as post_titles
            FROM users u
            LEFT JOIN posts p ON u.id = p.user_id
            GROUP BY u.id, u.username, u.score
            ORDER BY u.score DESC
        ''')
        users = cursor.fetchall()
        conn.close()
        return users
    
    def update_user_score(self, user_id, new_score):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET score = ? WHERE id = ?",
            (new_score, user_id)
        )
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0
    
    def add_post(self, user_id, title, content=""):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO posts (user_id, title, content) VALUES (?, ?, ?)",
            (user_id, title, content)
        )
        conn.commit()
        conn.close()
    
    def get_user_posts(self, user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title, content, created_at FROM posts WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        posts = cursor.fetchall()
        conn.close()
        return posts
    
    def delete_user(self, user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0
    
    def delete_post(self, post_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0
    
    def update_post(self, post_id, title, content):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE posts SET title = ?, content = ? WHERE id = ?",
            (title, content, post_id)
        )
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0
    
    def move_user_to_deleted(self, user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT username, score, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        user_data = cursor.fetchone()
        
        if not user_data:
            conn.close()
            return False
        
        username, score, created_at = user_data
        
        cursor.execute(
            "INSERT INTO deleted_users (id, username, score, original_created_at) VALUES (?, ?, ?, ?)",
            (user_id, username, score, created_at)
        )
        
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0
    
    def get_deleted_users(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, score, deleted_at, original_created_at
            FROM deleted_users
            ORDER BY deleted_at DESC
        ''')
        users = cursor.fetchall()
        conn.close()
        return users
    
    def restore_user(self, user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT username FROM deleted_users WHERE id = ?", (user_id,))
        deleted_user = cursor.fetchone()
        
        if not deleted_user:
            conn.close()
            return False
        
        username = deleted_user[0]
        
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return False
        
        cursor.execute(
            "SELECT score, original_created_at FROM deleted_users WHERE id = ?",
            (user_id,)
        )
        user_data = cursor.fetchone()
        
        if not user_data:
            conn.close()
            return False
        
        score, original_created_at = user_data
        
        cursor.execute(
            "INSERT INTO users (id, username, score, created_at) VALUES (?, ?, ?, ?)",
            (user_id, username, score, original_created_at)
        )
        
        cursor.execute("DELETE FROM deleted_users WHERE id = ?", (user_id,))
        
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0
    
    def permanently_delete_user(self, user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM deleted_users WHERE id = ?", (user_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0


class ScoreDescriptionDialog(QDialog):
    def __init__(self, username, score, parent=None):
        super().__init__(parent)
        self.username = username
        self.score = score
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle(f"Описание добавления баллов - {self.username}")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        info_label = QLabel(f"Пользователь: {self.username}\nДобавляемые баллы: {self.score}")
        info_label.setStyleSheet("font-weight: bold; padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(info_label)
        
        form_layout = QFormLayout()
        
        self.date_input = QDateEdit()
        self.date_input.setDate(datetime.now().date())
        self.date_input.setEnabled(False)
        form_layout.addRow("Дата:", self.date_input)
        
        self.reason_input = QTextEdit()
        self.reason_input.setPlaceholderText("Опишите, за что были добавлены баллы...")
        self.reason_input.setMaximumHeight(80)
        form_layout.addRow("За что были добавлены баллы:", self.reason_input)
        
        self.added_by_input = QLineEdit()
        self.added_by_input.setPlaceholderText("Кто добавил баллы")
        form_layout.addRow("Кто добавил баллы:", self.added_by_input)
        
        self.score_display = QLabel(str(self.score))
        self.score_display.setStyleSheet("font-weight: bold; color: green;")
        form_layout.addRow("Сколько баллов добавлено:", self.score_display)
        
        layout.addLayout(form_layout)
        
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            self
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_description_data(self):
        return {
            'date': self.date_input.date().toString('yyyy-MM-dd'),
            'reason': self.reason_input.toPlainText().strip(),
            'added_by': self.added_by_input.text().strip(),
            'score': self.score
        }


class DeletedUsersWindow(QMainWindow):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.refresh_deleted_users_table()
    
    def init_ui(self):
        self.setWindowTitle("Удаленные пользователи")
        self.setGeometry(200, 200, 700, 500)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        title_label = QLabel("История удаленных пользователей")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title_label)
        
        table_group = QGroupBox("Удаленные пользователи")
        table_layout = QVBoxLayout(table_group)
        
        self.deleted_users_table = QTableWidget()
        self.deleted_users_table.setColumnCount(5)
        self.deleted_users_table.setHorizontalHeaderLabels([
            "ID", "Имя пользователя", "Очки", "Дата удаления", "Дата создания"
        ])
        self.deleted_users_table.horizontalHeader().setStretchLastSection(True)
        
        buttons_layout = QHBoxLayout()
        self.restore_btn = QPushButton("Восстановить")
        self.restore_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        self.permanent_delete_btn = QPushButton("Удалить навсегда")
        self.permanent_delete_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        self.refresh_btn = QPushButton("Обновить")
        
        buttons_layout.addWidget(self.restore_btn)
        buttons_layout.addWidget(self.permanent_delete_btn)
        buttons_layout.addWidget(self.refresh_btn)
        
        table_layout.addWidget(self.deleted_users_table)
        table_layout.addLayout(buttons_layout)
        
        layout.addWidget(table_group)
        
        self.restore_btn.clicked.connect(self.restore_user)
        self.permanent_delete_btn.clicked.connect(self.permanent_delete_user)
        self.refresh_btn.clicked.connect(self.refresh_deleted_users_table)
        
        self.deleted_users_table.setSelectionBehavior(QTableWidget.SelectRows)
    
    def refresh_deleted_users_table(self):
        users = self.db.get_deleted_users()
        self.deleted_users_table.setRowCount(len(users))
        
        for row, user in enumerate(users):
            user_id, username, score, deleted_at, original_created_at = user
            
            self.deleted_users_table.setItem(row, 0, QTableWidgetItem(str(user_id)))
            self.deleted_users_table.setItem(row, 1, QTableWidgetItem(username))
            self.deleted_users_table.setItem(row, 2, QTableWidgetItem(str(score)))
            self.deleted_users_table.setItem(row, 3, QTableWidgetItem(deleted_at))
            self.deleted_users_table.setItem(row, 4, QTableWidgetItem(original_created_at or "Неизвестно"))
        
        self.deleted_users_table.resizeColumnsToContents()
    
    def restore_user(self):
        current_row = self.deleted_users_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя для восстановления!")
            return
        
        user_id_item = self.deleted_users_table.item(current_row, 0)
        username_item = self.deleted_users_table.item(current_row, 1)
        
        if not user_id_item or not username_item:
            return
        
        user_id = int(user_id_item.text())
        username = username_item.text()
        
        reply = QMessageBox.question(
            self,
            "Подтверждение восстановления",
            f"Вы уверены, что хотите восстановить пользователя '{username}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.db.restore_user(user_id):
                QMessageBox.information(self, "Успех", f"Пользователь '{username}' восстановлен!")
                self.refresh_deleted_users_table()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось восстановить пользователя! Возможно, пользователь с таким именем уже существует.")
    
    def permanent_delete_user(self):
        current_row = self.deleted_users_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя для полного удаления!")
            return
        
        user_id_item = self.deleted_users_table.item(current_row, 0)
        username_item = self.deleted_users_table.item(current_row, 1)
        
        if not user_id_item or not username_item:
            return
        
        user_id = int(user_id_item.text())
        username = username_item.text()
        
        reply = QMessageBox.warning(
            self,
            "ОПАСНО! Полное удаление",
            f"Вы уверены, что хотите НАВСЕГДА удалить пользователя '{username}'?\n"
            f"Это действие нельзя отменить!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.db.permanently_delete_user(user_id):
                QMessageBox.information(self, "Успех", f"Пользователь '{username}' полностью удален!")
                self.refresh_deleted_users_table()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить пользователя!")


class ScoreTrackerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = ScoreTrackerDB()
        self.init_ui()
        self.refresh_users_table()
    
    def init_ui(self):
        self.setWindowTitle("Мини Трекер Очков")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        add_group = QGroupBox("Добавить пользователя")
        add_layout = QFormLayout(add_group)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Введите имя пользователя")
        self.score_input = QLineEdit()
        self.score_input.setPlaceholderText("0")
        self.score_input.setText("0")
        self.score_input.textChanged.connect(self.update_button_states)
        
        add_layout.addRow("Имя пользователя:", self.username_input)
        add_layout.addRow("Очки:", self.score_input)
        
        add_button_layout = QHBoxLayout()
        self.add_user_btn = QPushButton("Добавить пользователя")
        self.add_description_btn = QPushButton("Добавить описание")
        self.add_description_btn.setEnabled(False)
        self.add_post_btn = QPushButton("Добавить пост")
        add_button_layout.addWidget(self.add_user_btn)
        add_button_layout.addWidget(self.add_description_btn)
        add_button_layout.addWidget(self.add_post_btn)
        
        add_layout.addRow(add_button_layout)
        
        update_group = QGroupBox("Обновить очки пользователя")
        update_layout = QFormLayout(update_group)
        
        self.update_id_input = QLineEdit()
        self.update_id_input.setPlaceholderText("ID пользователя")
        self.update_score_input = QLineEdit()
        self.update_score_input.setPlaceholderText("Новые очки")
        
        self.update_score_btn = QPushButton("Обновить очки")
        
        update_layout.addRow("ID пользователя:", self.update_id_input)
        update_layout.addRow("Новые очки:", self.update_score_input)
        update_layout.addRow(self.update_score_btn)
        
        table_group = QGroupBox("Список пользователей")
        table_layout = QVBoxLayout(table_group)
        
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels([
            "ID", "Имя пользователя", "Очки", "Кол-во постов", "Заголовки постов"
        ])
        self.users_table.horizontalHeader().setStretchLastSection(True)
        
        refresh_btn = QPushButton("Обновить список")
        self.delete_user_btn = QPushButton("Удалить пользователя")
        self.delete_user_btn.setStyleSheet("QPushButton { background-color: #ff4444; color: white; }")
        
        table_buttons_layout = QHBoxLayout()
        table_buttons_layout.addWidget(refresh_btn)
        table_buttons_layout.addWidget(self.delete_user_btn)
        
        self.deleted_users_btn = QPushButton("Удаленные пользователи")
        self.deleted_users_btn.setStyleSheet("QPushButton { background-color: #ff9800; color: white; }")
        table_buttons_layout.addWidget(self.deleted_users_btn)
        
        table_layout.addWidget(self.users_table)
        table_layout.addLayout(table_buttons_layout)
        
        posts_group = QGroupBox("Посты пользователя")
        posts_layout = QVBoxLayout(posts_group)
        
        self.posts_display = QTextEdit()
        self.posts_display.setReadOnly(True)
        self.posts_display.setText("Выберите пользователя для просмотра постов.")
        
        posts_buttons_layout = QHBoxLayout()
        self.edit_post_btn = QPushButton("Редактировать пост")
        self.delete_post_btn = QPushButton("Удалить пост")
        self.delete_post_btn.setStyleSheet("QPushButton { background-color: #ff4444; color: white; }")
        self.edit_post_btn.setEnabled(False)
        self.delete_post_btn.setEnabled(False)
        posts_buttons_layout.addWidget(self.edit_post_btn)
        posts_buttons_layout.addWidget(self.delete_post_btn)
        
        posts_layout.addWidget(self.posts_display)
        posts_layout.addLayout(posts_buttons_layout)
        
        layout.addWidget(add_group)
        layout.addWidget(update_group)
        layout.addWidget(table_group)
        layout.addWidget(posts_group)
        
        self.add_user_btn.clicked.connect(self.add_user)
        self.add_description_btn.clicked.connect(self.add_score_description)
        self.update_score_btn.clicked.connect(self.update_score)
        self.add_post_btn.clicked.connect(self.add_post)
        refresh_btn.clicked.connect(self.refresh_users_table)
        self.delete_user_btn.clicked.connect(self.delete_user)
        self.deleted_users_btn.clicked.connect(self.open_deleted_users_window)
        self.edit_post_btn.clicked.connect(self.edit_post)
        self.delete_post_btn.clicked.connect(self.delete_post)
        self.users_table.itemSelectionChanged.connect(self.on_user_selection_changed)
        self.posts_display.cursorPositionChanged.connect(self.on_post_cursor_changed)
        
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        self.selected_post_id = None
        
        self.deleted_window = None
    
    def add_user(self):
        username = self.username_input.text().strip()
        try:
            score = int(self.score_input.text()) if self.score_input.text().strip() else 0
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Очки должны быть числом!")
            return
        
        if not username:
            QMessageBox.warning(self, "Ошибка", "Введите имя пользователя!")
            return
        
        if self.db.add_user(username, score):
            QMessageBox.information(self, "Успех", "Пользователь добавлен!")
            self.username_input.clear()
            self.score_input.setText("0")
            self.refresh_users_table()
        else:
            QMessageBox.warning(self, "Ошибка", "Пользователь с таким именем уже существует!")
    
    def update_score(self):
        try:
            user_id = int(self.update_id_input.text())
            new_score = int(self.update_score_input.text())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "ID и очки должны быть числами!")
            return
        
        if self.db.update_user_score(user_id, new_score):
            QMessageBox.information(self, "Успех", "Очки обновлены!")
            self.update_id_input.clear()
            self.update_score_input.clear()
            self.refresh_users_table()
        else:
            QMessageBox.warning(self, "Ошибка", "Пользователь с таким ID не найден!")
    
    def add_post(self):
        username = self.username_input.text().strip()
        if not username:
            QMessageBox.warning(self, "Ошибка", "Введите имя пользователя для добавления поста!")
            return
        
        conn = sqlite3.connect(self.db.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            QMessageBox.warning(self, "Ошибка", "Пользователь не найден!")
            return
        
        user_id = result[0]
        title = f"Пост от {username}"
        content = f"Содержание поста для {username}"
        
        self.db.add_post(user_id, title, content)
        QMessageBox.information(self, "Успех", "Пост добавлен!")
        self.refresh_users_table()
    
    def refresh_users_table(self):
        users = self.db.get_all_users()
        self.users_table.setRowCount(len(users))
        
        for row, user in enumerate(users):
            user_id, username, score, posts_count, post_titles = user
            
            self.users_table.setItem(row, 0, QTableWidgetItem(str(user_id)))
            self.users_table.setItem(row, 1, QTableWidgetItem(username))
            self.users_table.setItem(row, 2, QTableWidgetItem(str(score)))
            self.users_table.setItem(row, 3, QTableWidgetItem(str(posts_count)))
            
            if post_titles and len(post_titles) > 50:
                post_titles = post_titles[:47] + "..."
            self.users_table.setItem(row, 4, QTableWidgetItem(post_titles or "Нет постов"))
        
        self.users_table.resizeColumnsToContents()
    
    def on_user_selection_changed(self):
        current_row = self.users_table.currentRow()
        if current_row >= 0:
            user_id_item = self.users_table.item(current_row, 0)
            if user_id_item:
                user_id = int(user_id_item.text())
                self.display_user_posts(user_id)
    
    def display_user_posts(self, user_id):
        posts = self.db.get_user_posts(user_id)
        
        if not posts:
            self.posts_display.setText("У этого пользователя нет постов.")
            return
        
        posts_text = f"Посты пользователя ID {user_id}:\n\n"
        for i, (post_id, title, content, created_at) in enumerate(posts, 1):
            posts_text += f"[ID: {post_id}] {i}. {title}\n"
            posts_text += f"   Содержание: {content}\n"
            posts_text += f"   Дата: {created_at}\n"
            posts_text += f"   (Кликните на этот текст для выбора поста)\n\n"
        
        self.posts_display.setText(posts_text)
        self.selected_post_id = None
        self.update_post_buttons_state()
    
    def on_post_cursor_changed(self):
        cursor = self.posts_display.textCursor()
        cursor.select(cursor.LineUnderCursor)
        selected_text = cursor.selectedText()
        
        import re
        match = re.search(r'\[ID: (\d+)\]', selected_text)
        if match:
            self.selected_post_id = int(match.group(1))
            self.update_post_buttons_state()
        else:
            self.selected_post_id = None
            self.update_post_buttons_state()
    
    def update_post_buttons_state(self):
        has_post = self.selected_post_id is not None
        self.edit_post_btn.setEnabled(has_post)
        self.delete_post_btn.setEnabled(has_post)
    
    def update_button_states(self):
        score_text = self.score_input.text().strip()
        try:
            score = int(score_text) if score_text else 0
            self.add_description_btn.setEnabled(score > 0)
        except ValueError:
            self.add_description_btn.setEnabled(False)
    
    def add_score_description(self):
        username = self.username_input.text().strip()
        try:
            score = int(self.score_input.text()) if self.score_input.text().strip() else 0
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Очки должны быть числом!")
            return
        
        if not username:
            QMessageBox.warning(self, "Ошибка", "Введите имя пользователя!")
            return
        
        if score <= 0:
            QMessageBox.warning(self, "Ошибка", "Очки должны быть больше нуля!")
            return
        
        dialog = ScoreDescriptionDialog(username, score, self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_description_data()
            
            if self.db.add_user(username, score):
                conn = sqlite3.connect(self.db.db_name)
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    user_id = result[0]
                    title = f"Добавление баллов: {data['reason'][:30]}..."
                    content = f"""Дата: {data['date']}
За что: {data['reason']}
Кто добавил: {data['added_by']}
Количество: {data['score']} баллов"""
                    
                    self.db.add_post(user_id, title, content)
                    QMessageBox.information(self, "Успех", "Пользователь и описание добавлены!")
                    self.username_input.clear()
                    self.score_input.setText("0")
                    self.refresh_users_table()
            else:
                QMessageBox.warning(self, "Ошибка", "Пользователь с таким именем уже существует!")
    
    def delete_user(self):
        current_row = self.users_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя для удаления!")
            return
        
        user_id_item = self.users_table.item(current_row, 0)
        username_item = self.users_table.item(current_row, 1)
        
        if not user_id_item or not username_item:
            return
        
        user_id = int(user_id_item.text())
        username = username_item.text()
        
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить пользователя '{username}'?\n"
            f"Пользователь будет перенесен в архив удаленных.\n"
            f"Все связанные посты также будут удалены!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.db.move_user_to_deleted(user_id):
                QMessageBox.information(self, "Успех", f"Пользователь '{username}' перенесен в архив удаленных!")
                self.refresh_users_table()
                self.posts_display.setText("Выберите пользователя для просмотра постов.")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить пользователя!")
    
    def open_deleted_users_window(self):
        if self.deleted_window is None or not self.deleted_window.isVisible():
            self.deleted_window = DeletedUsersWindow(self.db, self)
            self.deleted_window.show()
        else:
            self.deleted_window.raise_()
            self.deleted_window.activateWindow()
    
    def edit_post(self):
        if not self.selected_post_id:
            QMessageBox.warning(self, "Ошибка", "Выберите пост для редактирования!")
            return
        
        posts = self.db.get_user_posts(self.get_selected_user_id())
        current_post = None
        for post in posts:
            if post[0] == self.selected_post_id:
                current_post = post
                break
        
        if not current_post:
            QMessageBox.warning(self, "Ошибка", "Пост не найден!")
            return
        
        from PyQt5.QtWidgets import QInputDialog
        
        new_title, ok = QInputDialog.getText(
            self, "Редактировать пост",
            "Заголовок:",
            text=current_post[1]
        )
        
        if ok and new_title.strip():
            new_content, ok = QInputDialog.getText(
                self, "Редактировать пост",
                "Содержание:",
                text=current_post[2]
            )
            
            if ok:
                if self.db.update_post(self.selected_post_id, new_title.strip(), new_content.strip()):
                    QMessageBox.information(self, "Успех", "Пост обновлен!")
                    self.refresh_users_table()
                    self.display_user_posts(self.get_selected_user_id())
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось обновить пост!")
    
    def delete_post(self):
        if not self.selected_post_id:
            QMessageBox.warning(self, "Ошибка", "Выберите пост для удаления!")
            return
        
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            "Вы уверены, что хотите удалить этот пост?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.db.delete_post(self.selected_post_id):
                QMessageBox.information(self, "Успех", "Пост удален!")
                self.refresh_users_table()
                self.display_user_posts(self.get_selected_user_id())
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить пост!")
    
    def get_selected_user_id(self):
        current_row = self.users_table.currentRow()
        if current_row >= 0:
            user_id_item = self.users_table.item(current_row, 0)
            if user_id_item:
                return int(user_id_item.text())
        return None


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)
    
    window = ScoreTrackerApp()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()