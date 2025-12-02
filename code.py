import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Cargar variables de entorno desde un archivo .env
load_dotenv()

# --- CONFIGURACIÓN ---
# Mueve tu token a un archivo .env por seguridad.
TOKEN = os.getenv('DISCORD_TOKEN')
# Reemplaza con los IDs reales de tu servidor (activa el Modo Desarrollador en Discord)
CANAL_ID = 1357862393698582717    # El canal donde se esperan las imágenes
ROL_APROBADO_ID = 1398080680088436776 # El ID del rol a asignar

# El emoji que usará el bot para reaccionar
EMOJI_REACCION = '✅' # Puedes usar el nombre o el ID si es un emoji personalizado

# Necesitas definir las Intenciones (Intents) para que el bot pueda recibir 
# eventos de mensajes y cambios de estado.
# NECESITAS HABILITAR LOS MESSAGE CONTENT INTENTS EN EL PORTAL DE DESARROLLADORES DE DISCORD
intents = discord.Intents.default()
intents.message_content = True # Permite leer el contenido de los mensajes
intents.members = True         # Permite acceder a la información de los miembros y roles

# Inicializa el bot (cliente)
bot = commands.Bot(command_prefix='!', intents=intents)

# --- EVENTO DE MENSAJE ---
@bot.event
async def on_message(message):
    # 1. Ignorar mensajes del propio bot
    if message.author == bot.user:
        return

    # 2. Verificar que el mensaje provenga del canal específico
    if message.channel.id != CANAL_ID:
        return

    # 3. Verificar si el mensaje contiene algún adjunto (Attachment)
    #    (Esto suele indicar que es una imagen o archivo subido)
    if message.attachments:
        try:
            # Es más seguro obtener el objeto Member directamente desde el guild
            # para asegurarse de que no sea un objeto User si no está en caché.
            member = message.guild.get_member(message.author.id)
            if not member:
                print(f"No se pudo encontrar al miembro con ID {message.author.id} en el servidor.")
                return
            
            # A. Reaccionar al mensaje
            await message.add_reaction(EMOJI_REACCION)

            # B. Obtener el objeto Role usando el ID
            rol_aprobado = message.guild.get_role(ROL_APROBADO_ID)

            if rol_aprobado:
                # C. Asignar el rol al miembro
                await member.add_roles(rol_aprobado, reason="Imagen enviada y aprobada automáticamente.")
                print(f"Rol '{rol_aprobado.name}' asignado a {member.name}")
            else:
                print(f"Error: No se encontró el rol con ID {ROL_APROBADO_ID}")
                # Opcional: Avisar en el canal que hay un problema de configuración
                await message.channel.send(f"⚠️ Error de configuración: No se encontró el rol con ID `{ROL_APROBADO_ID}`. Por favor, avisa a un administrador.")


        except discord.Forbidden:
            print("Error de Permisos: El bot no tiene los permisos necesarios (Gestionar Roles o Reaccionar).")
            # Avisar al canal si el bot no tiene permisos es una buena práctica.
            await message.channel.send("⚠️ Error: No tengo permisos para reaccionar o asignar roles. Por favor, revisa mis permisos.")
        except Exception as e:
            print(f"Ocurrió un error inesperado: {e}")
            # await message.channel.send("⚠️ Error inesperado al procesar la imagen.")
            
    # Esto es necesario si usas commands.Bot para que también procese comandos (si tienes alguno)
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