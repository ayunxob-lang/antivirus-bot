import hashlib
import time
import threading
from flask import Flask
import requests
import telebot

# 1. Sozlamalar
BOT_TOKEN = "8822672925:AAFwhCqSJpg5Jl14gpjd6HUpItI0vxzpc5w"
VT_API_KEY = "771e86962f15f9a2bc4fd49ea82613d03c3f8f4f30b2d74f209d0562bd87ae53"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')


@app.route('/')
def home():
  return "Bot muvaffaqiyatli ishlayapti!"


def run_server():
  import os
  port = int(os.environ.get("PORT", 8080))
  app.run(host='0.0.0.0', port=port)


threading.Thread(target=run_server).start()


@bot.message_handler(commands=['start'])
def send_welcome(message):
  bot.reply_to(
      message,
      "👋 Salom! Men antivirus botman.\n\n🛡 Menga biron bir fayl yoki havola (link)"
      " yuboring, unda virus bor-yo'qligini tekshirib beraman!",
  )


# --- FAYLLARNI TEKSHIRISH ---
@bot.message_handler(content_types=['document'])
def handle_docs(message):
  try:
    # Fayl kelishi bilan xabar chiqarish
    bot.reply_to(message, "📄 Fayl qabul qilindi.")

    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    file_hash = hashlib.sha256(downloaded_file).hexdigest()

    url = f"https://www.virustotal.com/api/v3/files/{file_hash}"
    headers = {"x-apikey": VT_API_KEY}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
      result = response.json()
      stats = result['data']['attributes']['last_analysis_stats']
      malicious = stats['malicious']
      undetected = stats['undetected']

      if malicious > 0:
        bot.reply_to(
            message,
            f"🚨 Diqqat! Faylda virus topildi!\n🦠 Zararli: {malicious}\n✅ Toza:"
            f" {undetected}",
        )
      else:
        bot.reply_to(
            message,
            f"📄 Bu fayl mutloq xavfsiz. Bemalol foydalaning.\n🦠 Zararli:"
            f" {malicious}\n✅ Toza: {undetected}",
        )

    elif response.status_code == 404:
      bot.reply_to(
          message,
          "📄 Bu fayl mutloq xavfsiz. Bemalol foydalaning.\n🦠 Zararli: 0\n✅ Toza:"
          " 0",
      )
    else:
      bot.reply_to(
          message,
          f"❌ Faylni tekshirishda xatolik! Status kod: {response.status_code}",
      )

  except Exception as e:
    bot.reply_to(message, f"Xato yuz berdi: {str(e)}")


# --- HAVOLALARNI TEKSHIRISH ---
@bot.message_handler(
    func=lambda message: message.text
    and (
        message.text.startswith('http://')
        or message.text.startswith('https://')
    )
)
def handle_links(message):
  try:
    bot.reply_to(
        message, "🔍 Havola qabul qilindi."
    )

    url = "https://www.virustotal.com/api/v3/urls"
    headers = {"x-apikey": VT_API_KEY}
    data = {"url": message.text}
    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
      time.sleep(3)
      analysis_id = response.json()['data']['id']
      analysis_url = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"
      result_response = requests.get(analysis_url, headers=headers)

      if result_response.status_code == 200:
        stats = result_response.json()['data']['attributes']['stats']
        malicious = stats['malicious']
        harmless = stats['harmless']

        if malicious > 0:
          bot.reply_to(
              message,
              f"🚨 Diqqat! Havola xavfli deb topildi!\n🦠 Zararli (Malicious):"
              f" {malicious}\n✅ Toza (Harmless): {harmless}",
          )
        else:
          bot.reply_to(
              message,
              f"🔗 Bu havola mutloq xavfsiz. Bemalol foydalaning.\n🦠 Zararli"
              f" (Malicious): {malicious}\n✅ Toza (Harmless): {harmless}",
          )
      else:
        bot.reply_to(
            message,
            f"❌ Natijani olishda xatolik! Status kod:"
            f" {result_response.status_code}",
        )
    else:
      bot.reply_to(
          message,
          f"❌ Havolani yuborishda xatolik yuz berdi!\nStatus kod:"
          f" {response.status_code}\nJavob: {response.text}",
      )
  except Exception as e:
    bot.reply_to(message, f"Xato yuz berdi: {str(e)}")


if __name__ == "__main__":
  bot.infinity_polling()
