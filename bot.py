import os
import json
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

print("DISCORD_TOKEN:", repr(os.getenv("DISCORD_TOKEN")))

# ======= Настройки радио =======
RADIO_URL = os.getenv("https://dfm.hostingradio.ru/dfm96.aacp?radiostatistica=IRP_VK")
CONFIG_FILE = "channels.json"

# ======= Keep-alive через Flask =======
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

# ======= Интенты =======
intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True
intents.message_content = True  # обязательно для команд

bot = commands.Bot(command_prefix="!", intents=intents)

# ======= Работа с конфигом =======
def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# ======= Автоподключение при запуске =======
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
            else:
                print(f"⚠ Канал {channel_id} не найден на сервере {guild.name}")

# ======= Команды =======
@bot.command(name="setradio")
@commands.has_permissions(administrator=True)
async def set_radio(ctx, channel: discord.VoiceChannel):
    """Устанавливает голосовой канал по умолчанию для радио"""
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

@bot.command(name="playradio")
async def play_radio(ctx):
    """Запуск радио вручную"""
    if not ctx.guild.voice_client:
        await ctx.send("Бот не в голосовом канале!")
        return
    vc = ctx.guild.voice_client
    vc.stop()
    vc.play(discord.FFmpegPCMAudio(RADIO_URL))
    await ctx.send("▶ Радио запущено!")

@bot.command(name="stopradio")
async def stop_radio(ctx):
    """Остановка радио и отключение от канала"""
    if ctx.guild.voice_client:
        await ctx.guild.voice_client.disconnect()
        await ctx.send("⛔ Радио остановлено.")
    else:
        await ctx.send("Бот не подключён к голосовому каналу.")

@bot.command(name="getdefaultvoice")
async def get_default_voice(ctx):
    """Показать канал по умолчанию для радио на этом сервере"""
    config = load_config()
    gid = str(ctx.guild.id)
    if gid in config:
        channel = bot.get_channel(config[gid])
        if channel:
            await ctx.send(f"🎧 Канал по умолчанию: **{channel.name}**")
        else:
            await ctx.send("Канал не найден.")
    else:
        await ctx.send("Канал по умолчанию ещё не установлен. Используй `!setradio`.")

# ======= Запуск бота =======
bot.run(os.getenv("DISCORD_TOKEN"))
