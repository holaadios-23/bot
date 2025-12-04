import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Cargar variables de entorno desde un archivo .env
load_dotenv()

# --- CONFIGURACIÓN PRINCIPAL ---
# Mueve tu token a un archivo .env por seguridad.
TOKEN = os.getenv('DISCORD_TOKEN')

# Reemplaza con los IDs reales de tu servidor
CANAL_ID = 1357862393698582717    # ID del canal donde se esperan las imágenes
ROL_APROBADO_ID = 1398080680088436776 # ID del rol a asignar

# El emoji que usará el bot para reaccionar
EMOJI_REACCION = '✅' 

# --- INTENTS ---
# Necesarios para leer mensajes y acceder a información de miembros y roles.
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True         

# Inicializa el bot
bot = commands.Bot(command_prefix='!', intents=intents)

# --- EVENTO DE MENSAJE (APROBACIÓN DE IMAGEN) ---
@bot.event
async def on_message(message):
    # 1. Ignorar mensajes del propio bot o si no están en el canal correcto
    if message.author.bot or message.channel.id != CANAL_ID:
        return

    # 2. Verificar si el mensaje contiene algún adjunto (Attachment)
    if message.attachments:
        try:
            # Obtener el objeto Member para manipular los roles
            member = message.guild.get_member(message.author.id)
            if not member:
                return
            
            # A. Reaccionar al mensaje
            await message.add_reaction(EMOJI_REACCION)

            # B. Obtener el objeto Role usando el ID
            rol_aprobado = message.guild.get_role(ROL_APROBADO_ID)

            if rol_aprobado:
                # C. Asignar el rol al miembro
                await member.add_roles(rol_aprobado, reason="Imagen aprobada automáticamente.")
                print(f"Rol '{rol_aprobado.name}' asignado a {member.name}")
            else:
                print(f"Error: No se encontró el rol con ID {ROL_APROBADO_ID}")
                await message.channel.send(f"⚠️ Error de configuración: No se encontró el rol con ID `{ROL_APROBADO_ID}`.")

        except discord.Forbidden:
            print("Error de Permisos: El bot no tiene los permisos necesarios.")
            await message.channel.send("⚠️ Error: No tengo permisos para reaccionar o asignar roles. Por favor, revisa mis permisos.")
        except Exception as e:
            print(f"Ocurrió un error inesperado: {e}")
            
    # Procesa comandos normales si los hubiera
    await bot.process_commands(message)

# --- INICIO DEL BOT ---
@bot.event
async def on_ready():
    print(f'Bot iniciado como: {bot.user}')
    print('------')

if TOKEN is None:
    print("Error: El token del bot no está configurado. Asegúrate de crear un archivo .env con DISCORD_TOKEN='tu_token'")
else:
    try:
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        print("Error: El token proporcionado es inválido. Revisa tu archivo .env.")
