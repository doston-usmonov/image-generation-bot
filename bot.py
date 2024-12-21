import os
import logging
import json
import requests
import traceback
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import TelegramAPIError
from dotenv import load_dotenv
from database import db
import time
from datetime import datetime

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bot.log'
)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
LEONARDO_API_KEY = os.getenv('LEONARDO_API_KEY')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')  # Default value if not set

storage = MemoryStorage()
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot, storage=storage)

# States
class GenerateImage(StatesGroup):
    waiting_for_prompt = State()

# Bot commands setup
BOT_COMMANDS = [
    types.BotCommand(command="start", description="Botni ishga tushirish"),
    types.BotCommand(command="help", description="Yordam"),
    types.BotCommand(command="generate", description="Rasm yaratish"),
    types.BotCommand(command="myimages", description="Mening rasmlarim"),
    types.BotCommand(command="stats", description="Statistika"),
    types.BotCommand(command="admin", description="Admin paneli"),
]

# Help message
HELP_MESSAGE = f"""
🤖 Leonardo AI Bot yordamida siz:

1. 🎨 Sun'iy intellekt yordamida rasmlar yaratishingiz
2. 🖼 O'z rasmlaringizni saqlab qo'yishingiz
3. 📂 Saqlangan rasmlaringizni ko'rishingiz mumkin

Buyruqlar:
/start - Botni ishga tushirish
/help - Yordam
/generate - Yangi rasm yaratish
/myimages - Mening rasmlarim
/stats - Statistika
/admin - Admin paneli

❓ Savol va takliflar uchun: @{ADMIN_USERNAME}
"""

# Welcome message
WELCOME_MESSAGE = f"""
👋 Xush kelibsiz! Men Leonardo AI yordamida rasmlar yaratuvchi botman.

🎨 Men sizga matn orqali tasvirlangan rasmlaringizni yaratishda yordam beraman. 
Buning uchun /generate buyrug'ini yuboring yoki "🎨 Rasm yaratish" tugmasini bosing.

💡 Masalan: "a beautiful sunset over mountains" yoki "a cute cat playing with yarn"

🖼 Yaratilgan rasmlaringizni ko'rish uchun /myimages buyrug'ini yuboring.

❓ Savol va takliflar uchun: @{ADMIN_USERNAME}
"""

async def setup_bot_commands(bot: Bot):
    try:
        await bot.set_my_commands(BOT_COMMANDS)
        logger.info("Bot commands have been set up successfully")
    except Exception as e:
        logger.error(f"Error setting up bot commands: {str(e)}")

# Leonardo API functions
def generate_image_with_leonardo(prompt: str):
    try:
        api_key = os.getenv("LEONARDO_API_KEY")
        if not api_key:
            logger.error("LEONARDO_API_KEY not found in environment variables")
            return None
            
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Create generation
        data = {
            "prompt": prompt,
            "num_images": 1,
            "width": 512,
            "height": 512
        }
        
        logger.info(f"Sending generation request to Leonardo API with prompt: {prompt}")
        response = requests.post(
            "https://cloud.leonardo.ai/api/rest/v1/generations",
            headers=headers,
            json=data
        )
        
        logger.info(f"Leonardo API generation response status code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Leonardo API generation response: {result}")
            
            if 'sdGenerationJob' in result and 'generationId' in result['sdGenerationJob']:
                generation_id = result['sdGenerationJob']['generationId']
                
                # Wait for generation to complete and get the result
                max_attempts = 30  # Maximum number of attempts (5 minutes total)
                attempt = 0
                while attempt < max_attempts:
                    logger.info(f"Checking generation status, attempt {attempt + 1}/{max_attempts}")
                    
                    # Get generation result
                    result_response = requests.get(
                        f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}",
                        headers=headers
                    )
                    
                    if result_response.status_code == 200:
                        result_data = result_response.json()
                        logger.info(f"Generation status response: {result_data}")
                        
                        if 'generations_by_pk' in result_data and result_data['generations_by_pk'].get('status') == 'COMPLETE':
                            images = result_data['generations_by_pk'].get('generated_images', [])
                            if images:
                                return {'image_url': images[0].get('url')}
                            break
                        elif result_data['generations_by_pk'].get('status') == 'FAILED':
                            logger.error("Generation failed")
                            break
                    
                    attempt += 1
                    time.sleep(10)  # Wait 10 seconds before next attempt
                
                if attempt >= max_attempts:
                    logger.error("Generation timed out")
            else:
                logger.error("No generationId in response")
            return None
        else:
            logger.error(f"Leonardo API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error in generate_image_with_leonardo: {str(e)}\n{traceback.format_exc()}")
        return None

