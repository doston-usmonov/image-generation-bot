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

4. PostgreSQL o'rnatish va sozlash:

Ubuntu/Debian:
```bash
# PostgreSQL o'rnatish
sudo apt update
sudo apt install postgresql postgresql-contrib

# PostgreSQL serverini ishga tushirish
sudo systemctl start postgresql
sudo systemctl enable postgresql

# PostgreSQL ga kirish
sudo -u postgres psql

# Ma'lumotlar bazasini yaratish
CREATE DATABASE leonardo_bot;

# Foydalanuvchi yaratish va huquqlar berish
CREATE USER botuser WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE leonardo_bot TO botuser;

# Chiqish
\q
```

macOS (Homebrew orqali):
```bash
# PostgreSQL o'rnatish
brew install postgresql

# PostgreSQL serverini ishga tushirish
brew services start postgresql

# Ma'lumotlar bazasini yaratish
createdb leonardo_bot

# Foydalanuvchi yaratish va huquqlar berish
psql leonardo_bot
CREATE USER botuser WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE leonardo_bot TO botuser;
\q
```

5. `.env.example` faylidan `.env` fayl yarating va sozlamalarni kiriting:
```bash
cp .env.example .env
```

6. `.env` faylini tahrirlang va quyidagi ma'lumotlarni kiriting:
```
TELEGRAM_TOKEN=your_telegram_bot_token
LEONARDO_API_KEY=your_leonardo_api_key
DATABASE_URL=postgresql://botuser:your_password@localhost:5432/leonardo_bot
ADMIN_ID=your_telegram_id
```

## Ma'lumotlar bazasi

Bot PostgreSQL ma'lumotlar bazasidan foydalanadi. Bazada quyidagi jadvallar mavjud:

### Users jadvali
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    username VARCHAR(255),
    is_admin BOOLEAN DEFAULT FALSE,
    is_blocked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Images jadvali
```sql
CREATE TABLE images (
    id SERIAL PRIMARY KEY,
    file_id VARCHAR(255),
    user_id INTEGER REFERENCES users(id),
    prompt TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
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

## Xavfsizlik

- Muhim ma'lumotlar (API kalitlar, token) `.env` faylida saqlanadi
- Admin huquqlari faqat ADMIN_ID ga ega bo'lgan foydalanuvchiga beriladi
- Bloklangan foydalanuvchilar botdan foydalana olmaydi
- PostgreSQL foydalanuvchisi minimal kerakli huquqlarga ega

## Muammolarni hal qilish

### Ma'lumotlar bazasi xatoliklari

1. "database does not exist" xatoligi:
```bash
# Ma'lumotlar bazasini yarating
sudo -u postgres createdb leonardo_bot
```

2. "role does not exist" xatoligi:
```bash
# PostgreSQL ga kirib
sudo -u postgres psql

# Foydalanuvchini qaytadan yarating
CREATE USER botuser WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE leonardo_bot TO botuser;
```

3. "permission denied" xatoligi:
```bash
# PostgreSQL ga kirib
sudo -u postgres psql

# Foydalanuvchi huquqlarini tekshiring
\du botuser

# Kerakli huquqlarni bering
GRANT ALL PRIVILEGES ON DATABASE leonardo_bot TO botuser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO botuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO botuser;
```

## Serverda doimiy ishlashi uchun sozlash

### 1. Systemd service yaratish

```bash
# Systemd service faylini yaratish
sudo nano /etc/systemd/system/leonardo-bot.service
```

Service faylining tarkibi:
```ini
[Unit]
Description=Leonardo AI Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=your_username
Group=your_username
WorkingDirectory=/var/www/bots/leonardo
Environment=PYTHONPATH=/var/www/bots/leonardo
ExecStart=/var/www/bots/leonardo/venv/bin/python3 bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Serviceni ishga tushirish

```bash
# Systemd konfiguratsiyasini qayta yuklash
sudo systemctl daemon-reload

# Serviceni ishga tushirish
sudo systemctl start leonardo-bot

# Serviceni avto-ishga tushirishni yoqish
sudo systemctl enable leonardo-bot

# Service statusini tekshirish
sudo systemctl status leonardo-bot
```

### 3. Loglarni ko'rish

```bash
# Service loglarini ko'rish
sudo journalctl -u leonardo-bot -f

# Bot loglarini ko'rish
tail -f /var/www/bots/leonardo/bot.log
```

### 4. Service boshqaruvi

```bash
# Serviceni to'xtatish
sudo systemctl stop leonardo-bot

# Serviceni qayta ishga tushirish
sudo systemctl restart leonardo-bot

# Serviceni o'chirish
sudo systemctl disable leonardo-bot
```

### Supervisor orqali ishga tushirish

Agar systemd o'rniga Supervisor ishlatmoqchi bo'lsangiz:

1. Supervisor o'rnatish:
```bash
sudo apt update
sudo apt install supervisor
```

2. Bot konfiguratsiya faylini yaratish:
```bash
sudo nano /etc/supervisor/conf.d/leonardo-bot.conf
```

Konfiguratsiya fayli tarkibi:
```ini
[program:leonardo-bot]
directory=/var/www/bots/leonardo
command=/var/www/bots/leonardo/venv/bin/python3 bot.py
user=your_username
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/leonardo-bot.err.log
stdout_logfile=/var/log/supervisor/leonardo-bot.out.log
environment=
    PYTHONPATH="/var/www/bots/leonardo",
    PATH="/var/www/bots/leonardo/venv/bin"
```

3. Supervisor konfiguratsiyasini yangilash:
```bash
sudo supervisorctl reread
sudo supervisorctl update
```

4. Bot statusini tekshirish:
```bash
sudo supervisorctl status leonardo-bot
```

5. Bot boshqaruvi:
```bash
# Botni to'xtatish
sudo supervisorctl stop leonardo-bot

# Botni ishga tushirish
sudo supervisorctl start leonardo-bot

# Botni qayta ishga tushirish
sudo supervisorctl restart leonardo-bot
```

### Xavfsizlik maslahatlar

1. Bot uchun alohida foydalanuvchi yarating:
```bash
sudo useradd -r -s /bin/false leonardo-bot
sudo chown -R leonardo-bot:leonardo-bot /var/www/bots/leonardo
```

2. Fayllar uchun to'g'ri ruxsatlarni o'rnating:
```bash
chmod 644 /var/www/bots/leonardo/bot.py
chmod 600 /var/www/bots/leonardo/.env
```

3. Firewall sozlamalari:
```bash
sudo ufw allow ssh
sudo ufw allow https
sudo ufw allow postgresql
sudo ufw enable
```

## Litsenziya

MIT License
