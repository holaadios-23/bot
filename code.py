import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
import datetime
import asyncio
from flask import Flask
from threading import Thread

# --- CONFIGURACIÓN PARA RENDER ---
app = Flask('')
@app.route('/')
def home(): return "Bot Online"

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
TARGET_TIME = datetime.time(21, 0, 0, tzinfo=datetime.timezone.utc)

# Base de datos temporal para recordatorios (Se borra si el bot se reinicia en Render)
# Para algo permanente usarías una DB, pero esto sirve para el uso diario.
db_recordatorios = {} 
anuncios_activos = True

intents = discord.Intents.default()
intents.message_content = True 
intents.members = True          
bot = commands.Bot(command_prefix='!', intents=intents)

# --- SINCRONIZACIÓN DE COMANDOS SLASH ---
@bot.event
async def on_ready():
    print(f'Bot iniciado como: {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos slash")
    except Exception as e:
        print(e)
    if not anuncio_semanal.is_running(): anuncio_semanal.start()

# --- 1. SISTEMA DE RECORDATORIOS ---
async def crear_recordatorio(interaction_or_ctx, tiempo_min: int, tarea: str):
    user_id = interaction_or_ctx.author.id if hasattr(interaction_or_ctx, 'author') else interaction_or_ctx.user.id
    
    if user_id not in db_recordatorios: db_recordatorios[user_id] = []
    
    if len(db_recordatorios[user_id]) >= 5:
        return "❌ Ya tienes el máximo de 5 recordatorios activos."

    db_recordatorios[user_id].append(tarea)
    resp = f"⏰ Recordatorio fijado en {tiempo_min} min: **{tarea}**"
    
    # Responder según el tipo de origen
    if isinstance(interaction_or_ctx, discord.Interaction):
        await interaction_or_ctx.response.send_message(resp)
    else:
        await interaction_or_ctx.send(resp)

    await asyncio.sleep(tiempo_min * 60)
    
    # Enviar recordatorio
    user = await bot.fetch_user(user_id)
    await user.send(f"🔔 **RECORDATORIO:** {tarea}")
    
    # Limpiar lista
    if tarea in db_recordatorios[user_id]:
        db_recordatorios[user_id].remove(tarea)

@bot.command()
async def recordar(ctx, tiempo: int, *, tarea: str):
    await crear_recordatorio(ctx, tiempo, tarea)

@bot.tree.command(name="recordar", description="Crea un recordatorio (máximo 5)")
async def recordar_slash(interaction: discord.Interaction, tiempo_minutos: int, tarea: str):
    await crear_recordatorio(interaction, tiempo_minutos, tarea)

# --- 2. COMANDO PING (! Y /) ---
@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! {round(bot.latency * 1000)}ms")

@bot.tree.command(name="ping", description="Muestra la latencia del bot")
async def ping_slash(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong! {round(bot.latency * 1000)}ms")

# --- 3. DESACTIVAR ANUNCIOS (! Y /) ---
@bot.command()
@commands.has_permissions(administrator=True)
async def toggle_anuncios(ctx):
    global anuncios_activos
    anuncios_activos = not anuncios_activos
    estado = "ACTIVADOS" if anuncios_activos else "DESACTIVADOS"
    await ctx.send(f"📢 Los anuncios del sábado han sido: **{estado}**")

@bot.tree.command(name="toggle_anuncios", description="Activa o desactiva los anuncios del sábado")
@app_commands.checks.has_permissions(administrator=True)
async def toggle_anuncios_slash(interaction: discord.Interaction):
    global anuncios_activos
    anuncios_activos = not anuncios_activos
    estado = "ACTIVADOS" if anuncios_activos else "DESACTIVADOS"
    await interaction.response.send_message(f"📢 Los anuncios del sábado han sido: **{estado}**")

# --- TAREA: ANUNCIO SEMANAL (CON FILTRO) ---
@tasks.loop(time=TARGET_TIME)
async def anuncio_semanal():
    await bot.wait_until_ready()
    if not anuncios_activos: return # No hace nada si están desactivados
    
    if datetime.datetime.now(datetime.timezone.utc).weekday() == 5:
        for guild in bot.guilds:
            canal = guild.get_channel(ANUNCIO_CANAL_ID)
            rol = guild.get_role(ROL_AVISOS_ID)
            if canal and rol: await canal.send(f"{rol.mention} ES HORA DE JUGAR")

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

if TOKEN:
    keep_alive()
    bot.run(TOKEN)