# Command handlers
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    try:
        await db.add_user(message.from_user.id, message.from_user.username)
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🎨 Rasm yaratish", callback_data="generate"))
        keyboard.add(InlineKeyboardButton("🖼 Mening rasmlarim", callback_data="my_images"))
        keyboard.add(InlineKeyboardButton("❓ Yordam", callback_data="help"))
        
        await message.reply(WELCOME_MESSAGE, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in send_welcome: {str(e)}\n{traceback.format_exc()}")
        await message.reply("❌ Tizimda xatolik yuz berdi")

@dp.message_handler(commands=['help'])
@dp.callback_query_handler(lambda c: c.data == 'help')
async def send_help(message_or_callback: types.Message | types.CallbackQuery):
    try:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🎨 Rasm yaratish", callback_data="generate"))
        keyboard.add(InlineKeyboardButton("🖼 Mening rasmlarim", callback_data="my_images"))
        
        if isinstance(message_or_callback, types.CallbackQuery):
            await bot.answer_callback_query(message_or_callback.id)
            await bot.send_message(
                message_or_callback.from_user.id,
                HELP_MESSAGE,
                reply_markup=keyboard
            )
        else:
            await message_or_callback.reply(HELP_MESSAGE, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in send_help: {str(e)}\n{traceback.format_exc()}")
        error_message = "❌ Tizimda xatolik yuz berdi"
        if isinstance(message_or_callback, types.CallbackQuery):
            await bot.send_message(message_or_callback.from_user.id, error_message)
        else:
            await message_or_callback.reply(error_message)

@dp.message_handler(commands=['stats'])
async def show_stats(message: types.Message):
    try:
        user = await db.get_user(message.from_user.id)
        if not user or not user['is_admin']:
            await message.reply("❌ Bu buyruq faqat adminlar uchun")
            return
            
        stats = await db.get_stats()
        
        stats_message = (
            "📊 Bot statistikasi:\n\n"
            f"👥 Jami foydalanuvchilar: {stats['total_users']}\n"
            f"👤 Faol foydalanuvchilar: {stats['active_users']}\n"
            f"🖼 Jami rasmlar: {stats['total_images']}\n"
            f"🎨 Bugun yaratilgan rasmlar: {stats['images_today']}\n"
            f"🚫 Bloklangan foydalanuvchilar: {stats['blocked_users']}\n"
            f"👨‍💼 Adminlar soni: {stats['admin_count']}"
        )
        
        await message.reply(stats_message)
    except Exception as e:
        logger.error(f"Error in show_stats: {str(e)}\n{traceback.format_exc()}")
        await message.reply("❌ Tizimda xatolik yuz berdi")

@dp.message_handler(commands=['generate'])
@dp.callback_query_handler(lambda c: c.data == 'generate')
async def process_generate(message_or_callback: types.Message | types.CallbackQuery):
    try:
        if isinstance(message_or_callback, types.CallbackQuery):
            await bot.answer_callback_query(message_or_callback.id)
            message = message_or_callback.message
            user_id = message_or_callback.from_user.id
        else:
            message = message_or_callback
            user_id = message.from_user.id
            
        user = await db.get_user(user_id)
        if not user:
            error_message = "❌ Foydalanuvchi topilmadi"
            if isinstance(message_or_callback, types.CallbackQuery):
                await bot.send_message(user_id, error_message)
            else:
                await message.reply(error_message)
            return
            
        if user['is_blocked']:
            error_message = "❌ Siz bloklangansiz"
            if isinstance(message_or_callback, types.CallbackQuery):
                await bot.send_message(user_id, error_message)
            else:
                await message.reply(error_message)
            return
            
        await GenerateImage.waiting_for_prompt.set()
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel"))
        
        prompt_message = (
            "🎨 Rasm uchun tavsif yuboring\n\n"
            "Masalan:\n"
            "• a beautiful sunset over mountains\n"
            "• a cute cat playing with yarn\n"
            "• an astronaut riding a horse on mars"
        )
        
        if isinstance(message_or_callback, types.CallbackQuery):
            await bot.send_message(user_id, prompt_message, reply_markup=keyboard)
        else:
            await message.reply(prompt_message, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in process_generate: {str(e)}\n{traceback.format_exc()}")
        error_message = "❌ Tizimda xatolik yuz berdi"
        if isinstance(message_or_callback, types.CallbackQuery):
            await bot.send_message(message_or_callback.from_user.id, error_message)
        else:
            await message.reply(error_message)

@dp.callback_query_handler(lambda c: c.data == 'cancel', state='*')
async def cancel_handler(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        current_state = await state.get_state()
        if current_state is not None:
            try:
                await state.storage.set_state(chat=callback_query.message.chat.id, user=callback_query.from_user.id, state=None)
                await state.storage.set_data(chat=callback_query.message.chat.id, user=callback_query.from_user.id, data={})
                await state.storage.reset_bucket(chat=callback_query.message.chat.id, user=callback_query.from_user.id)
            except Exception as e:
                logger.error(f"Error resetting state: {str(e)}\n{traceback.format_exc()}")
        
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "✅ Amal bekor qilindi")
        
        # Try to delete the message with the cancel button
        try:
            await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        except Exception as e:
            logger.error(f"Error deleting message: {str(e)}")
            
    except Exception as e:
        logger.error(f"Error in cancel_handler: {str(e)}\n{traceback.format_exc()}")
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "❌ Tizimda xatolik yuz berdi")

@dp.message_handler(state=GenerateImage.waiting_for_prompt)
async def process_prompt(message: types.Message, state: FSMContext):
    status_message = None
    try:
        # Generate new image
        status_message = await message.reply("🎨 Rasm yaratilmoqda...")
        
        logger.info(f"Starting image generation for user {message.from_user.id} with prompt: {message.text}")
        result = generate_image_with_leonardo(message.text)
        
        if result and 'image_url' in result:
            logger.info(f"Image generated successfully, downloading from URL: {result['image_url']}")
            # Download and send image
            image_response = requests.get(result['image_url'])
            if image_response.status_code == 200:
                # Save image to temporary file
                temp_path = f"temp_{message.from_user.id}.jpg"
                with open(temp_path, "wb") as f:
                    f.write(image_response.content)
                
                try:
                    # Send photo from file
                    with open(temp_path, "rb") as f:
                        sent_photo = await bot.send_photo(
                            message.chat.id,
                            f,
                            caption=f"🎨 Prompt: {message.text}\n\n"
                                   f"🤖 @{(await bot.me).username}"
                        )
                    
                    # Save to database
                    user = await db.get_user(message.from_user.id)
                    if user:
                        await db.add_image(
                            sent_photo.photo[-1].file_id,
                            user['id'],
                            message.text
                        )
                        logger.info(f"Image saved to database for user {message.from_user.id}")
                finally:
                    # Clean up temporary file
                    try:
                        os.remove(temp_path)
                    except Exception as e:
                        logger.error(f"Error removing temporary file: {str(e)}")
            else:
                logger.error(f"Failed to download image: {image_response.status_code} - {image_response.text}")
                await message.reply("❌ Rasm yuklab olishda xatolik yuz berdi")
        else:
            logger.error("No image_url in Leonardo API response")
            await message.reply("❌ Rasm yaratishda xatolik yuz berdi")
    except Exception as e:
        logger.error(f"Error in process_prompt: {str(e)}\n{traceback.format_exc()}")
        await message.reply("❌ Tizimda xatolik yuz berdi")
    finally:
        try:
            if status_message:
                await status_message.delete()
        except TelegramAPIError as e:
            logger.error(f"Error deleting status message: {str(e)}")
        
        try:
            current_state = await state.get_state()
            if current_state is not None:
                await state.storage.set_state(chat=message.chat.id, user=message.from_user.id, state=None)
                await state.storage.set_data(chat=message.chat.id, user=message.from_user.id, data={})
                await state.storage.reset_bucket(chat=message.chat.id, user=message.from_user.id)
        except Exception as e:
            logger.error(f"Error finishing state for user {message.from_user.id}: {str(e)}\n{traceback.format_exc()}")

@dp.message_handler(commands=['myimages'])
@dp.callback_query_handler(lambda c: c.data == 'my_images')
async def show_user_images(message_or_callback: types.Message | types.CallbackQuery):
    try:
        user_id = message_or_callback.from_user.id
        user = await db.get_user(user_id)
        
        if not user:
            error_message = "❌ Foydalanuvchi topilmadi"
            if isinstance(message_or_callback, types.CallbackQuery):
                await bot.answer_callback_query(message_or_callback.id)
                await bot.send_message(user_id, error_message)
            else:
                await message_or_callback.reply(error_message)
            return
        
        images = await db.get_user_images(user['id'])
        
        if not images:
            no_images_message = "🖼 Sizda hali saqlangan rasmlar yo'q"
            if isinstance(message_or_callback, types.CallbackQuery):
                await bot.answer_callback_query(message_or_callback.id)
                await bot.send_message(user_id, no_images_message)
            else:
                await message_or_callback.reply(no_images_message)
            return
            
        if isinstance(message_or_callback, types.CallbackQuery):
            await bot.answer_callback_query(message_or_callback.id)
        
        for image in images:
            created_at = image['created_at'].replace(tzinfo=None) if image['created_at'] else datetime.now()
            caption = (
                f"🎨 Prompt: {image['prompt']}\n"
                f"📅 Sana: {created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                f"🤖 @{(await bot.me).username}"
            )
            
            # Send each image with caption
            if isinstance(message_or_callback, types.CallbackQuery):
                await bot.send_photo(user_id, image['file_id'], caption=caption)
            else:
                await bot.send_photo(message_or_callback.chat.id, image['file_id'], caption=caption)
                
    except Exception as e:
        logger.error(f"Error in show_user_images: {str(e)}\n{traceback.format_exc()}")
        error_message = "❌ Tizimda xatolik yuz berdi"
        if isinstance(message_or_callback, types.CallbackQuery):
            await bot.send_message(message_or_callback.from_user.id, error_message)
        else:
            await message_or_callback.reply(error_message)

@dp.callback_query_handler(lambda c: c.data == 'my_images')
async def show_user_images(callback_query: types.CallbackQuery):
    try:
        user = await db.get_user(callback_query.from_user.id)
        images = await db.get_user_images(user['id'])
        
        if not images:
            await bot.answer_callback_query(callback_query.id)
            await bot.send_message(
                callback_query.from_user.id,
                "🖼 Sizda hali rasmlar yo'q"
            )
            return

        await bot.answer_callback_query(callback_query.id)
        for image in images:
            await bot.send_photo(
                callback_query.from_user.id,
                image['file_id'],
                caption=f"🎨 Prompt: {image['prompt']}\n"
                       f"📅 Sana: {image['created_at'].strftime('%Y-%m-%d %H:%M')}"
            )
    except Exception as e:
        logger.error(f"Error in show_user_images: {str(e)}\n{traceback.format_exc()}")
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(
            callback_query.from_user.id,
            "❌ Tizimda xatolik yuz berdi"
        )

# Admin handlers
@dp.message_handler(commands=['admin'])
async def admin_panel(message: types.Message):
    try:
        user = await db.get_user(message.from_user.id)
        if not user or not user['is_admin']:
            await message.reply("❌ Bu buyruq faqat adminlar uchun")
            return
            
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("👥 Adminlar ro'yxati", callback_data="list_admins"),
            InlineKeyboardButton("➕ Admin qo'shish", callback_data="add_admin"),
            InlineKeyboardButton("➖ Adminni o'chirish", callback_data="remove_admin"),
            InlineKeyboardButton("🚫 Bloklash", callback_data="block_user"),
            InlineKeyboardButton("✅ Blokdan chiqarish", callback_data="unblock_user")
        )
        
        await message.reply("👨‍💼 Admin paneli:", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in admin_panel: {str(e)}\n{traceback.format_exc()}")
        await message.reply("❌ Tizimda xatolik yuz berdi")

@dp.callback_query_handler(lambda c: c.data == 'list_admins')
async def list_admins(callback_query: types.CallbackQuery):
    try:
        user = await db.get_user(callback_query.from_user.id)
        if not user or not user['is_admin']:
            await bot.answer_callback_query(callback_query.id, "❌ Bu buyruq faqat adminlar uchun")
            return
            
        admins = await db.get_all_admins()
        if not admins:
            await bot.answer_callback_query(callback_query.id)
            await bot.send_message(callback_query.from_user.id, "👥 Adminlar ro'yxati bo'sh")
            return
            
        admin_list = "👥 Adminlar ro'yxati:\n\n"
        for admin in admins:
            admin_list += f"• {admin['username'] or f'ID: {admin['telegram_id']}'}\n"
            
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, admin_list)
    except Exception as e:
        logger.error(f"Error in list_admins: {str(e)}\n{traceback.format_exc()}")
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "❌ Tizimda xatolik yuz berdi")

