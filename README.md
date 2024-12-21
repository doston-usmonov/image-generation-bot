# Leonardo AI Telegram Bot

Leonardo.ai API yordamida rasmlar generatsiya qiluvchi va mavjud rasmlarni anime stiliga o'tkazuvchi Telegram bot.

## Asosiy funksiyalar

1. **Rasm generatsiya qilish**
   - Matn orqali rasm yaratish
   - Yuqori sifatli rasmlar
   - Turli xil uslublar

2. **Rasmni anime stiliga o'tkazish**
   - Mavjud rasmlarni anime stiliga o'tkazish
   - Studio Ghibli uslubida qayta ishlash
   - Yuqori sifatli natija

## O'rnatish

1. **Talab qilinadigan dasturlar**
   - Python 3.7+
   - pip (Python package manager)

2. **Repositoryni yuklab olish**
   ```bash
   git clone https://github.com/yourusername/leonardo-bot.git
   cd leonardo-bot
   ```

3. **Virtual muhit yaratish**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac uchun
   # Windows uchun: venv\Scripts\activate
   ```

4. **Kerakli kutubxonalarni o'rnatish**
   ```bash
   pip install -r requirements.txt
   ```

5. **Muhit o'zgaruvchilarini sozlash**
   - `config.env` faylini yarating
   ```env
   BOT_TOKEN=your_telegram_bot_token
   LEONARDO_API_KEY=your_leonardo_api_key
   ```

   - `BOT_TOKEN` olish uchun:
     1. Telegram-da [@BotFather](https://t.me/BotFather) ga murojaat qiling
     2. `/newbot` buyrug'ini yuboring
     3. Bot nomini va username-ini kiriting
     4. BotFather bergan token-ni `BOT_TOKEN` ga yozing

   - `LEONARDO_API_KEY` olish uchun:
     1. [Leonardo.ai](https://leonardo.ai/) saytiga kiring
     2. Ro'yxatdan o'ting
     3. API kalitini oling va `LEONARDO_API_KEY` ga yozing

## Ishga tushirish

```bash
python bot.py
```

## Botdan foydalanish

### 1. Rasm generatsiya qilish
- `/start` - Botni ishga tushirish
- `/generate_image` - Rasm generatsiya qilishni boshlash
- Rasm tavsifini ingliz tilida kiriting
- Bot sizga generatsiya qilingan rasmni yuboradi

### 2. Rasmni anime stiliga o'tkazish
- Botga istalgan rasmni yuboring
- Bot rasmni anime stiliga o'tkazib beradi
- Natijada Studio Ghibli uslubidagi rasm olinadi

## Texnik ma'lumotlar

### Rasm generatsiya parametrlari
- Rasm o'lchami: 512x512 piksel
- Guidance scale: 7
- Inference steps: 30
- Prompt magic: Yoqilgan
- Preset style: ANIME

### Anime stil parametrlari
- Model: Anime Pastel Model
- Image prompt weight: 0.7
- Studio Ghibli uslubi
- Yuqori sifatli anime detallari

## Cheklovlar

1. **API cheklovlari**
   - Leonardo.ai API-ning kunlik so'rovlar limiti mavjud
   - Rasm generatsiya qilish vaqti 30-60 soniya
   - Rasm o'lchami maksimum 512x512 piksel

2. **Rasm talablari**
   - Yuborilgan rasm hajmi 5MB dan oshmasligi kerak
   - Qo'llab-quvvatlanadigan formatlar: JPG, PNG

## Xatoliklarni bartaraf etish

1. **Bot javob bermayapti**
   - Internet aloqasini tekshiring
   - Botni qayta ishga tushiring
   - Token to'g'riligini tekshiring

2. **Rasm generatsiya qilinmayapti**
   - API kaliti to'g'riligini tekshiring
   - Tavsif ingliz tilida ekanligini tekshiring
   - API limitlarini tekshiring

3. **Anime stil xatoligi**
   - Rasm hajmini tekshiring
   - Rasm formatini tekshiring
   - Qaytadan urinib ko'ring

## Yordam va qo'llab-quvvatlash

Muammolar yoki savollar bo'lsa, quyidagi manzillarga murojaat qiling:
- GitHub Issues
- Telegram: @yourusername
- Email: your.email@example.com

## Litsenziya

MIT License - Batafsil ma'lumot uchun [LICENSE](LICENSE) faylini ko'ring.
