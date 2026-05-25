import sqlite3
import hashlib
import re
import time
import tkinter as tk
from tkinter import messagebox, ttk

# ==================== РАБОТА С БАЗОЙ ДАННЫХ ====================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE,
            password_hash TEXT,
            email TEXT,
            phone TEXT,
            role_id INTEGER,
            FOREIGN KEY (role_id) REFERENCES roles(id)
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            destination TEXT,
            price INTEGER,
            days INTEGER,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS hotels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            city TEXT,
            stars INTEGER,
            price_per_night INTEGER,
            tour_id INTEGER,
            FOREIGN KEY (tour_id) REFERENCES tours(id) ON DELETE CASCADE
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            tour_id INTEGER,
            hotel_id INTEGER,
            booking_date TEXT,
            nights INTEGER,
            total_price INTEGER,
            status TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (tour_id) REFERENCES tours(id),
            FOREIGN KEY (hotel_id) REFERENCES hotels(id)
        )
    ''')
    
    cur.execute("INSERT OR IGNORE INTO roles (id, name) VALUES (1, 'admin')")
    cur.execute("INSERT OR IGNORE INTO roles (id, name) VALUES (2, 'user')")
    
    # Тестовый админ
    admin_pass = hash_password("Admin123!")
    cur.execute('''
        INSERT OR IGNORE INTO users (login, password_hash, email, phone, role_id)
        VALUES (?, ?, ?, ?, ?)
    ''', ("admin", admin_pass, "admin@travel.com", "000000", 1))
    
    # Добавим тестовые туры
    cur.execute("SELECT COUNT(*) FROM tours")
    if cur.fetchone()[0] == 0:
        tours = [
            ("Парижское приключение", "Франция", 50000, 7, 1),
            ("Римские каникулы", "Италия", 45000, 6, 1),
            ("Турецкий рай", "Турция", 30000, 5, 1),
        ]
        cur.executemany("INSERT INTO tours (title, destination, price, days, created_by) VALUES (?, ?, ?, ?, ?)", tours)
        
        # Добавим тестовые отели
        hotels = [
            ("Отель Эйфель", "Париж", 5, 15000, 1),
            ("Отель Колизей", "Рим", 4, 12000, 2),
            ("Отель Анталия", "Анталия", 5, 8000, 3),
        ]
        cur.executemany("INSERT INTO hotels (name, city, stars, price_per_night, tour_id) VALUES (?, ?, ?, ?, ?)", hotels)
    
    conn.commit()
    conn.close()

# ==================== ФУНКЦИИ ДЛЯ ТУРОВ ====================

def get_tours():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT id, title, destination, price, days FROM tours")
    tours = cur.fetchall()
    conn.close()
    return tours

def get_tour_by_id(tour_id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT id, title, destination, price, days FROM tours WHERE id=?", (tour_id,))
    tour = cur.fetchone()
    conn.close()
    return tour

def add_tour(title, destination, price, days, user_id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO tours (title, destination, price, days, created_by)
        VALUES (?, ?, ?, ?, ?)
    ''', (title, destination, price, days, user_id))
    conn.commit()
    conn.close()

def update_tour(tour_id, title, destination, price, days):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('''
        UPDATE tours SET title=?, destination=?, price=?, days=?
        WHERE id=?
    ''', (title, destination, price, days, tour_id))
    conn.commit()
    conn.close()