# Admin states
class AdminStates(StatesGroup):
    waiting_for_admin_id = State()
    waiting_for_user_id = State()

@dp.callback_query_handler(lambda c: c.data == 'add_admin')
async def add_admin_start(callback_query: types.CallbackQuery):
    try:
        user = await db.get_user(callback_query.from_user.id)
        if not user or not user['is_admin']:
            await bot.answer_callback_query(callback_query.id, "❌ Bu buyruq faqat adminlar uchun")
            return
            
        await AdminStates.waiting_for_admin_id.set()
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel"))
        
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(
            callback_query.from_user.id,
            "📝 Yangi admin ID raqamini yuboring:",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in add_admin_start: {str(e)}\n{traceback.format_exc()}")
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "❌ Tizimda xatolik yuz berdi")

@dp.message_handler(state=AdminStates.waiting_for_admin_id)
async def add_admin_finish(message: types.Message, state: FSMContext):
    try:
        user = await db.get_user(message.from_user.id)
        if not user or not user['is_admin']:
            await message.reply("❌ Bu buyruq faqat adminlar uchun")
            return
            
        try:
            new_admin_id = int(message.text)
        except ValueError:
            await message.reply("❌ Noto'g'ri ID format. Raqam kiriting.")
            return
            
        new_admin = await db.get_user(new_admin_id)
        if not new_admin:
            await message.reply("❌ Bunday foydalanuvchi topilmadi")
            return
            
        await db.set_admin(new_admin_id, True)
        await message.reply("✅ Admin muvaffaqiyatli qo'shildi")
    except Exception as e:
        logger.error(f"Error in add_admin_finish: {str(e)}\n{traceback.format_exc()}")
        await message.reply("❌ Tizimda xatolik yuz berdi")
    finally:
        await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'remove_admin')
