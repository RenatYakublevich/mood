import logging

from aiogram import Bot, types
from aiogram.utils import executor
from aiogram.dispatcher import Dispatcher
from aiogram.types import ParseMode, InputMediaPhoto, InputMediaVideo, ChatActions
from aiogram.types import ReplyKeyboardRemove,ReplyKeyboardMarkup, KeyboardButton, \
                          InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import config
from database import Database


# логирование
logging.basicConfig(filename="all_log.log", level=logging.INFO, format='%(asctime)s - %(levelname)s -%(message)s')
warning_log = logging.getLogger("warning_log")
warning_log.setLevel(logging.WARNING)

fh = logging.FileHandler("warning_log.log")

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)


warning_log.addHandler(fh)

API_TOKEN = config.TOKEN

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot,storage=MemoryStorage())

db = Database('db_model.db')


@dp.message_handler(commands=['start', 'help'], state='*')
async def start(message: types.Message):
    try:
        button_profile = KeyboardButton('Профиль👤') # Done!
        button_add_mood = KeyboardButton('Добавить муд📝') # Done!
        button_rating = KeyboardButton('Рейтинг🏆') # Done!
        button_feed = KeyboardButton('Лента📰') # 50 / 50 фикс баг с тем что повторяется последний муд

        menu = ReplyKeyboardMarkup()
        menu.add(button_add_mood, button_profile, button_rating, button_feed)

        db.add_user(name=message.from_user.first_name, telegram_username=message.from_user.username)
        await message.answer(f"Привет {message.from_user.first_name.title()}!👋\n\n" \
                             f"Это телеграм бот Mood😎\nМесто, где ты можешь поделится своим мудом на сегодня\n" \
                             f"И не важно чёрный он или белый :)", reply_markup=menu)
    except Exception as e:
        warning_log.warning(e)


@dp.message_handler(lambda message: message.text.lower().startswith('профиль'), state='*')
async def profile(message: types.Message):
    try:
        await message.answer(f'Ваш ник - {db.show_info_user(info_param="name",telegram_username=message.from_user.username).title()}\n' \
                             f'Количество очков - {db.show_info_user(info_param="points", telegram_username=message.from_user.username)}\n' \
                             f'Количество мудов - {db.show_info_user(info_param="count_moods", telegram_username=message.from_user.username)}\n')
    except Exception as e:
        warning_log.warning(e)


# класс для работы с машиной состояний
class MoodParams(StatesGroup):
    type = State()
    text = State()


@dp.message_handler(lambda message: message.text.lower().startswith('добавить муд'), state='*')
async def add_mood(message: types.Message):
    button_white_mood = KeyboardButton('🤍')
    button_black_mood = KeyboardButton('🖤')

    types_mood = ReplyKeyboardMarkup(one_time_keyboard=True)
    types_mood.add(button_black_mood, button_white_mood)

    await message.answer('Напиши тип своего муда\nОн может быть белым - 🤍\nА может быть чёрным - 🖤',reply_markup=types_mood)
    await MoodParams.type.set()


@dp.message_handler(state=MoodParams.type)
async def input_mood_type(message: types.Message, state: FSMContext):
    await state.update_data(type=message.text)
    await message.answer('Прекрасно!\nТеперь опиши свой муд парочкой слов')
    await MoodParams.next()


@dp.message_handler(state=MoodParams.text)
async def input_mood_text(message: types.Message, state: FSMContext):
    try:
        await state.update_data(text=message.text)
        await message.answer('Отлично!\nТвой муд опубликован')
        user_data = await state.get_data() # словарь с всеми переменными машины состояния
        db.add_mood(text=user_data['text'], type=user_data['type'], telegram_username=message.from_user.username) # добавляем запись в дб
        await state.finish()
        await start(message)
    except Exception as e:
        warning_log.warning(e)


# TODO : обернуть в декоратор 
@dp.message_handler(commands=['exit'], state='*')
async def exit(message: types.Message, state: FSMContext):
    await state.finish()
    await start(message)


@dp.message_handler(lambda message: message.text.lower().startswith('рейтинг'), state='*')
async def show_rating(message: types.Message):
    try:
        place_num = 1
        rating = ''
        for place in db.show_rating():
            rating += f'{place_num} место - {db.show_info_user("name",place[0]).title()}'
            place_num += 1
        await message.answer(rating)
    except Exception as e:
        warning_log.warning(e)


@dp.message_handler(lambda message: message.text.startswith('Лента'), state='*')
async def show_mood_feed(message: types.Message):
    button_like = KeyboardButton('❤')
    button_next= KeyboardButton('➡')

    menu = ReplyKeyboardMarkup()
    menu.add(button_like, button_next)

    await message.answer(f'{"🖤" if db.show_info_mood(db.show_info_user("last_view_mood",message.from_user.username))[0] == "0" else "🤍"}\n{db.show_info_mood(db.show_info_user("last_view_mood",message.from_user.username))[2]}',reply_markup=menu)


@dp.message_handler(lambda message: message.text.startswith('➡'), state='*')
async def show_mood_feed_next(message: types.Message):
    try:
        await message.answer(
            f'{"🖤" if db.show_info_mood(db.show_info_user("last_view_mood",message.from_user.username))[0] == "0" else "🤍"}\n{db.show_info_mood(db.show_info_user("last_view_mood", message.from_user.username) + 1)[2]}')
    except TypeError:
        db.update_info_user(info_param='last_view_mood',info_param_value=1,telegram_username=message.from_user.username)
        await message.answer(
            f'{"🖤" if db.show_info_mood(db.show_info_user("last_view_mood",message.from_user.username))[0] == "0" else "🤍"}\n{db.show_info_mood(db.show_info_user("last_view_mood", message.from_user.username))[2]}')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)