def delete_tour(tour_id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM bookings WHERE tour_id=?", (tour_id,))
    cur.execute("DELETE FROM hotels WHERE tour_id=?", (tour_id,))
    cur.execute("DELETE FROM tours WHERE id=?", (tour_id,))
    conn.commit()
    conn.close()

def search_tours(query):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('''
        SELECT id, title, destination, price, days FROM tours
        WHERE title LIKE ? OR destination LIKE ?
    ''', (f'%{query}%', f'%{query}%'))
    tours = cur.fetchall()
    conn.close()
    return tours

# ==================== ФУНКЦИИ ДЛЯ ОТЕЛЕЙ ====================

def get_hotels(tour_id=None):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    if tour_id:
        cur.execute('''
            SELECT hotels.id, hotels.name, hotels.city, hotels.stars, hotels.price_per_night, tours.title
            FROM hotels JOIN tours ON hotels.tour_id = tours.id
            WHERE hotels.tour_id=?
        ''', (tour_id,))
    else:
        cur.execute('''
            SELECT hotels.id, hotels.name, hotels.city, hotels.stars, hotels.price_per_night, tours.title
            FROM hotels JOIN tours ON hotels.tour_id = tours.id
        ''')
    hotels = cur.fetchall()
    conn.close()
    return hotels

def get_hotel_by_id(hotel_id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT id, name, city, stars, price_per_night, tour_id FROM hotels WHERE id=?", (hotel_id,))
    hotel = cur.fetchone()
    conn.close()
    return hotel

def add_hotel(name, city, stars, price_per_night, tour_id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO hotels (name, city, stars, price_per_night, tour_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, city, stars, price_per_night, tour_id))
    conn.commit()
    conn.close()

def update_hotel(hotel_id, name, city, stars, price_per_night, tour_id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('''
        UPDATE hotels SET name=?, city=?, stars=?, price_per_night=?, tour_id=?
        WHERE id=?
    ''', (name, city, stars, price_per_night, tour_id, hotel_id))
    conn.commit()
    conn.close()

def delete_hotel(hotel_id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM bookings WHERE hotel_id=?", (hotel_id,))
    cur.execute("DELETE FROM hotels WHERE id=?", (hotel_id,))
    conn.commit()
    conn.close()

def search_hotels(query):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('''
        SELECT hotels.id, hotels.name, hotels.city, hotels.stars, hotels.price_per_night, tours.title
        FROM hotels JOIN tours ON hotels.tour_id = tours.id
        WHERE hotels.name LIKE ? OR hotels.city LIKE ?
    ''', (f'%{query}%', f'%{query}%'))
    hotels = cur.fetchall()
    conn.close()
    return hotels

# ==================== ФУНКЦИИ ДЛЯ БРОНИРОВАНИЙ ====================

def get_bookings(user_id=None):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    if user_id:
        cur.execute('''
            SELECT bookings.id, tours.title, hotels.name, bookings.booking_date, bookings.nights, 
                   bookings.total_price, bookings.status, tours.id, hotels.id
            FROM bookings 
            JOIN tours ON bookings.tour_id = tours.id
            JOIN hotels ON bookings.hotel_id = hotels.id
            WHERE bookings.user_id=?
        ''', (user_id,))
    else:
        cur.execute('''
            SELECT bookings.id, tours.title, hotels.name, bookings.booking_date, bookings.nights, 
                   bookings.total_price, bookings.status, users.login, tours.id, hotels.id
            FROM bookings 
            JOIN tours ON bookings.tour_id = tours.id
            JOIN hotels ON bookings.hotel_id = hotels.id
            JOIN users ON bookings.user_id = users.id
        ''')
    bookings = cur.fetchall()
    conn.close()
    return bookings

def get_booking_by_id(booking_id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('''
        SELECT id, user_id, tour_id, hotel_id, booking_date, nights, total_price, status
        FROM bookings WHERE id=?
    ''', (booking_id,))
    booking = cur.fetchone()
    conn.close()
    return booking

def add_booking(user_id, tour_id, hotel_id, nights, total_price):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    booking_date = time.strftime("%Y-%m-%d %H:%M:%S")
    cur.execute('''
        INSERT INTO bookings (user_id, tour_id, hotel_id, booking_date, nights, total_price, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, tour_id, hotel_id, booking_date, nights, total_price, "подтверждено"))
    conn.commit()
    conn.close()

def update_booking(booking_id, status):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("UPDATE bookings SET status=? WHERE id=?", (status, booking_id))
    conn.commit()
    conn.close()

def delete_booking(booking_id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM bookings WHERE id=?", (booking_id,))
    conn.commit()
    conn.close()

def get_tours_count():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM tours")
    count = cur.fetchone()[0]
    conn.close()
    return count

def get_bookings_count_for_user(user_id=None):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    if user_id:
        cur.execute("SELECT COUNT(*) FROM bookings WHERE user_id=?", (user_id,))
    else:
        cur.execute("SELECT COUNT(*) FROM bookings")
    count = cur.fetchone()[0]
    conn.close()
    return count

def get_hotels_count():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM hotels")
    count = cur.fetchone()[0]
    conn.close()
    return count

def get_user_by_login(login):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('''
        SELECT users.id, users.login, users.password_hash, users.email, users.phone, roles.name
        FROM users JOIN roles ON users.role_id = roles.id
        WHERE users.login = ?
    ''', (login,))
    user = cur.fetchone()
    conn.close()
    return user

def register_user(login, password, email, phone):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    try:
        cur.execute('''
            INSERT INTO users (login, password_hash, email, phone, role_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (login, hash_password(password), email, phone, 2))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def validate_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(pattern, email):
        return False
    if '@' not in email:
        return False
    local, domain = email.split('@', 1)
    if re.search(r'admin', domain, re.IGNORECASE):
        return False
    return True

def validate_password(password):
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True

def validate_string(value, min_len=3):
    return value and len(value.strip()) >= min_len

def validate_number(value):
    try:
        return int(value) > 0
    except ValueError:
        return False

# ==================== КЛАСС ДЛЯ ФОРМЫ ВВОДА ====================

class EntityForm:
    def __init__(self, parent, title, fields, on_save, entity_id=None, values=None):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("400x500")
        self.window.transient(parent)
        self.window.grab_set()
        
        self.fields = fields
        self.on_save = on_save
        self.entity_id = entity_id
        self.entries = {}
        
        for i, (label, field_type) in enumerate(fields):
            tk.Label(self.window, text=label + ":").pack(pady=5)
            entry = tk.Entry(self.window, width=30)
            entry.pack()
            if values and i < len(values):
                entry.insert(0, str(values[i]))
            self.entries[label] = (entry, field_type)
        
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Сохранить", command=self.save, bg="green", fg="white", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Отмена", command=self.window.destroy, bg="gray", fg="white", width=15).pack(side=tk.LEFT, padx=5)
    
    def save(self):
        data = {}
        for label, (entry, field_type) in self.entries.items():
            value = entry.get().strip()
            
            if not value:
                messagebox.showerror("Ошибка", f"Поле '{label}' не может быть пустым")
                return
            
            if field_type == 'number':
                try:
                    value = int(value)
                    if value <= 0:
                        messagebox.showerror("Ошибка", f"Поле '{label}' должно быть положительным числом")
                        return
                except ValueError:
                    messagebox.showerror("Ошибка", f"Поле '{label}' должно быть числом")
                    return
            elif field_type == 'string' and len(value) < 3:
                messagebox.showerror("Ошибка", f"Поле '{label}' должно содержать минимум 3 символа")
                return
            
            data[label] = value
        
        self.on_save(self.entity_id, data)
        self.window.destroy()

# ==================== КЛАСС ДЛЯ ТАБЛИЦЫ С CRUD ====================

class CRUDTable:
    def __init__(self, parent, title, columns, get_data_func, add_func, update_func, delete_func, 
                 search_func=None, form_fields=None, user_role='admin'):
        self.parent = parent
        self.title = title
        self.columns = columns
        self.get_data_func = get_data_func
        self.add_func = add_func
        self.update_func = update_func
        self.delete_func = delete_func
        self.search_func = search_func
        self.form_fields = form_fields
        self.user_role = user_role
        self.current_data = []
        
        frame = tk.LabelFrame(parent, text=title, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Поиск
        if search_func and user_role == 'admin':
            search_frame = tk.Frame(frame)
            search_frame.pack(fill=tk.X, pady=5)
            tk.Label(search_frame, text="🔍 Поиск:").pack(side=tk.LEFT)
            self.search_entry = tk.Entry(search_frame, width=30)
            self.search_entry.pack(side=tk.LEFT, padx=5)
            tk.Button(search_frame, text="Искать", command=self.search).pack(side=tk.LEFT)
            tk.Button(search_frame, text="Сброс", command=self.load_data).pack(side=tk.LEFT, padx=5)
        
        # Таблица
        table_frame = tk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scroll_y = tk.Scrollbar(table_frame, orient=tk.VERTICAL)
        scroll_x = tk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', 
                                  yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        scroll_y.grid(row=0, column=1, sticky='ns')
        scroll_x.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Кнопки CRUD
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=10)
        
        if user_role == 'admin':
            tk.Button(btn_frame, text="➕ Добавить", command=self.add, bg="green", fg="white", width=12).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text="✏️ Редактировать", command=self.edit, bg="orange", width=12).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text="🗑️ Удалить", command=self.delete, bg="red", fg="white", width=12).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text="🔄 Обновить", command=self.load_data, width=12).pack(side=tk.LEFT, padx=5)
        
        self.load_data()
    
    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.current_data = self.get_data_func()
        for row in self.current_data:
            self.tree.insert('', tk.END, values=row[:-1] if len(row) > len(self.columns) else row)
    
    def search(self):
        query = self.search_entry.get()
        if query:
            results = self.search_func(query)
            for item in self.tree.get_children():
                self.tree.delete(item)
            for row in results:
                self.tree.insert('', tk.END, values=row[:-1] if len(row) > len(self.columns) else row)
        else:
            self.load_data()
    
    def get_selected_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите запись")
            return None
        index = self.tree.index(selected[0])
        return self.current_data[index][0]
    
    def add(self):
        EntityForm(self.parent, f"Добавление {self.title}", self.form_fields, 
                   lambda id, data: self.save_callback(None, data, self.add_func))
    
    def edit(self):
        entity_id = self.get_selected_id()
        if not entity_id:
            return
        
        # Получаем текущие значения
        if hasattr(self, 'get_entity_by_id'):
            entity = self.get_entity_by_id(entity_id)
            if entity:
                values = entity[1:len(self.form_fields)+1]
                EntityForm(self.parent, f"Редактирование {self.title}", self.form_fields,
                          lambda id, data: self.save_callback(entity_id, data, self.update_func),
                          entity_id, values)
    
    def delete(self):
        entity_id = self.get_selected_id()
        if not entity_id:
            return
        
        # Получаем название записи для сообщения
        record_name = ""
        for row in self.current_data:
            if row[0] == entity_id:
                record_name = row[1] if len(row) > 1 else f"№{entity_id}"
                break
        
        if messagebox.askyesno("Подтверждение удаления", 
                               f"Вы действительно хотите удалить запись «{record_name}» (№{entity_id})?\n\n"
                               f"⚠️ Это действие нельзя отменить"):
            self.delete_func(entity_id)
            messagebox.showinfo("Успех", "Запись удалена")
            self.load_data()
    
    def save_callback(self, entity_id, data, func):
        if entity_id:
            func(entity_id, *[data[label] for label, _ in self.form_fields])
        else:
            func(*[data[label] for label, _ in self.form_fields])
        self.load_data()

# ==================== ОКНО РЕГИСТРАЦИИ ====================

class RegisterWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Регистрация")
        self.window.geometry("400x500")
        self.window.transient(parent)
        self.window.grab_set()
        
        tk.Label(self.window, text="Регистрация нового пользователя", font=("Arial", 14)).pack(pady=10)
        
        tk.Label(self.window, text="Логин:").pack(pady=5)
        self.login_entry = tk.Entry(self.window)
        self.login_entry.pack()
        
        tk.Label(self.window, text="Пароль:").pack(pady=5)
        self.pass_entry = tk.Entry(self.window, show="*")
        self.pass_entry.pack()
        
        tk.Label(self.window, text="Подтверждение пароля:").pack(pady=5)
        self.pass2_entry = tk.Entry(self.window, show="*")
        self.pass2_entry.pack()
        
        tk.Label(self.window, text="Email:").pack(pady=5)
        self.email_entry = tk.Entry(self.window)
        self.email_entry.pack()
        
        tk.Label(self.window, text="Телефон:").pack(pady=5)
        self.phone_entry = tk.Entry(self.window)
        self.phone_entry.pack()
        
        tk.Button(self.window, text="Зарегистрироваться", command=self.register, bg="green", fg="white").pack(pady=20)
        
    def register(self):
        login = self.login_entry.get()
        pwd = self.pass_entry.get()
        pwd2 = self.pass2_entry.get()
        email = self.email_entry.get()
        phone = self.phone_entry.get()
        
        if not all([login, pwd, email, phone]):
            messagebox.showerror("Ошибка", "Заполните все поля")
            return
        if pwd != pwd2:
            messagebox.showerror("Ошибка", "Пароли не совпадают")
            return
        if not validate_password(pwd):
            messagebox.showerror("Ошибка", "Пароль: мин 8 символов, заглавная буква, цифра, спецсимвол")
            return
        if not validate_email(email):
            messagebox.showerror("Ошибка", "Неверный email (не должен содержать 'admin' после @)")
            return
        if register_user(login, pwd, email, phone):
            messagebox.showinfo("Успех", "Регистрация пройдена! Теперь войдите.")
            self.window.destroy()
        else:
            messagebox.showerror("Ошибка", "Логин уже существует")

# ==================== ОКНО АВТОРИЗАЦИИ ====================

class AuthWindow:
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.failed_attempts = 0
        self.blocked_until = 0
        
        self.root.title("Авторизация - Туристический агент")
        self.root.geometry("400x350")
        
        tk.Label(root, text="🏖️ Туристический агент", font=("Arial", 16)).pack(pady=10)
        
        tk.Label(root, text="Логин:").pack(pady=5)
        self.entry_login = tk.Entry(root, width=30)
        self.entry_login.pack()
        
        tk.Label(root, text="Пароль:").pack(pady=5)
        self.entry_password = tk.Entry(root, show="*", width=30)
        self.entry_password.pack()
        
        tk.Button(root, text="Войти", command=self.login, bg="blue", fg="white", width=20).pack(pady=10)
        tk.Button(root, text="Регистрация", command=self.open_register, width=20).pack()
        
    def login(self):
        if time.time() < self.blocked_until:
            messagebox.showerror("Ошибка", f"Блокировка до {time.strftime('%H:%M:%S', time.localtime(self.blocked_until))}")
            return
            
        login = self.entry_login.get()
        password = self.entry_password.get()
        user = get_user_by_login(login)
        
        if user and user[2] == hash_password(password):
            self.on_login_success(user)
        else:
            self.failed_attempts += 1
            remaining = 3 - self.failed_attempts
            if self.failed_attempts >= 3:
                self.blocked_until = time.time() + 30
                self.failed_attempts = 0
                messagebox.showerror("Ошибка", "3 неверные попытки! Блокировка 30 секунд")
            else:
                messagebox.showerror("Ошибка", f"Неверный логин/пароль. Осталось попыток: {remaining}")
    
    def open_register(self):
        RegisterWindow(self.root)

# ==================== ОСНОВНОЕ ОКНО С ВКЛАДКАМИ ====================

class MainApp:
    def __init__(self, root, user_data):
        self.root = root
        self.user_id = user_data[0]
        self.user_login = user_data[1]
        self.user_role = user_data[5]
        
        self.root.title(f"Туристический агент - {self.user_login}")
        self.root.geometry("1200x700")
        
        # Верхняя панель
        top_frame = tk.Frame(root, bg="lightblue")
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(top_frame, text=f"✨ Добро пожаловать, {self.user_login}!", 
                font=("Arial", 16), bg="lightblue").pack(side=tk.LEFT, padx=10)
        
        role_text = "👑 Администратор" if self.user_role == 'admin' else "👤 Пользователь"
        tk.Label(top_frame, text=role_text, font=("Arial", 12), bg="lightblue").pack(side=tk.LEFT, padx=20)
        
        tk.Button(top_frame, text="🚪 Выйти", command=self.logout, bg="red", fg="white").pack(side=tk.RIGHT, padx=10)
        
        # Статистика
        stats_frame = tk.LabelFrame(root, text="📊 Статистика", padx=10, pady=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.stats_label = tk.Label(stats_frame, text="", font=("Arial", 11))
        self.stats_label.pack()
        self.update_stats()
        
        # Вкладки с CRUD
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        if self.user_role == 'admin':
            self.init_admin_tabs()
        else:
            self.init_user_tabs()
    
    def update_stats(self):
        tours_count = get_tours_count()
        hotels_count = get_hotels_count()
        bookings_count = get_bookings_count_for_user()
        
        if self.user_role == 'admin':
            text = f"🏝️ Туров: {tours_count}   |   🏨 Отелей: {hotels_count}   |   📋 Бронирований: {bookings_count}"
        else:
            my_bookings = get_bookings_count_for_user(self.user_id)
            text = f"🏝️ Доступно туров: {tours_count}   |   🏨 Отелей: {hotels_count}   |   📋 Моих бронирований: {my_bookings}"
        
        self.stats_label.config(text=text)
    
    def init_admin_tabs(self):
        # Тур: Туры
        tours_tab = ttk.Frame(self.notebook)
        self.notebook.add(tours_tab, text="🏝️ Туры")
        
        CRUDTable(tours_tab, "Управление турами",
                  columns=["ID", "Название", "Страна", "Цена", "Дней"],
                  get_data_func=get_tours,
                  add_func=lambda title, dest, price, days: add_tour(title, dest, price, days, self.user_id),
                  update_func=update_tour,
                  delete_func=delete_tour,
                  search_func=search_tours,
                  form_fields=[("Название", "string"), ("Страна", "string"), 
                              ("Цена", "number"), ("Дней", "number")],
                  user_role=self.user_role)
        
        # Вкладка: Отели
        hotels_tab = ttk.Frame(self.notebook)
        self.notebook.add(hotels_tab, text="🏨 Отели")
        
        class HotelsCRUD:
            def get_hotels_data():
                return get_hotels()
            
            def add_hotel_wrapper(name, city, stars, price_per_night, tour_id):
                add_hotel(name, city, stars, price_per_night, tour_id)
            
            def update_hotel_wrapper(id, name, city, stars, price_per_night, tour_id):
                update_hotel(id, name, city, stars, price_per_night, tour_id)
            
            def get_hotel_by_id(id):
                return get_hotel_by_id(id)
        
        # Создаём CRUD для отелей вручную из-за tour_id
        self.create_hotels_tab(hotels_tab)
        
        # Вкладка: Бронирования
        bookings_tab = ttk.Frame(self.notebook)
        self.notebook.add(bookings_tab, text="📋 Бронирования")
        
        CRUDTable(bookings_tab, "Управление бронированиями",
                  columns=["ID", "Тур", "Отель", "Дата", "Ночей", "Цена", "Статус", "Пользователь"],
                  get_data_func=lambda: get_bookings(),
                  add_func=None,  # Бронирования добавляются отдельно
                  update_func=lambda id, status: update_booking(id, status),
                  delete_func=delete_booking,
                  form_fields=[("Статус", "string")],
                  user_role=self.user_role)
        
        # Добавляем методы для отельного CRUD
        setattr(CRUDTable, 'get_entity_by_id', None)
    
    def create_hotels_tab(self, parent):
        frame = tk.LabelFrame(parent, text="Управление отелями", padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ["ID", "Название", "Город", "Звёзд", "Цена/ночь", "Тур"]
        tree = ttk.Treeview(frame, columns=columns, show='headings')
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        scroll_y = tk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        scroll_x = tk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        tree.grid(row=0, column=0, sticky='nsew')
        scroll_y.grid(row=0, column=1, sticky='ns')
        scroll_x.grid(row=1, column=0, sticky='ew')
        
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        def load_hotels():
            for item in tree.get_children():
                tree.delete(item)
            hotels = get_hotels()
            for hotel in hotels:
                tree.insert('', tk.END, values=(hotel[0], hotel[1], hotel[2], hotel[3], hotel[4], hotel[5]))
        
        def add_hotel_dialog():
            tours = get_tours()
            tour_names = {t[1]: t[0] for t in tours}
            
            dialog = tk.Toplevel(parent)
            dialog.title("Добавить отель")
            dialog.geometry("400x400")
            
            entries = {}
            fields = ["Название", "Город", "Звёзд", "Цена за ночь", "Тур"]
            for i, field in enumerate(fields):
                tk.Label(dialog, text=field + ":").pack(pady=5)
                if field == "Тур":
                    entry = ttk.Combobox(dialog, values=list(tour_names.keys()), width=27)
                else:
                    entry = tk.Entry(dialog, width=30)
                entry.pack()
                entries[field] = entry
            
            def save():
                try:
                    name = entries["Название"].get().strip()
                    city = entries["Город"].get().strip()
                    stars = int(entries["Звёзд"].get())
                    price = int(entries["Цена за ночь"].get())
                    tour_title = entries["Тур"].get()
                    tour_id = tour_names.get(tour_title)
                    
                    if not all([name, city, stars, price, tour_id]):
                        messagebox.showerror("Ошибка", "Заполните все поля")
                        return
                    if len(name) < 3 or len(city) < 3:
                        messagebox.showerror("Ошибка", "Название и город должны быть не менее 3 символов")
                        return
                    if stars < 1 or stars > 5:
                        messagebox.showerror("Ошибка", "Звёзд от 1 до 5")
                        return
                    if price <= 0:
                        messagebox.showerror("Ошибка", "Цена должна быть положительной")
                        return
                    
                    add_hotel(name, city, stars, price, tour_id)
                    messagebox.showinfo("Успех", "Отель добавлен")
                    dialog.destroy()
                    load_hotels()
                    self.update_stats()
                except ValueError:
                    messagebox.showerror("Ошибка", "Звёзд и цена должны быть числами")
            
            tk.Button(dialog, text="Сохранить", command=save, bg="green", fg="white").pack(pady=20)
        
        def edit_hotel():
            selected = tree.selection()
            if not selected:
                messagebox.showerror("Ошибка", "Выберите отель")
                return
            
            values = tree.item(selected[0])['values']
            hotel_id = values[0]
            hotel = get_hotel_by_id(hotel_id)
            if not hotel:
                return
            
            tours = get_tours()
            tour_names = {t[1]: t[0] for t in tours}
            current_tour = None
            for name, tid in tour_names.items():
                if tid == hotel[5]:
                    current_tour = name
                    break
            
            dialog = tk.Toplevel(parent)
            dialog.title("Редактировать отель")
            dialog.geometry("400x400")
            
            entries = {}
            fields = ["Название", "Город", "Звёзд", "Цена за ночь", "Тур"]
            values_data = [hotel[1], hotel[2], hotel[3], hotel[4], current_tour]
            
            for i, field in enumerate(fields):
                tk.Label(dialog, text=field + ":").pack(pady=5)
                if field == "Тур":
                    entry = ttk.Combobox(dialog, values=list(tour_names.keys()), width=27)
                else:
                    entry = tk.Entry(dialog, width=30)
                entry.insert(0, str(values_data[i]))
                entry.pack()
                entries[field] = entry
            
            def save():
                try:
                    name = entries["Название"].get().strip()
                    city = entries["Город"].get().strip()
                    stars = int(entries["Звёзд"].get())
                    price = int(entries["Цена за ночь"].get())
                    tour_title = entries["Тур"].get()
                    tour_id = tour_names.get(tour_title)
                    
                    if not all([name, city, stars, price, tour_id]):
                        messagebox.showerror("Ошибка", "Заполните все поля")
                        return
                    if len(name) < 3 or len(city) < 3:
                        messagebox.showerror("Ошибка", "Название и город должны быть не менее 3 символов")
                        return
                    if stars < 1 or stars > 5:
                        messagebox.showerror("Ошибка", "Звёзд от 1 до 5")
                        return
                    if price <= 0:
                        messagebox.showerror("Ошибка", "Цена должна быть положительной")
                        return
                    
                    update_hotel(hotel_id, name, city, stars, price, tour_id)
                    messagebox.showinfo("Успех", "Отель обновлён")
                    dialog.destroy()
                    load_hotels()
                    self.update_stats()
                except ValueError:
                    messagebox.showerror("Ошибка", "Звёзд и цена должны быть числами")
            
            tk.Button(dialog, text="Сохранить", command=save, bg="orange", fg="white").pack(pady=20)
        
        def delete_hotel():
            selected = tree.selection()
            if not selected:
                messagebox.showerror("Ошибка", "Выберите отель")
                return
            
            values = tree.item(selected[0])['values']
            hotel_name = values[1]
            hotel_id = values[0]
            
            if messagebox.askyesno("Подтверждение удаления",
                                   f"Вы действительно хотите удалить отель «{hotel_name}» (№{hotel_id})?\n\n"
                                   f"⚠️ Это действие нельзя отменить"):
                delete_hotel(hotel_id)
                messagebox.showinfo("Успех", "Отель удалён")
                load_hotels()
                self.update_stats()
        
        tk.Button(btn_frame, text="➕ Добавить", command=add_hotel_dialog, bg="green", fg="white", width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="✏️ Редактировать", command=edit_hotel, bg="orange", width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ Удалить", command=delete_hotel, bg="red", fg="white", width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🔄 Обновить", command=load_hotels, width=12).pack(side=tk.LEFT, padx=5)
        
        load_hotels()
    
    def init_user_tabs(self):
        # Пользователь видит туры
        tours_tab = ttk.Frame(self.notebook)
        self.notebook.add(tours_tab, text="🏝️ Туры")
        
        frame = tk.LabelFrame(tours_tab, text="Доступные туры", padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ["ID", "Название", "Страна", "Цена", "Дней"]
        tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        scroll = tk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        def load_tours():
            for item in tree.get_children():
                tree.delete(item)
            tours = get_tours()
            for tour in tours:
                tree.insert('', tk.END, values=tour)
        
        load_tours()
        
        # Вкладка с бронированиями пользователя
        my_bookings_tab = ttk.Frame(self.notebook)
        self.notebook.add(my_bookings_tab, text="📋 Мои бронирования")
        
        CRUDTable(my_bookings_tab, "Мои бронирования",
                  columns=["ID", "Тур", "Отель", "Дата", "Ночей", "Цена", "Статус"],
                  get_data_func=lambda: get_bookings(self.user_id),
                  add_func=None,
                  update_func=None,
                  delete_func=lambda id: delete_booking(id),
                  form_fields=None,
                  user_role='user')
    
    def logout(self):
        if messagebox.askyesno("Выход", "Вы уверены, что хотите выйти?"):
            self.root.destroy()
            start_app()

# ==================== ЗАПУСК ПРИЛОЖЕНИЯ ====================

def start_app():
    root = tk.Tk()
    
    def start_main_app(user_data):
        root.destroy()
        new_root = tk.Tk()
        MainApp(new_root, user_data)
        new_root.mainloop()
    
    AuthWindow(root, start_main_app)
    root.mainloop()

if __name__ == "__main__":
    init_db()
    start_app()