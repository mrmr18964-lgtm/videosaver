# 🎬 Video Yuklovchi Telegram Bot

Video havolasini yuboring — bot uni yuklab, to'g'ridan-to'g'ri video sifatida qaytaradi.

## Qo'llab-quvvatlanadilar
YouTube, Instagram, TikTok, Twitter/X, Facebook, Vimeo, Dailymotion va 1000+ boshqa saytlar (yt-dlp orqali).

---

## 🚀 Render'da Deploy Qilish

### 1. Bot token olish
1. Telegramda **[@BotFather](https://t.me/BotFather)** ga yozing
2. `/newbot` → nom bering → token oling
3. Tokenni ko'chirib oling: `1234567890:AAF...`

### 2. Render'ga yuklash
1. [render.com](https://render.com) ga kiring → **New → Blueprint**
2. GitHub repoga ulang (yoki ZIP ni repo sifatida yuklang)
3. `render.yaml` avtomatik aniqlanadi → **Apply**
4. **Environment Variables** bo'limida:
   - `BOT_TOKEN` = BotFather bergan token
5. **Deploy** tugmasini bosing ✅

---

## ⚙️ Muhit O'zgaruvchilari

| O'zgaruvchi   | Majburiy | Standart | Tavsif                        |
|---------------|----------|----------|-------------------------------|
| `BOT_TOKEN`   | ✅ Ha    | —        | BotFather tokeni              |
| `MAX_FILE_MB` | Yo'q     | `50`     | Maksimal fayl hajmi (MB)      |

---

## 📁 Fayl Tuzilmasi

```
videobot/
├── bot.py            # Asosiy bot kodi
├── requirements.txt  # Python kutubxonalari
├── render.yaml       # Render konfiguratsiyasi
└── README.md         # Shu fayl
```

---

## 🛠 Mahalliy Ishga Tushirish

```bash
# 1. Kutubxonalarni o'rnating
pip install -r requirements.txt

# 2. Token o'rnating
export BOT_TOKEN="your_token_here"

# 3. Botni ishga tushiring
python bot.py
```

---

## ⚠️ Cheklovlar
- Telegram maksimum fayl hajmi: **50 MB**
- Katta videolar uchun xabar ko'rsatiladi
- Render **Free** tarifi: resurslar cheklangan; ko'p foydalanuvchi uchun **Starter** tarifini tanlang
