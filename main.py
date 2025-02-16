import asyncio
import aiohttp
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# مقدارهای مهم (جایگزین کن)
TOKEN = "7954308819:AAEJZoc_WZy2hM8eBFW__raHGTML2GQ5kJU"  # توکن بات تلگرام
MAL_CLIENT_ID = "d623864309e3685eb6542fe3d8d4ef34"  # کلاینت آی‌دی از مای انیمه لیست
DATA_FILE = "subscribed_users.json"  # فایل ذخیره کاربران

bot = Bot(token=TOKEN)
dp = Dispatcher()
last_notified = {}  # ذخیره آخرین قسمت ارسال‌شده

# ---------- ذخیره و خواندن کاربران ----------
def load_users():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_users(users):
    with open(DATA_FILE, "w") as f:
        json.dump(users, f)

subscribed_users = load_users()

# ---------- دریافت انیمه‌های در حال پخش از MAL ----------
async def get_airing_anime():
    url = "https://api.myanimelist.net/v2/anime/season/now?fields=id,title,main_picture,mean,num_episodes,start_date"
    headers = {"X-MAL-CLIENT-ID": MAL_CLIENT_ID}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
            return data.get("data", [])

# ---------- چک کردن انیمه‌ها و ارسال نوتیف ----------
async def notify_users():
    while True:
        airing_list = await get_airing_anime()
        for anime in airing_list:
            anime_id = anime["node"]["id"]
            title = anime["node"]["title"]
            img_url = anime["node"]["main_picture"]["medium"]
            episodes = anime["node"].get("num_episodes", "نامشخص")
            mean_score = anime["node"].get("mean", "نامشخص")
            start_date = anime["node"].get("start_date", "نامشخص")

            # بررسی اینکه قبلاً اطلاع داده شده یا نه
            if anime_id not in last_notified or last_notified[anime_id] < episodes:
                msg = f"🎬 **قسمت جدید منتشر شد!**\n\n"
                msg += f"📺 **{title}**\n"
                msg += f"📅 تاریخ شروع: {start_date}\n"
                msg += f"⭐ امتیاز MAL: {mean_score}\n"
                msg += f"🎭 تعداد قسمت‌ها: {episodes}\n"
                msg += f"[🔗 مشاهده در MAL](https://myanimelist.net/anime/{anime_id})"

                for user_id in subscribed_users:
                    await bot.send_photo(chat_id=user_id, photo=img_url, caption=msg, parse_mode="Markdown")

                last_notified[anime_id] = episodes  # ذخیره آخرین قسمت ارسال‌شده

        await asyncio.sleep(3600)  # چک کردن هر ساعت

# ---------- ثبت کاربران جدید ----------
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = str(message.chat.id)
    if user_id not in subscribed_users:
        subscribed_users.append(user_id)
        save_users(subscribed_users)
        await message.reply("✅ شما در لیست اعلان‌های انیمه ثبت شدید! هر وقت قسمت جدیدی بیاد، بهتون خبر می‌دم. 🎬")
    else:
        await message.reply("⚡ شما قبلاً عضو لیست اعلان‌ها بودید.")

# ---------- حذف کاربران از لیست ----------
@dp.message(Command("stop"))
async def stop(message: types.Message):
    user_id = str(message.chat.id)
    if user_id in subscribed_users:
        subscribed_users.remove(user_id)
        save_users(subscribed_users)
        await message.reply("❌ شما از لیست اعلان‌های انیمه حذف شدید. برای دریافت دوباره، دستور /start رو بزنید.")
    else:
        await message.reply("🚫 شما قبلاً در لیست اعلان‌ها نبودید.")

# ---------- اجرای بات ----------
async def main():
    asyncio.create_task(notify_users())  # چک کردن انیمه‌ها
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
