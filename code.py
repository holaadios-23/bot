import os
import discord
from discord.ext import commands,tasks
from dotenv import load_dotenv
import random 

# Cargar variables de entorno desde un archivo .env
load_dotenv()

# --- CONFIGURACIÓN PRINCIPAL ---
TOKEN = os.getenv('DISCORD_TOKEN')
CANAL_ID = 1357862393698582717 # ID del canal para subir imágenes
ROL_APROBADO_ID = 1398080680088436776 # ID del rol a asignar por la imagen
EMOJI_REACCION = '✅'

# --- CONFIGURACIÓN ROL ARCOÍRIS ---
ROL_RAINBOW_ID = 1445836449944567819
TIEMPO_ENTRE_CAMBIOS = 15.0 # Segundos (Puedes bajar a 10.0 si es estable)
COLOR_INDEX = 0 # Inicia en la posición 0 de la lista
NUM_COLORES = 55 # <-- ACTUALIZADO: 48 + 7 = 55

# Lista combinada de 55 colores (48 intermedios + 7 puros)
COLORES_RAINBOW = [
    0xFF0000, 0xA1DB04, 0xB1CE01, 0xC0C000, 0xCEB101, 0xDBA104, 0xFF7F00, 
    0xE6910A, 0xEF8011, 0xF66F1A, 0xFC5F25, 0xFFFF00, 
    0xFF4F32, 0xFF4040, 0xFF324F, 0xFC255F, 0xF61A6F, 0xEF1180, 
    0xE60A91, 0xDB04A1, 0xFF00FF,
    0xCE01B1, 0xC000C0, 0xB101CE, 0x9400D3,
    0xA104DB, 0x910AE6, 0x8011EF, 0x6F1AF6, 0x5F25FC, 0x4F32FF, 
    0x4040FF, 0x0000FF,
    0x324FFF, 0x255FFC, 0x1A6FF6, 0x1180EF, 0x0A91E6, 0x04A1DB, 
    0x01B1CE, 0x00C0C0, 0x01CEB1, 0x00FF00,
    0x04DBA1, 0x0AE691, 0x11EF80, 0x1AF66F, 0x25FC5F, 
    0x32FF4F, 0x40FF40, 0x4FFF32, 0x5FFC25, 0x6FF61A, 0x80EF11, 0x91E60A
]

# Intenciones
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# --- EVENTO DE MENSAJE (APROBACIÓN DE IMAGEN) ---
@bot.event
async def on_message(message):
    if message.author.bot or message.channel.id != CANAL_ID:
        return

    if message.attachments:
        try:
            member = message.guild.get_member(message.author.id)
            if not member:
                return
            
            await message.add_reaction(EMOJI_REACCION)
            rol_aprobado = message.guild.get_role(ROL_APROBADO_ID)

            if rol_aprobado:
                await member.add_roles(rol_aprobado, reason="Imagen aprobada.")
                print(f"Rol '{rol_aprobado.name}' asignado a {member.name}")
            else:
                await message.channel.send(f"⚠️ Error: No se encontró el rol con ID `{ROL_APROBADO_ID}`.")

        except discord.Forbidden:
            await message.channel.send("⚠️ Error: No tengo permisos para reaccionar o asignar roles.")
        except Exception as e:
            print(f"Error inesperado en on_message: {e}")
            
    await bot.process_commands(message)

# --- FUNCIÓN DE BUCLE ASÍNCRONO (RAINBOW ROLE CON ROTACIÓN SECUENCIAL) ---
@tasks.loop(seconds=TIEMPO_ENTRE_CAMBIOS)
async def cambiar_color_rol():
    global COLOR_INDEX
    await bot.wait_until_ready()
    
    try: 
        new_color = COLORES_RAINBOW[COLOR_INDEX]
        
        # Rotación: 0, 1, 2, ..., 54, 0
        COLOR_INDEX = (COLOR_INDEX + 1) % NUM_COLORES
        
        for guild in bot.guilds:
            rainbow_role = guild.get_role(ROL_RAINBOW_ID)

            if rainbow_role:
                try:
                    await rainbow_role.edit(color=new_color)
                    print(f"Color de '{rainbow_role.name}' en '{guild.name}' cambiado a {hex(new_color)} (Index: {COLOR_INDEX})")
                except discord.Forbidden:
                    print(f"Error: Bot no puede editar rol '{rainbow_role.name}' en '{guild.name}'.")
                except Exception as e:
                    print(f"Error al cambiar color del rol en guild: {e}")
                    
    except Exception as general_error:
        print(f"⚠️ ERROR FATAL EN EL BUCLE cambiar_color_rol: {general_error}")

