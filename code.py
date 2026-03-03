import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import datetime
import random 
from flask import Flask
from threading import Thread

# --- CONFIGURACIÓN PARA RENDER ---
app = Flask('')
@app.route('/')
def home(): return "Bot Online - Esperando Anuncio Semanal"

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

# --- FUNCIÓN PARA CALCULAR PRÓXIMO ANUNCIO ---
def get_next_announcement_date():
    now = datetime.datetime.now(datetime.timezone.utc)
    # 5 es Sábado. Calculamos días restantes
    days_ahead = (5 - now.weekday() + 7) % 7
    if days_ahead == 0 and now.time() > TARGET_TIME:
        days_ahead = 7
    
    next_date = now + datetime.timedelta(days=days_ahead)
    return next_date.strftime("%d/%m/%Y") + " a las 21:00 UTC"

# --- TAREA: ROL ARCOÍRIS (DESACTIVADA CON COMENTARIOS) ---
# @tasks.loop(minutes=5)
# async def cambiar_color_arcoiris():
#     await bot.wait_until_ready()
#     nuevo_color = discord.Color.from_rgb(random.randint(0,255), random.randint(0,255), random.randint(0,255))
#     for guild in bot.guilds:
#         rol = guild.get_role(ROL_ARCOIRIS_ID)
#         if rol:
#             try:
#                 await rol.edit(color=nuevo_color)
#             except Exception as e: print(f"Error: {e}")

# --- COMANDO ACTUALIZADO: !test ---
@bot.command()
async def test(ctx):
    latencia = round(bot.latency * 1000)
    proximo = get_next_announcement_date()
    
    embed = discord.Embed(title="✅ Estado del Bot", color=0x00ff00)
    embed.add_field(name="Estado", value="Online", inline=True)
    embed.add_field(name="Latencia", value=f"{latencia}ms", inline=True)
    embed.add_field(name="Canal de Imágenes", value=f"<#{IMAGEN_CANAL_ID}>", inline=False)
    embed.add_field(name="Próximo Anuncio", value=f"📅 {proximo}", inline=False)
    
    await ctx.send(embed=embed)

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

if TOKEN:
    keep_alive()
    bot.run(TOKEN)
