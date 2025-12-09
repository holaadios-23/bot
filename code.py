import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import datetime 

# Cargar variables de entorno desde un archivo .env
load_dotenv()

# --- CONFIGURACIÓN PRINCIPAL ---
TOKEN = os.getenv('DISCORD_TOKEN')

# --- CONFIGURACIÓN DE APROBACIÓN DE IMÁGENES (Canal #imagen) ---
IMAGEN_CANAL_ID = 1357862393698582717    # <--- ID del canal #imagen (o el que uses para la aprobación)
ROL_APROBADO_ID = 1398080680088436776    # ID del rol a asignar por la imagen
EMOJI_REACCION = '✅' 

# --- CONFIGURACIÓN DE ANUNCIOS SEMANALES (Canal #juan) ---
ANUNCIO_CANAL_ID = 1370933615822897282   # <--- ID del canal #juan (¡REEMPLAZAR!)
ROL_AVISOS_ID = 1393278057963454524      # ID del rol @avisos (¡REEMPLAZAR!)

# Tiempo objetivo para la ejecución diaria (21:00 UTC)
TARGET_TIME = datetime.time(21, 0, 0, tzinfo=datetime.timezone.utc)

# --- INTENTS ---
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True         

bot = commands.Bot(command_prefix='!', intents=intents)

# --- TAREA DE ANUNCIO SEMANAL ---
@tasks.loop(time=TARGET_TIME)
async def anuncio_semanal():
    await bot.wait_until_ready()
    
    # 1. Verificar si hoy es Sábado (weekday() retorna 5 para Sábado)
    now = datetime.datetime.now(datetime.timezone.utc)
    
    if now.weekday() == 5: # El día es SÁBADO
        try:
            for guild in bot.guilds:
                # Usamos ANUNCIO_CANAL_ID para obtener el canal de destino
                target_channel = guild.get_channel(ANUNCIO_CANAL_ID)
                avisos_role = guild.get_role(ROL_AVISOS_ID)

                if target_channel and avisos_role:
                    message_content = f"{avisos_role.mention} ES HORA DE JUGAR"
                    await target_channel.send(message_content)
                    print(f"Anuncio semanal enviado en '{target_channel.name}' de '{guild.name}' a las {now.strftime('%H:%M')} UTC.")
                elif target_channel and not avisos_role:
                    print(f"Error: No se encontró el rol de avisos con ID {ROL_AVISOS_ID} en {guild.name}.")
                elif not target_channel:
                    print(f"Error: No se encontró el canal de anuncios con ID {ANUNCIO_CANAL_ID} en {guild.name}.")
        
        except Exception as e:
            print(f"Error durante el anuncio semanal: {e}")


# --- EVENTO DE MENSAJE (APROBACIÓN DE IMAGEN - Canal #imagen) ---
@bot.event
async def on_message(message):
    # Usamos IMAGEN_CANAL_ID para la verificación
    if message.author.bot or message.channel.id != IMAGEN_CANAL_ID:
        return

    if message.attachments:
        try:
            member = message.guild.get_member(message.author.id)
            if not member:
                return
            
            await message.add_reaction(EMOJI_REACCION)
            rol_aprobado = message.guild.get_role(ROL_APROBADO_ID)

            if rol_aprobado:
                await member.add_roles(rol_aprobado, reason="Imagen aprobada automáticamente.")
                print(f"Rol '{rol_aprobado.name}' asignado a {member.name}")
            else:
                await message.channel.send(f"⚠️ Error de configuración: No se encontró el rol con ID `{ROL_APROBADO_ID}`.")

        except discord.Forbidden:
            await message.channel.send("⚠️ Error: No tengo permisos para reaccionar o asignar roles. Por favor, revisa mis permisos.")
        except Exception as e:
            print(f"Ocurrió un error inesperado en on_message: {e}")
            
    await bot.process_commands(message)

# --- INICIO DEL BOT ---
@bot.event
async def on_ready():
    print(f'Bot iniciado como: {bot.user}')
    print('------')
    if not anuncio_semanal.is_running():
        anuncio_semanal.start()

if TOKEN is None:
    print("Error: El token del bot no está configurado.")
else:
    try:
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        print("Error: El token proporcionado es inválido. Revisa tu archivo .env.")
