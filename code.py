import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import datetime
import random # <--- Para los colores aleatorios
from flask import Flask
from threading import Thread

# --- CONFIGURACIÓN PARA RENDER ---
app = Flask('')
@app.route('/')
def home(): return "Bot Arcoíris Online"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# --- CARGA DE VARIABLES Y CONFIG ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

IMAGEN_CANAL_ID = 1357862393698582717
ROL_APROBADO_ID = 1398080680088436776
EMOJI_REACCION = '✅'
ANUNCIO_CANAL_ID = 1370933615822897282
ROL_AVISOS_ID = 1393278057963454524
ROL_ARCOIRIS_ID = 1455570171627573299

TARGET_TIME = datetime.time(21, 0, 0, tzinfo=datetime.timezone.utc)

intents = discord.Intents.default()
intents.message_content = True 
intents.members = True          
bot = commands.Bot(command_prefix='!', intents=intents)

# --- FUNCIÓN PARA COLOR ALEATORIO ---
def obtener_color_aleatorio():
    # Genera un color vibrante usando random
    return discord.Color.from_rgb(
        random.randint(0, 255), 
        random.randint(0, 255), 
        random.randint(0, 255)
    )

# --- TAREA: ROL ARCOÍRIS (ALEATORIO) ---
@tasks.loop(minutes=5)
async def cambiar_color_arcoiris():
    await bot.wait_until_ready()
    nuevo_color = obtener_color_aleatorio()

    for guild in bot.guilds:
        rol = guild.get_role(ROL_ARCOIRIS_ID)
        if rol:
            try:
                await rol.edit(color=nuevo_color)
                print(f"Color de rol cambiado a: {nuevo_color}")
            except Exception as e:
                print(f"Error cambiando color: {e}")

# --- NUEVO COMANDO: !color ---
@bot.command()
async def color(ctx):
    """Muestra el color hexadecimal actual del rol arcoíris."""
    rol = ctx.guild.get_role(ROL_ARCOIRIS_ID)
    if rol:
        hex_color = str(rol.color).upper()
        embed = discord.Embed(
            title="🌈 Color Actual del Rol", 
            description=f"El color actual es: **{hex_color}**",
            color=rol.color
        )
        # Esto añade una pequeña imagen del color al embed
        embed.set_thumbnail(url=f"https://singlecolorimage.com/get/{hex_color[1:]}/100x100")
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ No se encontró el rol arcoíris. Verifica el ID.")

# --- COMANDO: !test ---
@bot.command()
async def test(ctx):
    latencia = round(bot.latency * 1000)
    await ctx.send(f"✅ **Bot Online** | Latencia: {latencia}ms")

# --- EVENTO DE MENSAJE (APROBACIÓN) ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.channel.id == IMAGEN_CANAL_ID and message.attachments:
        try:
            member = message.guild.get_member(message.author.id)
            rol_aprobado = message.guild.get_role(ROL_APROBADO_ID)
            if member and rol_aprobado:
                await message.add_reaction(EMOJI_REACCION)
                await member.add_roles(rol_aprobado)
        except: pass
    await bot.process_commands(message)

# --- TAREA: ANUNCIO SEMANAL ---
@tasks.loop(time=TARGET_TIME)
async def anuncio_semanal():
    await bot.wait_until_ready()
    if datetime.datetime.now(datetime.timezone.utc).weekday() == 5:
        for guild in bot.guilds:
            canal = guild.get_channel(ANUNCIO_CANAL_ID)
            rol = guild.get_role(ROL_AVISOS_ID)
            if canal and rol: await canal.send(f"{rol.mention} ES HORA DE JUGAR")

# --- INICIO ---
@bot.event
async def on_ready():
    print(f'Bot iniciado como: {bot.user}')
    if not anuncio_semanal.is_running(): anuncio_semanal.start()
    if not cambiar_color_arcoiris.is_running(): cambiar_color_arcoiris.start()

if TOKEN:
    keep_alive()
    bot.run(TOKEN)

