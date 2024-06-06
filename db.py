import sqlite3

# Создаем соединение с базой данных (если базы данных не существует, она будет автоматически создана)
conn = sqlite3.connect('smoking_pics.db')

# Создаем курсор для выполнения операций с базой данных
cursor = conn.cursor()

# Создаем таблицу
cursor.execute('''CREATE TABLE IF NOT EXISTS фотографии (
                    id_camera INTEGER,
                    date DATE,
                    time TIME,
                    path TEXT
                )''')


# Сохраняем изменения
conn.commit()

# Закрываем соединение с базой данных
conn.close()
