import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import datetime
from flask import Flask
from threading import Thread

# --- CONFIGURACIÓN PARA RENDER (WEB SERVER) ---
app = Flask('')

@app.route('/')
def home():
    return "¡Bot de Discord está vivo y funcionando!"

def run_web():
    # Render asigna un puerto automáticamente en la variable PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# --- CARGA DE VARIABLES ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# --- CONFIGURACIÓN DE IDs ---
IMAGEN_CANAL_ID = 1357862393698582717
ROL_APROBADO_ID = 1398080680088436776
EMOJI_REACCION = '✅'
ANUNCIO_CANAL_ID = 1370933615822897282
ROL_AVISOS_ID = 1393278057963454524

TARGET_TIME = datetime.time(21, 0, 0, tzinfo=datetime.timezone.utc)

# --- INTENTS ---
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True          

bot = commands.Bot(command_prefix='!', intents=intents)

# --- COMANDO DE VERIFICACIÓN (!test) ---
@bot.command()
async def test(ctx):
    """Verifica si el bot responde y muestra su latencia."""
    latencia = round(bot.latency * 1000)
    embed = discord.Embed(title="✅ Estado del Bot", color=0x00ff00)
    embed.add_field(name="Estado", value="Online", inline=True)
    embed.add_field(name="Latencia", value=f"{latencia}ms", inline=True)
    embed.add_field(name="Canal de Imágenes", value=f"<#{IMAGEN_CANAL_ID}>", inline=False)
    
    await ctx.send(embed=embed)

# --- TAREA DE ANUNCIO SEMANAL ---
@tasks.loop(time=TARGET_TIME)
async def anuncio_semanal():
    await bot.wait_until_ready()
    now = datetime.datetime.now(datetime.timezone.utc)
    
    if now.weekday() == 5: # SÁBADO
        try:
            for guild in bot.guilds:
                target_channel = guild.get_channel(ANUNCIO_CANAL_ID)
                avisos_role = guild.get_role(ROL_AVISOS_ID)

                if target_channel and avisos_role:
                    await target_channel.send(f"{avisos_role.mention} ES HORA DE JUGAR")
                    print(f"Anuncio enviado en {guild.name}")
        except Exception as e:
            print(f"Error en anuncio: {e}")

# --- EVENTO DE MENSAJE (APROBACIÓN) ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Si es en el canal de imágenes y tiene adjunto
    if message.channel.id == IMAGEN_CANAL_ID and message.attachments:
        try:
            member = message.guild.get_member(message.author.id)
            if member:
                await message.add_reaction(EMOJI_REACCION)
                rol_aprobado = message.guild.get_role(ROL_APROBADO_ID)
                if rol_aprobado:
                    await member.add_roles(rol_aprobado)
                    print(f"Rol asignado a {member.name}")
        except Exception as e:
            print(f"Error en on_message: {e}")
            
    # IMPORTANTE: Procesar comandos después del on_message
    await bot.process_commands(message)

# --- INICIO ---
@bot.event
async def on_ready():
    print(f'Bot iniciado como: {bot.user}')
    if not anuncio_semanal.is_running():
        anuncio_semanal.start()

if TOKEN:
    keep_alive() # Inicia el servidor web para Render
    bot.run(TOKEN)
else:
    print("No se encontró el TOKEN.")