async def remove_admin_start(callback_query: types.CallbackQuery):
    try:
        user = await db.get_user(callback_query.from_user.id)
        if not user or not user['is_admin']:
            await bot.answer_callback_query(callback_query.id, "❌ Bu buyruq faqat adminlar uchun")
            return
            
        await AdminStates.waiting_for_admin_id.set()
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel"))
        
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(
            callback_query.from_user.id,
            "📝 O'chirilishi kerak bo'lgan admin ID raqamini yuboring:",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in remove_admin_start: {str(e)}\n{traceback.format_exc()}")
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "❌ Tizimda xatolik yuz berdi")

@dp.message_handler(state=AdminStates.waiting_for_admin_id)
async def remove_admin_finish(message: types.Message, state: FSMContext):
    try:
        user = await db.get_user(message.from_user.id)
        if not user or not user['is_admin']:
            await message.reply("❌ Bu buyruq faqat adminlar uchun")
            return
            
        try:
            admin_id = int(message.text)
        except ValueError:
            await message.reply("❌ Noto'g'ri ID format. Raqam kiriting.")
            return
            
        admin = await db.get_user(admin_id)
        if not admin:
            await message.reply("❌ Bunday foydalanuvchi topilmadi")
            return
            
        if not admin['is_admin']:
            await message.reply("❌ Bu foydalanuvchi admin emas")
            return
            
        if str(admin_id) == os.getenv("ADMIN_ID"):
            await message.reply("❌ Asosiy adminni o'chirib bo'lmaydi")
            return
            
        await db.set_admin(admin_id, False)
        await message.reply("✅ Admin muvaffaqiyatli o'chirildi")
    except Exception as e:
        logger.error(f"Error in remove_admin_finish: {str(e)}\n{traceback.format_exc()}")
        await message.reply("❌ Tizimda xatolik yuz berdi")
    finally:
        await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'block_user')
