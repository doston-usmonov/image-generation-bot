# Leonardo AI Image Generation Bot

Telegram bot that generates images using Leonardo AI API.

## Features

- 🎨 Generate images from text descriptions
- 🖼 Save and manage generated images
- 👥 User management system
- 📊 Usage statistics
- 🔒 Admin panel with user control

## Installation

1. Repository ni clone qiling:
```bash
git clone https://github.com/doston-usmonov/image-generation-bot
cd image-generation-bot
```

2. Virtual muhit yarating va faollashtiring:
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

3. Kerakli kutubxonalarni o'rnating:
```bash
pip install -r requirements.txt
```

4. `.env.example` faylidan `.env` fayl yarating va sozlamalarni kiriting:
```bash
cp .env.example .env
```

5. `.env` faylini tahrirlang va quyidagi ma'lumotlarni kiriting:
```
TELEGRAM_TOKEN=your_telegram_bot_token
LEONARDO_API_KEY=your_leonardo_api_key
DATABASE_URL=postgresql://username:password@localhost:5432/dbname
ADMIN_ID=your_telegram_id
```

## Ishga tushirish

```bash
python bot.py
```

## Bot buyruqlari

- `/start` - Botni ishga tushirish
- `/help` - Yordam
- `/generate` - Yangi rasm yaratish
- `/myimages` - Mening rasmlarim
- `/stats` - Statistika (faqat adminlar uchun)
- `/admin` - Admin paneli (faqat adminlar uchun)

## Admin paneli funksiyalari

- 👥 Adminlar ro'yxatini ko'rish
- ➕ Admin qo'shish
- ➖ Adminni o'chirish
- 🚫 Foydalanuvchini bloklash
- ✅ Foydalanuvchini blokdan chiqarish
- 📊 Bot statistikasini ko'rish

## Ma'lumotlar bazasi

Bot PostgreSQL ma'lumotlar bazasidan foydalanadi. Bazada quyidagi jadvallar mavjud:

- `users` - Foydalanuvchilar ma'lumotlari
- `images` - Yaratilgan rasmlar

## Xavfsizlik

- Muhim ma'lumotlar (API kalitlar, token) `.env` faylida saqlanadi
- Admin huquqlari faqat ADMIN_ID ga ega bo'lgan foydalanuvchiga beriladi
- Bloklangan foydalanuvchilar botdan foydalana olmaydi

## Litsenziya

MIT License
