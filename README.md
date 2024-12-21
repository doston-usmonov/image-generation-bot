# Leonardo AI Rasm Generatsiya Bot

Bu Telegram bot Leonardo AI API orqali rasmlar yaratish imkonini beradi.

## Xususiyatlar

- 🎨 Leonardo AI orqali rasmlar yaratish
- 💾 Yaratilgan rasmlarni saqlash va ko'rish
- 🔍 Avval yaratilgan rasmlarni qidirish
- 👥 Admin panel orqali foydalanuvchilarni boshqarish

## O'rnatish

1. Repository ni clone qiling:
```bash
git clone https://github.com/yourusername/leonardo-bot.git
cd leonardo-bot
```

2. Virtual muhit yarating va faollashtiring:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac uchun
# yoki
venv\Scripts\activate  # Windows uchun
```

3. Kerakli kutubxonalarni o'rnating:
```bash
pip install -r requirements.txt
```

4. `.env.example` faylini `.env` ga nusxalang va sozlamalarni kiriting:
```bash
cp .env.example .env
```

5. `.env` faylini tahrirlang va quyidagi ma'lumotlarni kiriting:
- `TELEGRAM_TOKEN`: Telegram Bot Token (@BotFather dan olinadi)
- `LEONARDO_API_KEY`: Leonardo AI API kaliti
- `DATABASE_URL`: PostgreSQL ma'lumotlar bazasi URL manzili
- `ADMIN_ID`: Asosiy admin Telegram ID raqami

6. PostgreSQL ma'lumotlar bazasini yarating:
```sql
CREATE DATABASE your_database_name;
```

7. Botni ishga tushiring:
```bash
python bot.py
```

## Foydalanish

1. Botni Telegramda toping
2. `/start` buyrug'ini yuboring
3. "🎨 Rasm yaratish" tugmasini bosing
4. Rasm uchun tavsif (prompt) yuboring
5. Bot rasm yaratib, sizga yuboradi

## Admin buyruqlari

- `/admin` - Admin panelni ochish (faqat admin uchun)

## Texnik tafsilotlar

- Python 3.8+
- aiogram 2.25.1
- PostgreSQL ma'lumotlar bazasi
- Leonardo AI API
