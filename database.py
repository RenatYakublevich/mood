import sqlite3


class Database:
    def __init__(self,database_file):
        self.connection = sqlite3.connect(database_file)
        self.cursor = self.connection.cursor()

    def add_user(self, name, telegram_username):
        try:
            with self.connection:
                return self.cursor.execute(
                    "INSERT INTO `users` (`name`, `telegram_username`) VALUES(?,?)",
                    (name, telegram_username))
        except sqlite3.IntegrityError:
            pass

    def show_info_user(self, info_param, telegram_username):
        with self.connection:
            return self.cursor.execute(f"SELECT {info_param} FROM `users` WHERE `telegram_username` = ?", (telegram_username,)).fetchone()[0]


    def add_mood(self, text, telegram_username, type):
        with self.connection:
            if type == '🤍':
                type = True
            else:
                type = False

            return self.cursor.execute(
                "INSERT INTO `moods` (`text`, `telegram_username`, `type`) VALUES(?,?,?)",
                (text, telegram_username, type))

    def show_info_mood(self):
        with self.connection:
            pass

    def show_rating(self):
        pass
