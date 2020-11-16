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

    def show_count_mood(self, telegram_username):
        with self.connection:
            return self.cursor.execute(f"SELECT `count_moods` FROM `users` WHERE `telegram_username` = ?",
                                       (telegram_username,)).fetchone()[0]

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
            self.cursor.execute('UPDATE `users` SET `count_moods` = ? WHERE `telegram_username` = ?',
                                       (int(self.show_count_mood(telegram_username)) + 1, telegram_username))
            return self.cursor.execute(
                "INSERT INTO `moods` (`text`, `telegram_username`, `type`) VALUES(?,?,?)",
                (text, telegram_username, type_bool))

    def show_info_mood(self):
        with self.connection:
            pass

    def show_rating(self):
        pass
