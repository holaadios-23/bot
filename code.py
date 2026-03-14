import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import datetime
from flask import Flask
from threading import Thread

# --- CONFIGURACIÓN PARA RENDER (KEEP ALIVE) ---
app = Flask('')
@app.route('/')
def home(): return "Bot de Aprobación y Anuncios Online"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# --- CARGA DE CONFIGURACIÓN ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Canal de aprobación (#confirmacion-de-sub)
IMAGEN_CANAL_ID = 1357862393698582717
ROL_APROBADO_ID = 1398080680088436776
EMOJI_REACCION = '✅'

# Canal de anuncios (#juan)
ANUNCIO_CANAL_ID = 1370933615822897282
ROL_AVISOS_ID = 1393278057963454524

# Hora del anuncio (21:00 UTC)
TARGET_TIME = datetime.time(21, 0, 0, tzinfo=datetime.timezone.utc)

intents = discord.Intents.default()
intents.message_content = True 
intents.members = True          
bot = commands.Bot(command_prefix='!', intents=intents)

# --- UTILIDAD: PRÓXIMO ANUNCIO ---
def get_next_announcement_date():
    now = datetime.datetime.now(datetime.timezone.utc)
    days_ahead = (5 - now.weekday() + 7) % 7
    if days_ahead == 0 and now.time() > TARGET_TIME: days_ahead = 7
    next_date = now + datetime.timedelta(days=days_ahead)
    return next_date.strftime("%d/%m/%Y") + " a las 21:00 UTC"

# --- COMANDO: !test ---
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

# --- EVENTO: APROBACIÓN POR IMAGEN ---
@bot.event
async def on_message(message):
    if message.author.bot: return

    # Verificamos si es el canal de imágenes y si tiene archivos adjuntos
    if message.channel.id == IMAGEN_CANAL_ID and message.attachments:
        try:
            member = message.guild.get_member(message.author.id)
            rol_aprobado = message.guild.get_role(ROL_APROBADO_ID)
            
            if member and rol_aprobado:
                await message.add_reaction(EMOJI_REACCION)
                await member.add_roles(rol_aprobado, reason="Imagen enviada en canal de aprobación.")
                print(f"✅ Rol asignado a {member.name}")
        except Exception as e:
            print(f"❌ Error en aprobación: {e}")
            
    await bot.process_commands(message)

# --- TAREA: ANUNCIO SEMANAL (SÁBADOS) ---
@tasks.loop(time=TARGET_TIME)
async def anuncio_semanal():
    await bot.wait_until_ready()
    # 5 representa el Sábado
    if datetime.datetime.now(datetime.timezone.utc).weekday() == 5:
        try:
            canal = bot.get_channel(ANUNCIO_CANAL_ID)
            if canal:
                await canal.send(f"<@&{ROL_AVISOS_ID}> ES HORA DE JUGAR")
                print("📢 Anuncio semanal enviado correctamente.")
        except Exception as e:
            print(f"❌ Error enviando anuncio: {e}")

# --- INICIO ---
@bot.event
async def on_ready():
    print(f'Bot iniciado como: {bot.user}')
    if not anuncio_semanal.is_running(): 
        anuncio_semanal.start()

if TOKEN:
    keep_alive()
    bot.run(TOKEN)
else:
    print("❌ ERROR: No se encontró el TOKEN en las variables de entorno.")
