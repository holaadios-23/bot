import os
import discord
from discord.ext import commands,tasks
from dotenv import load_dotenv
import colorsys

# Cargar variables de entorno desde un archivo .env
load_dotenv()

# --- CONFIGURACIÓN PRINCIPAL ---
TOKEN = os.getenv('DISCORD_TOKEN')
CANAL_ID = 1357862393698582717 # ID del canal para subir imágenes
ROL_APROBADO_ID = 1398080680088436776 # ID del rol a asignar por la imagen
EMOJI_REACCION = '✅'

# --- CONFIGURACIÓN ROL ARCOÍRIS ---
ROL_RAINBOW_ID = 1445836449944567819
TIEMPO_ENTRE_CAMBIOS = 30.0 # Segundos
TONALIDAD_ACTUAL = 0 # Hue inicial (0 = Rojo)
INCREMENTO_HUE = 15 # Pasos del cambio de color (360 / 15 = 24 colores por ciclo)

# Intenciones
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# --- FUNCIÓN PARA CONVERTIR HSL A HEXADECIMAL (CORREGIDA) ---
# Usamos L=0.5 (Luminosidad media) y S=1.0 (Saturación máxima) para colores puros.
def hsl_a_discord_color(h):
    # colorsys.hls_to_rgb(h, l, s)
    r, g, b = colorsys.hls_to_rgb(h, 0.5, 1.0) 
    
    # Convertir floats (0.0-1.0) a enteros (0-255)
    r = int(r * 255)
    g = int(g * 255)
    b = int(b * 255)
    
    # Combinar en formato 0xRRGGBB
    return (r << 16) + (g << 8) + b 

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


