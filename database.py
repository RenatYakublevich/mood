import sqlite3


class Database:
    def __init__(self,database_file):
        self.connection = sqlite3.connect(database_file)
        self.cursor = self.connection.cursor()


    def add_user(self, name, telegram_username):
        """
        Функция добавляет пользователя в таблицу users
        :param name: никнейм пользователя
        :param telegram_username: уникальный никнейм в телеграме
        :return: None
        """
        try:
            with self.connection:
                return self.cursor.execute(
                    "INSERT INTO `users` (`name`, `telegram_username`) VALUES(?,?)",
                    (name, telegram_username))
        except sqlite3.IntegrityError:
            pass


    def show_info_user(self, info_param, telegram_username):
        """
        :param info_param: параметр для возврата функцией
        :param telegram_username: уникальный никнейм в телеграме
        :return: Функция возвращает информацию о пользователе
        """
        with self.connection:
            return self.cursor.execute(f"SELECT {info_param} FROM `users` WHERE `telegram_username` = ?",
                                       (telegram_username,)).fetchone()[0]


    def update_info_user(self, info_param, info_param_value, telegram_username):
        """
        :param info_param: параметр для обновления
        :param info_param_value: значения параметра для обновления
        :param telegram_username: уникальный никнейм в телеграм
        :return: None
        """
        with self.connection:
            self.cursor.execute(f'UPDATE `users` SET `last_view_mood` = ? WHERE `telegram_username` = ?',(info_param_value,telegram_username))

    def add_mood(self, text, telegram_username, type):
        """
        Функция создаёт запись в таблице moods
        :param text: текст записи
        :param telegram_username: уникальный никнейм в телеграме
        :param type: тип записи(белый или чёрный / True или False)
        :return: None
        """
        with self.connection:
            type_bool = True if type == '🤍' else False # если сердечко белое - True
            # прибовляем +1 к количеству записей
            self.cursor.execute('UPDATE `users` SET `count_moods` = ? WHERE `telegram_username` = ?',
                                       (int(self.show_info_user('count_moods', telegram_username)) + 1, telegram_username))

            # прибавляем +5 к количеству поинтов
            self.cursor.execute('UPDATE `users` SET `points` = ? WHERE `telegram_username` = ?',
                                (int(self.show_info_user('points', telegram_username)) + 5, telegram_username))
            return self.cursor.execute(
                "INSERT INTO `moods` (`text`, `telegram_username`, `type`) VALUES(?,?,?)",
                (text, telegram_username, type_bool))


    def show_info_mood(self, mood_id):
        """
        :param mood_id: айди записи
        :return: функция возвращает информацию о записе по её айди
        """
        with self.connection:
            return self.cursor.execute(f"SELECT `type`,`telegram_username`,`text` FROM `moods` WHERE `id` = ?",
                                       (mood_id,)).fetchone()


    def show_rating(self):
        """
        :return: функция возвращает топ 5 пользователей по очкам
        """
        with self.connection:
            return self.cursor.execute(
                'SELECT `telegram_username` FROM `users` ORDER BY `points` DESC LIMIT 5').fetchall()


# db = Database('db_model.db') # FOR DEBUG

# print(db.update_info_user(info_param='x',info_param_value=2,telegram_username='dop3file')) # FOR DEBUG

