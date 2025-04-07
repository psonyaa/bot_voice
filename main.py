import os
import whisper
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
import asyncio

# Конфигурация
TOKEN = os.getenv("TELEGRAM_TOKEN")
MODEL_TYPE = "tiny"  # Можно изменить на "small" если будут проблемы с памятью

# Инициализация
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()
model = whisper.load_model(MODEL_TYPE)

async def transcribe_audio(file_path):
    """Транскрибация аудио с помощью Whisper"""
    result = model.transcribe(file_path)
    segments = result["segments"]
    return "\n".join(
        [f"{round(seg['start'], 2)}s - {round(seg['end'], 2)}s: {seg['text']}" 
         for seg in segments]
    )

@dp.message(CommandStart())
async def start(message: types.Message):
    """Обработчик команды /start"""
    await message.answer(
        "Привет! Отправь голосовое сообщение или аудиофайл "
        "(.m4a, .mp3, .wav и др.), и я расшифрую его."
    )

@dp.message(F.voice | F.audio | F.document)
async def handle_media(message: types.Message):
    """Обработчик медиафайлов"""
    try:
        if message.voice:
            file_id = message.voice.file_id
            filename = "voice.ogg"
        elif message.audio:
            file_id = message.audio.file_id
            filename = message.audio.file_name or "audio.mp3"
        else:
            file_id = message.document.file_id
            filename = message.document.file_name or "audio.m4a"

        # Скачиваем файл
        file = await bot.get_file(file_id)
        file_path = await bot.download_file(file.file_path)
        
        # Сохраняем временный файл
        with open(filename, "wb") as f:
            f.write(file_path.read())

        # Транскрибируем и отправляем результат
        transcription = await transcribe_audio(filename)
        await message.answer(f"🔊 *Расшифровка:*\n{transcription}")

    except Exception as e:
        await message.answer("Произошла ошибка при обработке аудио.")
        print(f"Ошибка: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

async def main():
    """Основная функция с обработкой перезапусков"""
    while True:
        try:
            await dp.start_polling(bot)
        except Exception as e:
            print(f"Бот упал с ошибкой: {e}. Перезапуск через 5 секунд...")
            await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(main())
