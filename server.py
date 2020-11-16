import logging
import os

from aiogram import Bot, types
from aiogram.utils import executor
from aiogram.utils.emoji import emojize
from aiogram.dispatcher import Dispatcher
from aiogram.types.message import ContentType
from aiogram.utils.markdown import text, bold, italic, code, pre
from aiogram.types import ParseMode, InputMediaPhoto, InputMediaVideo, ChatActions
from aiogram.types import ReplyKeyboardRemove,ReplyKeyboardMarkup, KeyboardButton, \
                          InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import config
from database import Database


logging.basicConfig(level=logging.INFO)

API_TOKEN = config.TOKEN

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot,storage=MemoryStorage())

db = Database('db_model.db')


@dp.message_handler(commands=['start', 'help'], state='*')
async def start(message: types.Message):
    button_profile = KeyboardButton('Профиль👤')
    button_add_mood = KeyboardButton('Добавить муд📝')

    menu = ReplyKeyboardMarkup()
    menu.add(button_add_mood, button_profile)

    db.add_user(name=message.from_user.first_name, telegram_username=message.from_user.username)
    await message.answer(f"Привет {message.from_user.first_name.title()}!👋\n\n" \
                         f"Это телеграм бот Mood😎\nМесто, где ты можешь поделится своим мудом на сегодня\n" \
                         f"И не важно чёрный он или белый :)", reply_markup=menu)

@dp.message_handler(lambda message: message.text.lower().startswith('профиль'), state='*')
async def profile(message: types.Message):
    await message.answer(f'Ваш ник - {db.show_info_user(info_param="name",telegram_username=message.from_user.username).title()}\n' \
                         f'Количество очков - {db.show_info_user(info_param="points", telegram_username=message.from_user.username)}\n' \
                         f'Количество мудов - {db.show_info_user(info_param="count_moods", telegram_username=message.from_user.username)}\n')

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
async def mood_type(message: types.Message, state: FSMContext):
    await state.update_data(type=message.text)
    await message.answer('Прекрасно!\nТеперь опиши свой муд парочкой слов')
    await MoodParams.next()

@dp.message_handler(state=MoodParams.text)
async def mood_text(message: types.Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer('Отлично!\nТвой муд опубликован')
    user_data = await state.get_data() # словарь с всеми переменными машины состояния
    db.add_mood(text=user_data['text'], type=user_data['type'], telegram_username=message.from_user.username) # добавляем запись в дб
    await state.finish()
    await start(message)



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)