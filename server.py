import logging

from aiogram import *
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
logging.basicConfig()
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

BACK = 'Назад◀'
ad_count = 10


async def ad(message: types.Message):
    photo = open('ad.jpg','rb')

    await message.answer_photo(photo,caption='Здесь могла быть ваша реклама :)')


@dp.message_handler(commands=['start', 'help'], state='*')
async def start(message: types.Message):
    try:
        button_profile = KeyboardButton('Профиль👤') # Done!
        button_add_mood = KeyboardButton('Добавить муд📝') # Done!
        button_rating = KeyboardButton('Рейтинг🏆') # Done!
        button_feed = KeyboardButton('Лента📰') # Done!
        button_achievements = KeyboardButton('Достижения🎖')

        menu = ReplyKeyboardMarkup()
        menu.add(button_add_mood, button_profile, button_rating, button_feed, button_achievements)

        db.add_user(name=message.from_user.first_name, telegram_username=message.from_user.username)
        await message.answer(f"Привет {message.from_user.first_name.title()}!👋\n\n" \
                             f"Это телеграм бот Mood😎\nМесто, где ты можешь поделится своим мудом на сегодня\n" \
                             f"И не важно чёрный он или белый :)", reply_markup=menu)
    except Exception as e:
        warning_log.warning(e)


@dp.message_handler(lambda message: message.text.lower().startswith('профиль') or message.text == '/profile', state='*')
async def profile(message):
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


@dp.message_handler(lambda message: message.text.lower().startswith('добавить муд') or message.text == '/add_mood', state='*')
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


@dp.message_handler(lambda message: message.text.lower().startswith('рейтинг') or message.text == '/rating', state='*')
async def show_rating(message: types.Message):
    try:
        place_num = 1
        rating = ''
        for place in db.show_rating():
            rating += f'{place_num} место - {db.show_info_user("name",place[0]).title()}\n'
            place_num += 1
        await message.answer(rating)
    except Exception as e:
        warning_log.warning(e)


@dp.message_handler(lambda message: message.text.startswith('Лента') or message.text == '/feed', state='*')
async def show_mood_feed(message: types.Message):
    button_like = KeyboardButton('❤')
    button_next= KeyboardButton('➡')
    button_back = KeyboardButton(BACK)

    menu = ReplyKeyboardMarkup()
    menu.add(button_back, button_like, button_next)

    await message.answer(
        f'{"🖤" if db.show_info_mood(db.show_info_user("last_view_mood", message.from_user.username))[0] == 0 else "🤍"}\n{db.show_info_mood(db.show_info_user("last_view_mood", message.from_user.username))[2]}',reply_markup=menu)


@dp.message_handler(lambda message: message.text.startswith('➡'), state='*')
async def show_mood_feed_next(message: types.Message, state: FSMContext):
    try:
        if message.text == BACK:
            await _exit(message, state)

        if db.show_info_user(info_param='ad_count',telegram_username=message.from_user.username) / ad_count == 1:
            await ad(message)
            db.update_info_user(info_param='ad_count',
                                info_param_value=1,
                                telegram_username=message.from_user.username)
            return 1

        await message.answer(
            f'{"🖤" if db.show_info_mood(db.show_info_user("last_view_mood",message.from_user.username) + 1)[0] == 0 else "🤍"}\n{db.show_info_mood(db.show_info_user("last_view_mood", message.from_user.username) + 1)[2]}')

        # добавляем +1 к счётчику рекламы(каждые 10 мудов реклама)
        db.update_info_user(info_param='ad_count', info_param_value=db.show_info_user("ad_count", message.from_user.username) + 1,
                            telegram_username=message.from_user.username)

        # обновляем последний муд юзера на + 1
        db.update_info_user(info_param='last_view_mood', info_param_value=db.show_info_user("last_view_mood", message.from_user.username) + 1,
                            telegram_username=message.from_user.username)


    except TypeError as e: # если записи заканчиваются
        # обновляем последний муд юзера на 1
        db.update_info_user(info_param='last_view_mood',info_param_value=1,telegram_username=message.from_user.username)
        await message.answer(
            f'{"🖤" if db.show_info_mood(db.show_info_user("last_view_mood",message.from_user.username))[0] == 0 else "🤍"}\n{db.show_info_mood(db.show_info_user("last_view_mood", message.from_user.username))[2]}')

    except Exception as e:
        warning_log.warning(e)