# --- INICIO DEL BOT ---
@bot.event
async def on_ready():
    print(f'Bot iniciado como: {bot.user}')
    print('------')
    if not cambiar_color_rol.is_running():
        cambiar_color_rol.start()
        
if TOKEN is None:
    print("Error: El token del bot no está configurado.")
else:
    try:
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        print("Error: El token proporcionado es inválido.")# --- EVENTO DE MENSAJE (APROBACIÓN DE IMAGEN) ---
@bot.event
async def on_message(message):
    if message.author.bot or message.channel.id != CANAL_ID:
        return

    if message.attachments:
        try:
            member = message.guild.get_member(message.author.id)
            if not member:
                return
            
            await message.add_reaction(EMOJI_REACCION)
            rol_aprobado = message.guild.get_role(ROL_APROBADO_ID)

            if rol_aprobado:
                await member.add_roles(rol_aprobado, reason="Imagen aprobada.")
                print(f"Rol '{rol_aprobado.name}' asignado a {member.name}")
            else:
                await message.channel.send(f"⚠️ Error: No se encontró el rol con ID `{ROL_APROBADO_ID}`.")

        except discord.Forbidden:
            await message.channel.send("⚠️ Error: No tengo permisos para reaccionar o asignar roles.")
        except Exception as e:
            print(f"Error inesperado en on_message: {e}")
            
    await bot.process_commands(message)

# --- FUNCIÓN DE BUCLE ASÍNCRONO ---
@tasks.loop(seconds=TIEMPO_ENTRE_CAMBIOS)
async def cambiar_color_rol():
    global TONALIDAD_ACTUAL
    await bot.wait_until_ready()
    
    # NUEVO: Bloque try/except para toda la tarea
    try: 
        # 1. Calcular el nuevo valor de Tonalidad (Hue)
        TONALIDAD_ACTUAL = (TONALIDAD_ACTUAL + INCREMENTO_HUE) % 360
        
        # 2. Convertir la tonalidad a formato de color Discord (RGB)
        new_color_int = hsl_a_discord_color(TONALIDAD_ACTUAL / 360) 

        # 3. Aplicar el color a todos los servidores
        for guild in bot.guilds:
            rainbow_role = guild.get_role(ROL_RAINBOW_ID)

            if rainbow_role:
                try:
                    await rainbow_role.edit(color=new_color_int)
                    # Este print confirma que el bucle sigue vivo
                    print(f"Color de rol '{rainbow_role.name}' cambiado a HSL({TONALIDAD_ACTUAL}°) / {hex(new_color_int)}")
                    
                except discord.Forbidden:
                    print(f"Error de Permisos: Bot no puede editar rol '{rainbow_role.name}' en '{guild.name}'.")
                except Exception as e:
                    print(f"Error al cambiar color del rol en guild: {e}")
                    
    except Exception as general_error:
        # Esto captura cualquier error fuera del bucle de guilds (e.g., error en colorsys)
        print(f"⚠️ ERROR FATAL EN EL BUCLE cambiar_color_rol: {general_error}")
        
# --- INICIO DEL BOT ---
@bot.event
async def on_ready():
    print(f'Bot iniciado como: {bot.user}')
    print('------')
    if not cambiar_color_rol.is_running():
        cambiar_color_rol.start()
        
if TOKEN is None:
    print("Error: El token del bot no está configurado.")
else:
    try:
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        print("Error: El token proporcionado es inválido.")