async def block_user_start(callback_query: types.CallbackQuery):
    try:
        user = await db.get_user(callback_query.from_user.id)
        if not user or not user['is_admin']:
            await bot.answer_callback_query(callback_query.id, "❌ Bu buyruq faqat adminlar uchun")
            return
            
        await AdminStates.waiting_for_user_id.set()
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel"))
        
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(
            callback_query.from_user.id,
            "📝 Bloklanishi kerak bo'lgan foydalanuvchi ID raqamini yuboring:",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in block_user_start: {str(e)}\n{traceback.format_exc()}")
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "❌ Tizimda xatolik yuz berdi")

@dp.message_handler(state=AdminStates.waiting_for_user_id)
async def block_user_finish(message: types.Message, state: FSMContext):
    try:
        user = await db.get_user(message.from_user.id)
        if not user or not user['is_admin']:
            await message.reply("❌ Bu buyruq faqat adminlar uchun")
            return
            
        try:
            user_id = int(message.text)
        except ValueError:
            await message.reply("❌ Noto'g'ri ID format. Raqam kiriting.")
            return
            
        target_user = await db.get_user(user_id)
        if not target_user:
            await message.reply("❌ Bunday foydalanuvchi topilmadi")
            return
            
        if target_user['is_admin']:
            await message.reply("❌ Adminni bloklash mumkin emas")
            return
            
        await db.set_blocked(user_id, True)
        await message.reply("✅ Foydalanuvchi muvaffaqiyatli bloklandi")
    except Exception as e:
        logger.error(f"Error in block_user_finish: {str(e)}\n{traceback.format_exc()}")
        await message.reply("❌ Tizimda xatolik yuz berdi")
    finally:
        await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'unblock_user')
