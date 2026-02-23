import os
import json
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# ===== Настройки =====
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
RADIO_URL = os.getenv(
    "RADIO_URL",
    "https://dfm.hostingradio.ru/dfm96.aacp?radiostatistica=IRP_VK"
)
CONFIG_FILE = "channels.json"

# ===== Интенты =====
intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== Flask (для хостинга) =====
app = Flask("")

@app.route("/")
def home():
    return "Bot is running"

def run():
    app.run(host="0.0.0.0", port=3000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ===== Работа с конфигом =====
def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# ===== Функция запуска радио =====
def play_radio(vc):
    if vc.is_playing():
        vc.stop()

    source = discord.FFmpegPCMAudio(
        RADIO_URL,
        executable="ffmpeg",
        before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        options="-vn"
    )
    vc.play(source)

# ===== При запуске =====
@bot.event
async def on_ready():
    print(f"Бот запущен как {bot.user}")
    config = load_config()

    for guild in bot.guilds:
        gid = str(guild.id)
        if gid in config:
            channel = bot.get_channel(config[gid])
            if channel:
                try:
                    if guild.voice_client:
                        await guild.voice_client.disconnect(force=True)

                    vc = await channel.connect()
                    play_radio(vc)
                    print(f"▶ Подключён к {channel.name} ({guild.name})")

                except Exception as e:
                    print(f"Ошибка подключения: {e}")

# ===== Если выбросило из канала =====
@bot.event
async def on_voice_state_update(member, before, after):
    if member == bot.user and after.channel is None:
        print("Бота выбросило из канала")

# ===== Установка канала =====
@bot.command(name="setradio")
@commands.has_permissions(administrator=True)
async def set_radio(ctx, channel: discord.VoiceChannel):
    config = load_config()
    config[str(ctx.guild.id)] = channel.id
    save_config(config)

    await ctx.send(f"🎧 Радио будет играть в: **{channel.name}**")

    try:
        if ctx.guild.voice_client:
            await ctx.guild.voice_client.disconnect(force=True)

        vc = await channel.connect()
        play_radio(vc)

    except Exception as e:
        await ctx.send(f"Ошибка подключения: {e}")

# ===== Команда остановки =====
@bot.command(name="stopradio")
@commands.has_permissions(administrator=True)
async def stop_radio(ctx):
    if ctx.guild.voice_client:
        await ctx.guild.voice_client.disconnect(force=True)
        await ctx.send("⛔ Радио остановлено")
    else:
        await ctx.send("Бот не подключён")

# ===== Запуск =====
keep_alive()
bot.run(DISCORD_TOKEN)
