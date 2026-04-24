import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import datetime
import random 
import asyncio # Necesario para las pausas de limpieza
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
    days_ahead = (5 - now.weekday() + 7) % 7
    if days_ahead == 0 and now.time() > TARGET_TIME:
        days_ahead = 7
    
    next_date = now + datetime.timedelta(days=days_ahead)
    return next_date.strftime("%d/%m/%Y") + " a las 21:00 UTC"

# --- NUEVO COMANDO: LIMPIEZA GLOBAL ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def limpiar_usuario(ctx, usuario: discord.Member, *, texto: str):
    """Buscador global: !limpiar_usuario @nombre palabra"""
    msg_inicial = await ctx.send(f"🔍 Escaneando servidor para eliminar mensajes de **{usuario.display_name}** con el texto: `{texto}`...")
    
    total_eliminados = 0
    texto_buscado = texto.lower()

    # Recorremos todos los canales de texto donde el bot tiene acceso
    for canal in ctx.guild.text_channels:
        try:
            # Revisa los últimos 500 mensajes de cada canal
            async for message in canal.history(limit=500):
                if message.author.id == usuario.id and texto_buscado in message.content.lower():
                    await message.delete()
                    total_eliminados += 1
                    await asyncio.sleep(0.4) # Evita el baneo por spam de la API
        except discord.Forbidden:
            continue # Salta canales donde no tiene permiso
        except Exception as e:
            print(f"Error en canal {canal.name}: {e}")

    await ctx.send(f"✅ Proceso terminado. Se eliminaron **{total_eliminados}** mensajes en total.")

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