async def unblock_user_start(callback_query: types.CallbackQuery):
    try:
        user = await db.get_user(callback_query.from_user.id)
        if not user or not user['is_admin']:
            await bot.answer_callback_query(callback_query.id, "❌ Bu buyruq faqat adminlar uchun")
            return
            
        await AdminStates.waiting_for_user_id.set()
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel"))
        
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(
            callback_query.from_user.id,
            "📝 Blokdan chiqarilishi kerak bo'lgan foydalanuvchi ID raqamini yuboring:",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in unblock_user_start: {str(e)}\n{traceback.format_exc()}")
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "❌ Tizimda xatolik yuz berdi")

@dp.message_handler(state=AdminStates.waiting_for_user_id)
async def unblock_user_finish(message: types.Message, state: FSMContext):
    try:
        user = await db.get_user(message.from_user.id)
        if not user or not user['is_admin']:
            await message.reply("❌ Bu buyruq faqat adminlar uchun")
            return
            
        try:
            user_id = int(message.text)
        except ValueError:
            await message.reply("❌ Noto'g'ri ID format. Raqam kiriting.")
            return
            
        target_user = await db.get_user(user_id)
        if not target_user:
            await message.reply("❌ Bunday foydalanuvchi topilmadi")
            return
            
        if not target_user['is_blocked']:
            await message.reply("❌ Bu foydalanuvchi bloklanmagan")
            return
            
        await db.set_blocked(user_id, False)
        await message.reply("✅ Foydalanuvchi muvaffaqiyatli blokdan chiqarildi")
    except Exception as e:
        logger.error(f"Error in unblock_user_finish: {str(e)}\n{traceback.format_exc()}")
        await message.reply("❌ Tizimda xatolik yuz berdi")
    finally:
        await state.finish()

