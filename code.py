import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
import datetime
import asyncio
from flask import Flask
from threading import Thread
import random
import time
import json

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
ROL_PRISMATICO_ID = 1397336931561635883

# Variables de estado
db_recordatorios = {} 
anuncios_activos = True
prefijo_actual = "!" # Prefijo por defecto
prismatico_cooldowns = {}  # {user_id: timestamp_ultimo_cambio}
prismatico_random_cooldowns = {}  # {user_id: timestamp_ultimo_random}

# Función dinámica para obtener el prefijo
def get_prefix(bot, message):
    return prefijo_actual

intents = discord.Intents.default()
intents.message_content = True 
intents.members = True          
bot = commands.Bot(command_prefix=get_prefix, intents=intents)

# --- SINCRONIZACIÓN DE COMANDOS ---
@bot.event
async def on_ready():
    print(f'Bot iniciado como: {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos slash")
    except Exception as e:
        print(f"Error sincronizando: {e}")
    if not anuncio_semanal.is_running(): anuncio_semanal.start()

# --- COMANDO PARA CAMBIAR PREFIJO (! Y /) ---
@bot.command(name="prefijo")
@commands.has_permissions(administrator=True)
async def cambiar_prefijo(ctx, nuevo_prefijo: str):
    global prefijo_actual
    prefijo_actual = nuevo_prefijo
    await ctx.send(f"✅ El prefijo ha sido cambiado a: `{nuevo_prefijo}`")

@bot.tree.command(name="prefijo", description="Cambia el prefijo de los comandos de texto")
@app_commands.checks.has_permissions(administrator=True)
async def prefijo_slash(interaction: discord.Interaction, nuevo_prefijo: str):
    global prefijo_actual
    prefijo_actual = nuevo_prefijo
    await interaction.response.send_message(f"✅ El prefijo ha sido cambiado a: `{nuevo_prefijo}`")

# --- SISTEMA DE RECORDATORIOS ---
async def crear_recordatorio(interaction_or_ctx, tiempo_min: int, tarea: str):
    # Detectar si es Context o Interaction
    is_slash = isinstance(interaction_or_ctx, discord.Interaction)
    user_id = interaction_or_ctx.user.id if is_slash else interaction_or_ctx.author.id
    
    if user_id not in db_recordatorios: db_recordatorios[user_id] = []
    if len(db_recordatorios[user_id]) >= 5:
        msg = "❌ Ya tienes el máximo de 5 recordatorios activos."
        return await interaction_or_ctx.response.send_message(msg) if is_slash else await interaction_or_ctx.send(msg)

    db_recordatorios[user_id].append(tarea)
    confirmacion = f"⏰ Recordatorio fijado en {tiempo_min} min: **{tarea}**"
    
    if is_slash: await interaction_or_ctx.response.send_message(confirmacion)
    else: await interaction_or_ctx.send(confirmacion)

    await asyncio.sleep(tiempo_min * 60)
    
    user = await bot.fetch_user(user_id)
    try:
        await user.send(f"🔔 **RECORDATORIO:** {tarea}")
    except:
        pass # Por si tiene DMs cerrados
    
    if user_id in db_recordatorios and tarea in db_recordatorios[user_id]:
        db_recordatorios[user_id].remove(tarea)

@bot.command()
async def recordar(ctx, tiempo: int, *, tarea: str):
    await crear_recordatorio(ctx, tiempo, tarea)

@bot.tree.command(name="recordar", description="Crea un recordatorio (máximo 5)")
async def recordar_slash(interaction: discord.Interaction, tiempo_minutos: int, tarea: str):
    await crear_recordatorio(interaction, tiempo_minutos, tarea)

# --- COMANDO PING ---
@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! {round(bot.latency * 1000)}ms")

@bot.tree.command(name="ping", description="Muestra la latencia del bot")
async def ping_slash(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong! {round(bot.latency * 1000)}ms")

# --- DESACTIVAR ANUNCIOS ---
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

# --- SISTEMA PRISMÁTICO ---
def is_valid_hex(color):
    """Valida que sea un color hex válido"""
    if len(color) != 7:
        return False
    if color[0] != '#':
        return False
    try:
        int(color[1:], 16)
        return True
    except ValueError:
        return False

def hex_to_int(hex_color):
    """Convierte hex a int para Discord"""
    return int(hex_color[1:], 16)

@bot.command(name="prismatico")
async def prismatico(ctx):
    """Obtener el rol prismático"""
    member = ctx.author
    guild = ctx.guild
    rol_prismatico = guild.get_role(ROL_PRISMATICO_ID)
    
    if not rol_prismatico:
        await ctx.send("❌ El rol prismático no existe en este servidor.")
        return
    
    if rol_prismatico in member.roles:
        await ctx.send("✨ ¡Ya tienes el rol prismático!")
        return
    
    try:
        await member.add_roles(rol_prismatico)
        embed = discord.Embed(
            title="✨ ¡Bienvenido al club prismático!",
            description="Ahora puedes cambiar el color de tu nombre.\n\n**Comandos disponibles:**\n`!colorprismatico #FFFFFF` - Cambiar color (cada 2 días)\n`!randomcolor` - Color aleatorio (cada 2 horas)",
            color=discord.Color.from_str("#FF00FF")
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Error al asignar el rol: {e}")

@bot.command(name="colorprismatico")
async def colorprismatico(ctx, color: str):
    """Cambiar el color del rol prismático (máximo cada 2 días)"""
    member = ctx.author
    guild = ctx.guild
    rol_prismatico = guild.get_role(ROL_PRISMATICO_ID)
    
    if not rol_prismatico:
        await ctx.send("❌ El rol prismático no existe.")
        return
    
    if rol_prismatico not in member.roles:
        await ctx.send("❌ No tienes el rol prismático. Usa `!prismatico` primero.")
        return
    
    if not is_valid_hex(color):
        await ctx.send("❌ Color inválido. Usa el formato: `#FFFFFF` (hexadecimal)")
        return
    
    # Verificar cooldown (2 días = 172800 segundos)
    user_id = member.id
    tiempo_actual = time.time()
    
    if user_id in prismatico_cooldowns:
        tiempo_pasado = tiempo_actual - prismatico_cooldowns[user_id]
        if tiempo_pasado < 172800:  # 2 días
            horas_restantes = (172800 - tiempo_pasado) / 3600
            await ctx.send(f"⏳ Debes esperar {horas_restantes:.1f} horas más para cambiar de color.")
            return
    
    try:
        color_int = hex_to_int(color)
        await rol_prismatico.edit(color=discord.Color(color_int))
        prismatico_cooldowns[user_id] = tiempo_actual
        
        embed = discord.Embed(
            title="🎨 Color actualizado",
            description=f"Tu color prismático ahora es: `{color}`",
            color=discord.Color(color_int)
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Error al cambiar el color: {e}")

@bot.command(name="randomcolor")
async def randomcolor(ctx):
    """Cambiar a un color aleatorio (máximo cada 2 horas)"""
    member = ctx.author
    guild = ctx.guild
    rol_prismatico = guild.get_role(ROL_PRISMATICO_ID)
    
    if not rol_prismatico:
        await ctx.send("❌ El rol prismático no existe.")
        return
    
    if rol_prismatico not in member.roles:
        await ctx.send("❌ No tienes el rol prismático. Usa `!prismatico` primero.")
        return
    
    # Verificar cooldown (2 horas = 7200 segundos)
    user_id = member.id
    tiempo_actual = time.time()
    
    if user_id in prismatico_random_cooldowns:
        tiempo_pasado = tiempo_actual - prismatico_random_cooldowns[user_id]
        if tiempo_pasado < 7200:  # 2 horas
            minutos_restantes = (7200 - tiempo_pasado) / 60
            await ctx.send(f"⏳ Debes esperar {minutos_restantes:.1f} minutos más para usar randomcolor.")
            return
    
    try:
        color_aleatorio = random.randint(0, 0xFFFFFF)
        color_hex = f"#{color_aleatorio:06X}"
        
        await rol_prismatico.edit(color=discord.Color(color_aleatorio))
        prismatico_random_cooldowns[user_id] = tiempo_actual
        
        embed = discord.Embed(
            title="🌈 Color aleatorio aplicado",
            description=f"Tu nuevo color es: `{color_hex}`",
            color=discord.Color(color_aleatorio)
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Error al cambiar a color aleatorio: {e}")

# --- TAREAS Y EVENTOS ---
@tasks.loop(time=TARGET_TIME)
async def anuncio_semanal():
    await bot.wait_until_ready()
    if not anuncios_activos: return
    if datetime.datetime.now(datetime.timezone.utc).weekday() == 5:
        for guild in bot.guilds:
            canal = guild.get_channel(ANUNCIO_CANAL_ID)
            rol = guild.get_role(ROL_AVISOS_ID)
            if canal and rol: await canal.send(f"{rol.mention} ES HORA DE JUGAR")

@bot.event
async def on_message(message):
    if message.author.bot: return
    # Aprobación de imágenes
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
