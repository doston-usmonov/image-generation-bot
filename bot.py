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

💡 Masalan: "a beautiful sunset over mountains" yubi "a cute cat playing with yarn"

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
            error_data = response.json()
            error_message = error_data.get('error', 'Unknown error occurred')
            logger.error(f"Leonardo API error: {response.status_code} - {response.text}")
            return {'error': error_message}
    except Exception as e:
        logger.error(f"Error in generate_image_with_leonardo: {str(e)}\n{traceback.format_exc()}")
        return {'error': str(e)}

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
                await message_or_callback.reply(error_message)
            return
            
        if user['is_blocked']:
            error_message = "❌ Siz bloklangansiz"
            if isinstance(message_or_callback, types.CallbackQuery):
                await bot.send_message(user_id, error_message)
            else:
                await message_or_callback.reply(error_message)
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
            await message_or_callback.reply(prompt_message, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in process_generate: {str(e)}\n{traceback.format_exc()}")
        error_message = "❌ Tizimda xatolik yuz berdi"
        if isinstance(message_or_callback, types.CallbackQuery):
            await bot.send_message(message_or_callback.from_user.id, error_message)
        else:
            await message_or_callback.reply(error_message)

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
    try:
        prompt = message.text
        user_id = message.from_user.id
        
        logger.info(f"Starting image generation for user {user_id} with prompt: {prompt}")
        
        try:
            await state.finish()
        except Exception as e:
            logger.error(f"Error clearing state: {e}")
            # Continue execution even if state cleanup fails
            
        # Send "generating" message
        status_message = await message.reply("🎨 Rasm generatsiya qilinmoqda...")
        
        # Generate image
        logger.info(f"Sending generation request to Leonardo API with prompt: {prompt}")
        result = generate_image_with_leonardo(prompt)

        if result and 'image_url' in result:
            # Download the image
            image_url = result['image_url']
            image_response = requests.get(image_url)
            
            if image_response.status_code == 200:
                # Send the image
                sent_photo = await message.reply_photo(
                    image_response.content,
                    caption=f"Rasm @{(await bot.me).username} yordamida yaratildi"
                )

                # Save image to database
                user = await db.get_user(user_id)
                if user:
                    await db.add_image(
                        sent_photo.photo[-1].file_id,
                        user['id'],
                        prompt
                    )
                
                await status_message.delete()
            else:
                logger.error(f"Failed to download image: {image_response.status_code} - {image_response.text}")
                await status_message.edit_text("❌ Rasm yuklab olishda xatolik yuz berdi")
        elif result and 'error' in result:
            await status_message.edit_text(f"❌ Xatolik: {result['error']}")
        else:
            logger.error("No image_url in Leonardo API response")
            await status_message.edit_text("❌ Rasm yaratishda xatolik yuz berdi")

    except Exception as e:
        logger.error(f"Error in process_prompt: {str(e)}\n{traceback.format_exc()}")
        await message.reply("❌ Tizimda xatolik yuz berdi")
    finally:
        await state.finish()

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
    user = await db.get_user(message.from_user.id)
    if not user or not user['is_admin']:
        await message.reply("❌ Bu buyruq faqat adminlar uchun")
        return

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="manage_users"),
        InlineKeyboardButton("👮‍♂️ Adminlar", callback_data="list_admins"),
        InlineKeyboardButton("📊 Statistika", callback_data="show_stats")
    )
    
    await message.reply("🔧 Admin paneli:", reply_markup=keyboard)

# Admin states
class AdminStates(StatesGroup):
    waiting_for_username = State()