# Admin commands
@dp.message_handler(commands=['admin'], user_id=int(os.getenv("ADMIN_ID")))
async def admin_panel(message: types.Message):
    try:
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton("👥 Foydalanuvchilarni boshqarish", callback_data="manage_users"),
            InlineKeyboardButton("👮‍♂️ Adminlar ro'yxati", callback_data="list_admins")
        )
        await message.reply("👨‍💼 Admin panel:", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in admin_panel: {str(e)}\n{traceback.format_exc()}")
        await message.reply("❌ Tizimda xatolik yuz berdi")

@dp.callback_query_handler(lambda c: c.data == "list_admins", user_id=int(os.getenv("ADMIN_ID")))
async def list_admins(callback_query: types.CallbackQuery):
    try:
        admins = await db.get_all_admins()
        
        if not admins:
            await bot.answer_callback_query(callback_query.id)
            await bot.send_message(
                callback_query.from_user.id,
                "👮‍♂️ Hozircha adminlar yo'q"
            )
            return

        keyboard = InlineKeyboardMarkup(row_width=1)
        admin_text = "👮‍♂️ Adminlar ro'yxati:\n\n"
        
        for admin in admins:
            admin_text += f"• {admin['username']} (ID: {admin['telegram_id']})"
            admin_text += " 🚫" if admin['is_blocked'] else " ✅"
            admin_text += "\n"
            
            # Don't add block/unblock button for main admin
            if str(admin['telegram_id']) != os.getenv("ADMIN_ID"):
                action = "unblock" if admin['is_blocked'] else "block"
                keyboard.add(
                    InlineKeyboardButton(
                        f"{'🔓 Blokdan chiqarish' if admin['is_blocked'] else '🔒 Bloklash'}: {admin['username']}",
                        callback_data=f"toggle_block_{action}_{admin['telegram_id']}"
                    )
                )
        
        keyboard.add(InlineKeyboardButton("◀️ Orqaga", callback_data="admin_back"))
        
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(
            callback_query.from_user.id,
            admin_text,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in list_admins: {str(e)}\n{traceback.format_exc()}")
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(
            callback_query.from_user.id,
            "❌ Tizimda xatolik yuz berdi"
        )

@dp.callback_query_handler(
    lambda c: c.data.startswith("toggle_block_"),
    user_id=int(os.getenv("ADMIN_ID"))
)
async def toggle_user_block(callback_query: types.CallbackQuery):
    try:
        _, action, user_id = callback_query.data.split("_")
        block_status = action == "block"
        
        await db.toggle_user_block(int(user_id), block_status)
        
        await bot.answer_callback_query(
            callback_query.id,
            f"Foydalanuvchi {'bloklandi' if block_status else 'blokdan chiqarildi'}"
        )
        
        # Update the admin list
        await list_admins(callback_query)
    except Exception as e:
        logger.error(f"Error in toggle_user_block: {str(e)}\n{traceback.format_exc()}")
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(
            callback_query.from_user.id,
            "❌ Tizimda xatolik yuz berdi"
        )

@dp.callback_query_handler(lambda c: c.data == "admin_back", user_id=int(os.getenv("ADMIN_ID")))
async def admin_back(callback_query: types.CallbackQuery):
    try:
        await bot.answer_callback_query(callback_query.id)
        await admin_panel(await bot.send_message(
            callback_query.from_user.id,
            "👨‍💼 Admin panel:"
        ))
    except Exception as e:
        logger.error(f"Error in admin_back: {str(e)}\n{traceback.format_exc()}")
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(
            callback_query.from_user.id,
            "❌ Tizimda xatolik yuz berdi"
        )

# Add message handler middleware to check if user is blocked
class MessageMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message: types.Message, data: dict):
        if message.from_user.id != int(os.getenv("ADMIN_ID")):
            is_blocked = await db.is_user_blocked(message.from_user.id)
            if is_blocked:
                await message.reply("⛔️ Kechirasiz, siz bloklangansiz")
                raise CancelHandler()

# Register middleware
dp.middleware.setup(MessageMiddleware())

async def on_startup(dp):
    try:
        await db.create_pool()
        await db.create_tables()
        await setup_bot_commands(bot)
        logging.info("Bot started")
    except Exception as e:
        logger.error(f"Error in on_startup: {str(e)}\n{traceback.format_exc()}")

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
