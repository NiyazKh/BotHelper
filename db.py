import sqlite3
import logging

from config import DB_FILE, log_file

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=log_file,
    filemode="a"
)


def create_database():
    try:
        with sqlite3.connect(DB_FILE) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                total_tokens INTEGER,
                total_tts_symbols INTEGER,
                total_stt_blocks INTEGER)
            ''')
    except Exception as e:
        logging.error(f'Ошибка: {e}')
        return None


def execute_query(sql_query, data=None, db_path=DB_FILE):
    try:
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            if data:
                cursor.execute(sql_query, data)
            else:
                cursor.execute(sql_query)
            connection.commit()
    except Exception as e:
        logging.error(f'Ошибка: {e}')
        return None


def execute_selection_query(sql_query, data=None, db_path=DB_FILE):
    try:
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            if data:
                cursor.execute(sql_query, data)
            else:
                cursor.execute(sql_query)
            rows = cursor.fetchall()
            connection.commit()
            return rows
    except Exception as e:
        logging.error(f'Ошибка: {e}')
        return None


def add_new_user(user_id):
    sql_query = 'INSERT INTO users (user_id, total_tokens, total_tts_symbols, total_stt_blocks) VALUES (?, ?, ?, ?)'
    execute_query(sql_query, (user_id, 0, 0, 0))


def update_tokens(user_id, add_tokens):
    sql_query = f'UPDATE users SET total_tokens = total_tokens + {add_tokens} WHERE user_id={user_id};'
    execute_query(sql_query)


def update_stt_blocks(user_id, add_stt_blocks):
    sql_query = f'UPDATE users SET total_stt_blocks = total_stt_blocks + {add_stt_blocks} WHERE user_id={user_id};'
    execute_query(sql_query)


def update_tts_symbols(user_id, add_tts_symbols):
    sql_query = f'UPDATE users SET total_tts_symbols = total_tts_symbols + {add_tts_symbols} WHERE user_id={user_id};'
    execute_query(sql_query)


def select_all_users():
    users = []
    sql_query = 'SELECT user_id FROM users'
    data = execute_selection_query(sql_query)
    if data and data[0]:
        for user in data:
            users.append(user[0])
    return users


def get_tokens(user_id):
    sql_query = f'SELECT total_tokens, total_stt_blocks, total_tts_symbols FROM users WHERE user_id={user_id}'
    data = execute_selection_query(sql_query)[0]
    if data != ():
        return data[0], data[1], data[2]
    else:
        return 0


#add_new_user(1)
#print(get_tokens(1))
#create_database()