@dp.message_handler(lambda message: message.text.startswith('❤'), state='*')
async def show_mood_feed_like(message: types.Message, state: FSMContext):
    try:
        if message.text == BACK:
            await _exit(message, state)
        if db.show_info_user(info_param='ad_count',telegram_username=message.from_user.username) / ad_count == 1:
            await ad(message)
            db.update_info_user(info_param='ad_count',
                                info_param_value=1,
                                telegram_username=message.from_user.username)
            return 1
        await message.answer(
            f'{"🖤" if db.show_info_mood(db.show_info_user("last_view_mood",message.from_user.username) + 1)[0] == 0 else "🤍"}\n{db.show_info_mood(db.show_info_user("last_view_mood", message.from_user.username) + 1)[2]}')
        # добавляем +1 к счётчику рекламы(каждые 10 мудов реклама)
        db.update_info_user(info_param='ad_count',
                            info_param_value=db.show_info_user("ad_count", message.from_user.username) + 1,
                            telegram_username=message.from_user.username)

        # добавляем лайк к записе
        db.update_info_mood('likes',
                            db.show_info_mood(db.show_info_user("last_view_mood", message.from_user.username))[4] + 1,
                            db.show_info_user("last_view_mood", message.from_user.username))

        # добавляем очки юзеру который лайкнул
        db.update_info_user(info_param='points',
                            info_param_value=db.show_info_user("points", message.from_user.username) + 2,
                            telegram_username=message.from_user.username)

        # добавляем +1 к счётчику лайков
        db.update_info_user(info_param='count_likes',
                            info_param_value=db.show_info_user("count_likes", message.from_user.username) + 1,
                            telegram_username=message.from_user.username)

        # обновляем последний муд юзера + 1
        db.update_info_user(info_param='last_view_mood', info_param_value=db.show_info_user("last_view_mood", message.from_user.username) + 1,
                            telegram_username=message.from_user.username)
    except TypeError as e: # если записи заканчиваются
        #print(e)
        db.update_info_user(info_param='count_likes',
                            info_param_value=db.show_info_user("count_likes", message.from_user.username) + 1,
                            telegram_username=message.from_user.username)
        db.update_info_user(info_param='points',
                            info_param_value=db.show_info_user("points", message.from_user.username) + 2,
                            telegram_username=message.from_user.username)
        db.update_info_mood('likes',
                            db.show_info_mood(db.show_info_user("last_view_mood", message.from_user.username))[4] + 1,
                            db.show_info_user("last_view_mood", message.from_user.username))
        db.update_info_user(info_param='last_view_mood',info_param_value=1,telegram_username=message.from_user.username)
        await message.answer(
            f'{"🖤" if db.show_info_mood(db.show_info_user("last_view_mood",message.from_user.username))[0] == 0 else "🤍"}\n{db.show_info_mood(db.show_info_user("last_view_mood", message.from_user.username)  )[2]}')
    except Exception as e:
        warning_log.warning(e)

@dp.message_handler(lambda message: message.text.startswith('Достижения') or message.text == '/achievements')
async def achievements(message: types.Message):
    await message.answer(
        f'Достижения :\n\nЛюбовь всему миру🥰\nЛайкнуть 50 мудов\n{str(db.show_info_user("count_likes", message.from_user.username)) + "/50" if db.show_info_user("count_likes", message.from_user.username) < 50 else "Done✅"}\n\nКонтент крейтор🎥\nДобавить 20 мудов\n{str(db.show_info_user("count_moods", message.from_user.username)) + "/20" if db.show_info_user("count_moods", message.from_user.username) < 20 else "Done✅"}\n\nЛучший в мире😎\nТоп 1 в рейтинге\n0/1')

@dp.message_handler(lambda message: message.text == BACK, state='*')
async def _exit(message: types.Message, state: FSMContext):
    await state.finish()
    await start(message)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)