@dp.callback_query_handler(lambda c: c.data == "add_admin")
async def add_admin_start(callback_query: types.CallbackQuery):
    user = await db.get_user(callback_query.from_user.id)
    if not user or not user['is_admin']:
        await callback_query.answer("❌ Bu funksiya faqat adminlar uchun", show_alert=True)
        return

    await AdminStates.waiting_for_username.set()
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Bekor qilish", callback_data="admin_back"))
    
    await callback_query.message.edit_text(
        "✏️ Admin qilmoqchi bo'lgan foydalanuvchining <b>username</b>ini yuboring:\n\n"
        "<i>Masalan: @username</i>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@dp.message_handler(state=AdminStates.waiting_for_username)
async def process_admin_username(message: types.Message, state: FSMContext):
    try:
        # Username formatini tekshirish
        username = message.text.strip()
        if username.startswith('@'):
            username = username[1:]
        
        # Foydalanuvchini bazadan topish
        user = await db.get_user_by_username(username)
        if not user:
            await message.reply(
                "❌ Bunday foydalanuvchi topilmadi.\n\n"
                "✏️ Foydalanuvchi <b>username</b>ini to'g'ri yuboring yoki /cancel buyrug'ini bosing.",
                parse_mode="HTML"
            )
            return
        
        # Admin huquqini berish
        if user['is_admin']:
            await message.reply("❌ Bu foydalanuvchi allaqachon admin!")
        else:
            success = await db.set_admin(user['telegram_id'], True)
            if success:
                await message.reply(f"✅ {username} admin qilib tayinlandi!")
            else:
                await message.reply("❌ Xatolik yuz berdi. Qayta urinib ko'ring.")
        
        await state.finish()
        
        # Admin panelga qaytish
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="manage_users"),
            InlineKeyboardButton("👮‍♂️ Adminlar", callback_data="list_admins"),
            InlineKeyboardButton("📊 Statistika", callback_data="show_stats")
        )
        await message.reply("🔧 Admin paneli:", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in process_admin_username: {str(e)}\n{traceback.format_exc()}")
        await message.reply("❌ Xatolik yuz berdi. Qayta urinib ko'ring.")
        await state.finish()

@dp.callback_query_handler(lambda c: c.data == "remove_admin")
async def remove_admin_start(callback_query: types.CallbackQuery):
    user = await db.get_user(callback_query.from_user.id)
    if not user or not user['is_admin']:
        await callback_query.answer("❌ Bu funksiya faqat adminlar uchun", show_alert=True)
        return

    await AdminStates.waiting_for_username.set()
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Bekor qilish", callback_data="admin_back"))
    
    await callback_query.message.edit_text(
        "✏️ Admin huquqini olib tashlamoqchi bo'lgan foydalanuvchining <b>username</b>ini yuboring:\n\n"
        "<i>Masalan: @username</i>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@dp.message_handler(state=AdminStates.waiting_for_username)
async def process_remove_admin(message: types.Message, state: FSMContext):
    try:
        # Username formatini tekshirish
        username = message.text.strip()
        if username.startswith('@'):
            username = username[1:]
        
        # Foydalanuvchini bazadan topish
        user = await db.get_user_by_username(username)
        if not user:
            await message.reply(
                "❌ Bunday foydalanuvchi topilmadi.\n\n"
                "✏️ Foydalanuvchi <b>username</b>ini to'g'ri yuboring yoki /cancel buyrug'ini bosing.",
                parse_mode="HTML"
            )
            return
        
        # Admin huquqini olib tashlash
        if not user['is_admin']:
            await message.reply("❌ Bu foydalanuvchi admin emas!")
        else:
            # O'zini o'zi admin huquqidan mahrum qilishni oldini olish
            if user['telegram_id'] == message.from_user.id:
                await message.reply("❌ Siz o'zingizni admin huquqidan mahrum qila olmaysiz!")
                return
            
            success = await db.set_admin(user['telegram_id'], False)
            if success:
                await message.reply(f"✅ {username} admin huquqidan mahrum qilindi!")
            else:
                await message.reply("❌ Xatolik yuz berdi. Qayta urinib ko'ring.")
        
        await state.finish()
        
        # Admin panelga qaytish
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="manage_users"),
            InlineKeyboardButton("👮‍♂️ Adminlar", callback_data="list_admins"),
            InlineKeyboardButton("📊 Statistika", callback_data="show_stats")
        )
        await message.reply("🔧 Admin paneli:", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in process_remove_admin: {str(e)}\n{traceback.format_exc()}")
        await message.reply("❌ Xatolik yuz berdi. Qayta urinib ko'ring.")
        await state.finish()

@dp.callback_query_handler(lambda c: c.data == "admin_back", state="*")
async def admin_back_with_state(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        current_state = await state.get_state()
        if current_state:
            try:
                await state.finish()
            except Exception as e:
                logger.error(f"Error clearing state: {e}")
                # Continue execution even if state cleanup fails
    except Exception as e:
        logger.error(f"Error in admin_back_with_state: {e}")
    
    await admin_back(callback_query)

# Admin commands
@dp.message_handler(commands=['admin'], user_id=int(os.getenv("ADMIN_ID")))
async def admin_panel(message: types.Message):
    try:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("👥 Foydalanuvchilarni boshqarish", callback_data="manage_users"))
        keyboard.add(InlineKeyboardButton("👮‍♂️ Adminlar ro'yxati", callback_data="list_admins"))
        
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
            await bot.edit_message_text(
                "👮‍♂️ Hozircha adminlar yo'q",
                callback_query.message.chat.id,
                callback_query.message.message_id,
                reply_markup=get_admin_keyboard()
            )
            return

        admin_text = "👮‍♂️ Adminlar ro'yxati:\n\n"
        for admin in admins:
            username = admin['username'] if admin['username'] else f"ID: {admin['telegram_id']}"
            status = "🚫" if admin.get('is_blocked') else "✅"
            admin_text += f"• {username} {status}\n"

        keyboard = get_admin_keyboard()
        
        await bot.answer_callback_query(callback_query.id)
        await bot.edit_message_text(
            admin_text,
            callback_query.message.chat.id,
            callback_query.message.message_id,
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
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("👥 Foydalanuvchilarni boshqarish", callback_data="manage_users"))
        keyboard.add(InlineKeyboardButton("👮‍♂️ Adminlar ro'yxati", callback_data="list_admins"))
        
        await bot.answer_callback_query(callback_query.id)
        await bot.edit_message_text(
            "👨‍💼 Admin panel:",
            callback_query.message.chat.id,
            callback_query.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in admin_back: {str(e)}\n{traceback.format_exc()}")
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(
            callback_query.from_user.id,
            "❌ Tizimda xatolik yuz berdi"
        )

@dp.callback_query_handler(lambda c: c.data == "manage_users", user_id=int(os.getenv("ADMIN_ID")))
async def manage_users(callback_query: types.CallbackQuery):
    try:
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton("🚫 Foydalanuvchini bloklash", callback_data="block_user"),
            InlineKeyboardButton("✅ Foydalanuvchini blokdan chiqarish", callback_data="unblock_user"),
            InlineKeyboardButton("📊 Statistika", callback_data="show_stats"),
            InlineKeyboardButton("◀️ Orqaga", callback_data="admin_back")
        )
        
        await bot.answer_callback_query(callback_query.id)
        await bot.edit_message_text(
            "👥 Foydalanuvchilarni boshqarish paneli:",
            callback_query.message.chat.id,
            callback_query.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in manage_users: {str(e)}\n{traceback.format_exc()}")
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "❌ Xatolik yuz berdi")

@dp.callback_query_handler(lambda c: c.data == "show_stats", user_id=int(os.getenv("ADMIN_ID")))
async def show_stats_callback(callback_query: types.CallbackQuery):
    try:
        stats = await db.get_stats()
        
        stats_text = "📊 Bot statistikasi:\n\n"
        stats_text += f"👥 Jami foydalanuvchilar: {stats['total_users']}\n"
        stats_text += f"👤 Faol foydalanuvchilar: {stats['active_users']}\n"
        stats_text += f"🖼 Jami yaratilgan rasmlar: {stats['total_images']}\n"
        stats_text += f"🎨 Bugun yaratilgan rasmlar: {stats['images_today']}\n"
        stats_text += f"🚫 Bloklangan foydalanuvchilar: {stats['blocked_users']}\n"
        stats_text += f"👮‍♂️ Adminlar soni: {stats['admin_count']}\n"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Orqaga", callback_data="manage_users"))
        
        await bot.answer_callback_query(callback_query.id)
        await bot.edit_message_text(
            stats_text,
            callback_query.message.chat.id,
            callback_query.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in show_stats_callback: {str(e)}\n{traceback.format_exc()}")
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(
            callback_query.from_user.id,
            "❌ Tizimda xatolik yuz berdi"
        )

def get_admin_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("➕ Admin qo'shish", callback_data="add_admin"),
        types.InlineKeyboardButton("➖ Adminni o'chirish", callback_data="remove_admin")
    )
    keyboard.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back"))
    return keyboard

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
