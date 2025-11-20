import os
import json
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# ===== Проверка токена =====
print("DISCORD_TOKEN:", repr(os.getenv("DISCORD_TOKEN")))

# ===== Настройки радио =====
RADIO_URL = os.getenv("RADIO_URL", "https://dfm.hostingradio.ru/dfm96.aacp?radiostatistica=IRP_VK")
CONFIG_FILE = "channels.json"

# ===== Keep-alive через Flask =====
app = Flask('')

@app.route('/')
def home():
    return "Бот живой!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# ===== Интенты =====
intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== Работа с конфигом =====
def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# ===== Автоподключение при старте =====
@bot.event
async def on_ready():
    print(f"Бот запущен: {bot.user}")
    config = load_config()
    for guild in bot.guilds:
        gid = str(guild.id)
        if gid in config:
            channel_id = config[gid]
            channel = bot.get_channel(channel_id)
            if channel:
                try:
                    vc = await channel.connect()
                    vc.play(discord.FFmpegPCMAudio(RADIO_URL))
                    print(f"▶ Подключён к {channel.name} на сервере {guild.name}")
                except Exception as e:
                    print(f"Ошибка подключения: {e}")

# ===== Автоподключение на новом сервере =====
@bot.event
async def on_guild_join(guild):
    print(f"Бот добавлен на новый сервер: {guild.name}")
    # Ожидаем команду !setradio от админа нового сервера

# ===== Команда: установить канал радио =====
@bot.command(name="setradio")
@commands.has_permissions(administrator=True)
async def set_radio(ctx, channel: discord.VoiceChannel):
    config = load_config()
    config[str(ctx.guild.id)] = channel.id
    save_config(config)
    await ctx.send(f"🎧 Теперь радио будет играть в: **{channel.name}**")

    try:
        if ctx.guild.voice_client:
            await ctx.guild.voice_client.disconnect(force=True)
        vc = await channel.connect()
        vc.play(discord.FFmpegPCMAudio(RADIO_URL))
    except Exception as e:
        await ctx.send(f"Ошибка подключения: {e}")

# ===== Запуск бота =====
bot.run(os.getenv("DISCORD_TOKEN"))

