import sqlite3
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# Инициализация бота и хранилища в памяти
bot = Bot(token="my_token")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

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

# Определение состояний для добавления заметок
class NoteStates:
    WaitingForTitle = "waiting_for_title"
    WaitingForContent = "waiting_for_content"
    WaitingForSearch = "waiting_for_search"

# Обработчик команды start для начала взаимодействия с ботом
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    # Создание клавиатуры с доступными действиями
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="Добавить заметку", callback_data="add_note"))
    keyboard.add(InlineKeyboardButton(text="Просмотреть заметки", callback_data="view_notes"))
    keyboard.add(InlineKeyboardButton(text="Поиск заметок", callback_data="search_notes"))
    keyboard.add(InlineKeyboardButton(text="Удалить заметку", callback_data="delete_note"))
    await message.answer("Выберите действие:", reply_markup=keyboard)

# Обработчик нажатия кнопки "Добавить заметку"
@dp.callback_query_handler(lambda c: c.data == 'add_note')
async def add_note(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Введите заголовок заметки:")
    await state.set_state(NoteStates.WaitingForTitle)

# Обработчик ввода заголовка заметки
@dp.message_handler(state=NoteStates.WaitingForTitle)
async def process_title(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['title'] = message.text
    await message.answer("Введите содержание заметки:")
    await state.set_state(NoteStates.WaitingForContent)

# Обработчик ввода содержания заметки
@dp.message_handler(state=NoteStates.WaitingForContent)
async def process_content(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['content'] = message.text
    await save_note(message, state)

# Функция для сохранения заметки в базу данных
async def save_note(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        title = data['title']
        content = data['content']

    cursor.execute("INSERT INTO notes (title, content) VALUES (?, ?)", (title, content))
    conn.commit()
    await message.answer("Заметка успешно добавлена")
    await state.finish()  # Сброс состояния до начального

# Обработчик просмотра всех заметок
@dp.callback_query_handler(lambda c: c.data == 'view_notes')
async def view_notes(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    cursor.execute("SELECT title FROM notes")
    notes = cursor.fetchall()
    if not notes:
        await bot.send_message(callback_query.from_user.id, "Список заметок пуст")
    else:
        keyboard = InlineKeyboardMarkup()
        for note in notes:
            keyboard.add(InlineKeyboardButton(text=note[0], callback_data=f"view_note_{note[0]}"))
        await bot.send_message(callback_query.from_user.id, "Выберите заметку для просмотра:", reply_markup=keyboard)

# Обработчик просмотра отдельной заметки
@dp.callback_query_handler(lambda c: c.data.startswith('view_note_'))
async def view_note(callback_query: types.CallbackQuery):
    note_title = callback_query.data.split('_')[-1]
    cursor.execute("SELECT content FROM notes WHERE title=?", (note_title,))
    note_content = cursor.fetchone()
    if note_content:
        await bot.send_message(callback_query.from_user.id, f"Заголовок: {note_title}\n\n{note_content[0]}")
    else:
        await bot.send_message(callback_query.from_user.id, "Заметка не найдена")

# Обработчик поиска заметок
@dp.callback_query_handler(lambda c: c.data == 'search_notes')
async def search_notes(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Введите ключевое слово для поиска:")
    await state.set_state(NoteStates.WaitingForSearch)

# Обработчик ввода ключевого слова для поиска
@dp.message_handler(state=NoteStates.WaitingForSearch)
async def search_notes_by_keyword(message: types.Message, state: FSMContext):
    keyword = message.text
    cursor.execute("SELECT title FROM notes WHERE title LIKE ? OR content LIKE ?", ('%'+keyword+'%', '%'+keyword+'%'))
    notes = cursor.fetchall()
    if not notes:
        await message.answer("Заметки по вашему запросу не найдены")
    else:
        keyboard = InlineKeyboardMarkup()
        for note in notes:
            keyboard.add(InlineKeyboardButton(text=note[0], callback_data=f"view_note_{note[0]}"))
        await message.answer("Результаты поиска:", reply_markup=keyboard)
    await state.finish()  # Сброс состояния до начального

# Обработчик удаления заметки
@dp.callback_query_handler(lambda c: c.data == 'delete_note')
async def delete_note(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    cursor.execute("SELECT title FROM notes")
    notes = cursor.fetchall()
    if not notes:
        await bot.send_message(callback_query.from_user.id, "Список заметок пуст")
    else:
        keyboard = InlineKeyboardMarkup()
        for note in notes:
            keyboard.add(InlineKeyboardButton(text=note[0], callback_data=f"confirm_delete_note_{note[0]}"))
        await bot.send_message(callback_query.from_user.id, "Выберите заметку для удаления:", reply_markup=keyboard)

# Обработчик подтверждения удаления заметки
@dp.callback_query_handler(lambda c: c.data.startswith('confirm_delete_note_'))
async def process_confirm_delete_note(callback_query: types.CallbackQuery):
    note_title = callback_query.data.split('_')[-1]
    cursor.execute("DELETE FROM notes WHERE title=?", (note_title,))
    conn.commit()
    await bot.answer_callback_query(callback_query.id, "Заметка успешно удалена")

# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
