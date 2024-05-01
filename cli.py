import sqlite3

# Функция для добавления заметки
def add_note():
    title = input("Введите заголовок заметки: ")
    content = input("Введите содержание заметки: ")

    cursor.execute("INSERT INTO notes (title, content) VALUES (?, ?)", (title, content))
    conn.commit()
    print("Заметка успешно добавлена")

# Функция для просмотра всех заметок
def view_notes():
    cursor.execute("SELECT title, content FROM notes")
    notes = cursor.fetchall()
    if not notes:
        print("Список заметок пуст")
    else:
        for note in notes:
            print(note[0], note[1])  # Отображаем заголовок и содержание в одной строке через пробел

# Функция для поиска заметок по ключевому слову
def search_notes():
    keyword = input("Введите ключевое слово для поиска: ")

    cursor.execute("SELECT title, content FROM notes WHERE title LIKE ? OR content LIKE ?", ('%'+keyword+'%', '%'+keyword+'%'))
    notes = cursor.fetchall()
    if not notes:
        print("Заметки по вашему запросу не найдены")
    else:
        for note in notes:
            print(note[0], note[1])  # Отображаем заголовок и содержание в одной строке через пробел

# Функция для удаления заметки
def delete_note():
    cursor.execute("SELECT title FROM notes")
    notes = cursor.fetchall()
    if not notes:
        print("Список заметок пуст")
    else:
        print("Выберите заметку для удаления:")
        for note in notes:
            print(note[0])
        note_title = input("Введите заголовок заметки для удаления: ")

        cursor.execute("DELETE FROM notes WHERE title=?", (note_title,))
        conn.commit()
        print("Заметка успешно удалена")

# Подключение к базе данных
conn = sqlite3.connect('notes.db')
cursor = conn.cursor()

# Создание таблицы для заметок, если она не существует
cursor.execute('''
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY,
    title TEXT,
    content TEXT
)
''')
conn.commit()

# Основной цикл CLI приложения
while True:
    print("\nВыберите действие:")
    print("1. Добавить заметку")
    print("2. Просмотреть заметки")
    print("3. Поиск заметок")
    print("4. Удалить заметку")
    print("5. Выйти")

    choice = input("Введите номер действия: ")

    if choice == '1':
        add_note()
    elif choice == '2':
        view_notes()
    elif choice == '3':
        search_notes()
    elif choice == '4':
        delete_note()
    elif choice == '5':
        break
    else:
        print("Некорректный ввод. Попробуйте снова.")
