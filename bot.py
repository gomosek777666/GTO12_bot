import asyncio
import logging
import os
from datetime import datetime

from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токен вашего бота
TOKEN = "8918149877:AAGgFuFo37-pmqhXw-htk51awMmmZ8rpq9I"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Хранилище прогресса пользователей (в памяти)
# Формат: {user_id: [{"exercise": "Отжимания", "count": 25, "date": "06.10.2026"}]}
user_progress = {}

# Определение состояний FSM для записи прогресса
class ProgressState(StatesGroup):
    waiting_for_exercise = State()
        waiting_for_count = State()

        # Клавиатуры
        main_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                    [KeyboardButton(text="📋 План тренировок ГТО")],
                            [KeyboardButton(text="✏️ Записать результат"), KeyboardButton(text="📊 Мой прогресс")]
                                ],
                                    resize_keyboard=True
                                    )

                                    exercise_keyboard = ReplyKeyboardMarkup(
                                        keyboard=[
                                                [KeyboardButton(text="Подтягивания"), KeyboardButton(text="Отжимания")],
                                                        [KeyboardButton(text="Наклон из положения стоя"), KeyboardButton(text="Прыжок в длину")],
                                                                [KeyboardButton(text="❌ Отмена")]
                                                                    ],
                                                                        resize_keyboard=True
                                                                        )

                                                                        # Команда /start
                                                                        @dp.message(Command("start"))
                                                                        async def start_handler(message: types.Message):
                                                                            await message.answer(
                                                                                    f"Привет, {message.from_user.first_name}! 👋\n\n"
                                                                                            "Я твой персональный бот для подготовки к нормативам ГТО (VI ступень) и ведения дневника тренировок.\n"
                                                                                                    "Выбери нужный раздел в меню ниже:",
                                                                                                            reply_markup=main_keyboard
                                                                                                                )

                                                                                                                # Обработка кнопки "Отмена"
                                                                                                                @dp.message(F.text == "❌ Отмена")
                                                                                                                async def cancel_handler(message: types.Message, state: FSMContext):
                                                                                                                    await state.clear()
                                                                                                                        await message.answer("Действие отменено.", reply_markup=main_keyboard)

                                                                                                                        # Раздел "План тренировок"
                                                                                                                        @dp.message(F.text == "📋 План тренировок ГТО")
                                                                                                                        async def workout_plan(message: types.Message):
                                                                                                                            plan_text = (
                                                                                                                                    "🏆 **План подготовки к ГТО (VI ступень)**\n\n"
                                                                                                                                            "1️⃣ **Силовая подготовка:**\n"
                                                                                                                                                    "   • Подтягивания / Отжимания: 3-4 подхода по 70-80% от максимума.\n\n"
                                                                                                                                                            "2️⃣ **Гибкость:**\n"
                                                                                                                                                                    "   • Наклон вперед из положения стоя: 3 подхода с фиксацией на 10-15 секунд.\n\n"
                                                                                                                                                                            "3️⃣ **Скоростно-силовые:**\n"
                                                                                                                                                                                    "   • Прыжок в длину с места: 5-8 попыток с отдыхами.\n\n"
                                                                                                                                                                                            "💡 *Регулярно записывай свои результаты через кнопку «Записать результат»!*"
                                                                                                                                                                                                )
                                                                                                                                                                                                    await message.answer(plan_text, parse_mode="Markdown")

                                                                                                                                                                                                    # Старт записи прогресса (FSM)
                                                                                                                                                                                                    @dp.message(F.text == "✏️ Записать результат")
                                                                                                                                                                                                    async def start_record(message: types.Message, state: FSMContext):
                                                                                                                                                                                                        await state.set_state(ProgressState.waiting_for_exercise)
                                                                                                                                                                                                            await message.answer("Выбери упражнение из списка или напиши свое:", reply_markup=exercise_keyboard)

                                                                                                                                                                                                            # Выбор упражнения
                                                                                                                                                                                                            @dp.message(ProgressState.waiting_for_exercise)
                                                                                                                                                                                                            async def process_exercise(message: types.Message, state: FSMContext):
                                                                                                                                                                                                                await state.update_data(exercise=message.text)
                                                                                                                                                                                                                    await state.set_state(ProgressState.waiting_for_count)
                                                                                                                                                                                                                        await message.answer("Введи количество повторений или результат (только число):", reply_markup=ReplyKeyboardRemove())

                                                                                                                                                                                                                        # Ввод количества и сохранение
                                                                                                                                                                                                                        @dp.message(ProgressState.waiting_for_count)
                                                                                                                                                                                                                        async def process_count(message: types.Message, state: FSMContext):
                                                                                                                                                                                                                            if not message.text.isdigit():
                                                                                                                                                                                                                                    await message.answer("Пожалуйста, введи число!")
                                                                                                                                                                                                                                            return

                                                                                                                                                                                                                                                count = int(message.text)
                                                                                                                                                                                                                                                    user_data = await state.get_data()
                                                                                                                                                                                                                                                        exercise = user_data['exercise']
                                                                                                                                                                                                                                                            user_id = message.from_user.id
                                                                                                                                                                                                                                                                current_date = datetime.now().strftime("%d.%m.%Y")

                                                                                                                                                                                                                                                                    if user_id not in user_progress:
                                                                                                                                                                                                                                                                            user_progress[user_id] = []

                                                                                                                                                                                                                                                                                user_progress[user_id].append({
                                                                                                                                                                                                                                                                                        "exercise": exercise,
                                                                                                                                                                                                                                                                                                "count": count,
                                                                                                                                                                                                                                                                                                        "date": current_date
                                                                                                                                                                                                                                                                                                            })

                                                                                                                                                                                                                                                                                                                await state.clear()
                                                                                                                                                                                                                                                                                                                    await message.answer(
                                                                                                                                                                                                                                                                                                                            f"✅ Результат успешно сохранен!\n\n"
                                                                                                                                                                                                                                                                                                                                    f"📌 **{exercise}**: {count} ({current_date})",
                                                                                                                                                                                                                                                                                                                                            reply_markup=main_keyboard,
                                                                                                                                                                                                                                                                                                                                                    parse_mode="Markdown"
                                                                                                                                                                                                                                                                                                                                                        )

                                                                                                                                                                                                                                                                                                                                                        # Просмотр прогресса
                                                                                                                                                                                                                                                                                                                                                        @dp.message(F.text == "📊 Мой прогресс")
                                                                                                                                                                                                                                                                                                                                                        async def show_progress(message: types.Message):
                                                                                                                                                                                                                                                                                                                                                            user_id = message.from_user.id
                                                                                                                                                                                                                                                                                                                                                                records = user_progress.get(user_id, [])

                                                                                                                                                                                                                                                                                                                                                                    if not records:
                                                                                                                                                                                                                                                                                                                                                                            await message.answer("У тебя пока нет сохраненных результатов. Нажми «✏️ Записать результат», чтобы добавить первую запись!")
                                                                                                                                                                                                                                                                                                                                                                                    return

                                                                                                                                                                                                                                                                                                                                                                                        text = "📊 **Твой журнал прогресса:**\n\n"
                                                                                                                                                                                                                                                                                                                                                                                            for item in records[-10:]:  # Показываем последние 10 записей
                                                                                                                                                                                                                                                                                                                                                                                                    text += f"• `{item['date']}` — **{item['exercise']}**: {item['count']}\n"

                                                                                                                                                                                                                                                                                                                                                                                                        await message.answer(text, parse_mode="Markdown")

                                                                                                                                                                                                                                                                                                                                                                                                        # Встроенный веб-сервер aiohttp для поддержания работы облачного сервиса
                                                                                                                                                                                                                                                                                                                                                                                                        async def handle_ping(request):
                                                                                                                                                                                                                                                                                                                                                                                                            return web.Response(text="Bot is running active!")

                                                                                                                                                                                                                                                                                                                                                                                                            async def start_web_server():
                                                                                                                                                                                                                                                                                                                                                                                                                app = web.Application()
                                                                                                                                                                                                                                                                                                                                                                                                                    app.router.add_get("/", handle_ping)
                                                                                                                                                                                                                                                                                                                                                                                                                        app.router.add_get("/ping", handle_ping)
                                                                                                                                                                                                                                                                                                                                                                                                                            runner = web.AppRunner(app)
                                                                                                                                                                                                                                                                                                                                                                                                                                await runner.setup()
                                                                                                                                                                                                                                                                                                                                                                                                                                    port = int(os.environ.get("PORT", 8080))
                                                                                                                                                                                                                                                                                                                                                                                                                                        site = web.TCPSite(runner, "0.0.0.0", port)
                                                                                                                                                                                                                                                                                                                                                                                                                                            await site.start()
                                                                                                                                                                                                                                                                                                                                                                                                                                                logging.info(f"Веб-сервер запущен на порту {port}")

                                                                                                                                                                                                                                                                                                                                                                                                                                                # Главная функция запуска
                                                                                                                                                                                                                                                                                                                                                                                                                                                async def main():
                                                                                                                                                                                                                                                                                                                                                                                                                                                    await start_web_server()
                                                                                                                                                                                                                                                                                                                                                                                                                                                        print("Бот с функцией прогресса запущен!")
                                                                                                                                                                                                                                                                                                                                                                                                                                                            await dp.start_polling(bot)

                                                                                                                                                                                                                                                                                                                                                                                                                                                            if __name__ == "__main__":
                                                                                                                                                                                                                                                                                                                                                                                                                                                                asyncio.run(main())
                                                                                                                                                                                                                                                                                                                                                                                                                                                                