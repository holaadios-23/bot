import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import datetime
import random
import colorsys # <--- Para calcular el HSL
from flask import Flask
from threading import Thread

# --- CONFIGURACIÓN PARA RENDER ---
app = Flask('')
@app.route('/')
def home(): return "Bot con Comandos de Color Online"

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

# --- FUNCIONES DE UTILIDAD ---
def get_next_announcement_date():
    now = datetime.datetime.now(datetime.timezone.utc)
    days_ahead = (5 - now.weekday() + 7) % 7
    if days_ahead == 0 and now.time() > TARGET_TIME: days_ahead = 7
    next_date = now + datetime.timedelta(days=days_ahead)
    return next_date.strftime("%d/%m/%Y") + " a las 21:00 UTC"

# --- NUEVO COMANDO: !randomcolor (Cooldown 2h) ---
"""
@bot.command()
@commands.cooldown(1, 7200, commands.BucketType.guild) # 1 uso cada 7200 seg (2h)
async def randomcolor(ctx):
    rol = ctx.guild.get_role(ROL_ARCOIRIS_ID)
    if not rol: return await ctx.send("❌ No configuraste el ROL_ARCOIRIS_ID correctamente.")

    # Generar RGB
    r, g, b = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
    nuevo_color = discord.Color.from_rgb(r, g, b)
    
    # Calcular HSL
    h, s, l = colorsys.rgb_to_hls(r/255, g/255, b/255)
    
    try:
        await rol.edit(color=nuevo_color)
        hex_val = str(nuevo_color).upper()
        
        embed = discord.Embed(title="🎨 ¡Color Aleatorio Aplicado!", color=nuevo_color)
        embed.add_field(name="Hexadecimal", value=f"`{hex_val}`", inline=True)
        embed.add_field(name="RGB", value=f"`({r}, {g}, {b})`", inline=True)
        embed.add_field(name="HSL", value=f"`{round(h*360)}°, {round(s*100)}%, {round(l*100)}%`", inline=True)
        embed.set_thumbnail(url=f"https://singlecolorimage.com/get/{hex_val[1:]}/100x100")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Error al editar el rol: {e}")

"""

"""
# --- NUEVO COMANDO: !setcolor (Cooldown 2h) ---
@bot.command()
@commands.cooldown(1, 7200, commands.BucketType.guild)
async def setcolor(ctx, hex_input: str):
    rol = ctx.guild.get_role(ROL_ARCOIRIS_ID)
    if not rol: return await ctx.send("❌ Rol no encontrado.")

    # Limpiar el input por si no ponen el #
    hex_input = hex_input.strip("#")
    try:
        color_int = int(hex_input, 16)
        nuevo_color = discord.Color(color_int)
        await rol.edit(color=nuevo_color)
        await ctx.send(f"✅ Se ha cambiado el color del rol a: **#{hex_input.upper()}**")
    except ValueError:
        ctx.command.reset_cooldown(ctx) # Si falla el formato, no le cobramos el cooldown
        await ctx.send("❌ Formato inválido. Usa un hexadecimal real (ej: `!setcolor #FF5733`)")

# --- MANEJO DE ERRORES DE COOLDOWN ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        horas = int(error.retry_after // 3600)
        minutos = int((error.retry_after % 3600) // 60)
        await ctx.send(f"⏳ ¡Cálmate! Este comando tiene cooldown. Vuelve en **{horas}h {minutos}m**.")

"""

# --- COMANDO: !test ---
@bot.command()
async def test(ctx):
    latencia = round(bot.latency * 1000)
    embed = discord.Embed(title="✅ Estado del Bot", color=0x00ff00)
    embed.add_field(name="Latencia", value=f"{latencia}ms")
    embed.add_field(name="Próximo Anuncio", value=get_next_announcement_date(), inline=False)
    await ctx.send(embed=embed)

# --- EVENTO DE MENSAJE (APROBACIÓN) ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.channel.id == IMAGEN_CANAL_ID and message.attachments:
        try:
            member = message.guild.get_member(message.author.id)
            rol = message.guild.get_role(ROL_APROBADO_ID)
            if member and rol:
                await message.add_reaction(EMOJI_REACCION)
                await member.add_roles(rol)
        except: pass
    await bot.process_commands(message)

# --- TAREA: ANUNCIO SEMANAL ---
@tasks.loop(time=TARGET_TIME)
async def anuncio_semanal():
    await bot.wait_until_ready()
    if datetime.datetime.now(datetime.timezone.utc).weekday() == 5:
        canal = bot.get_channel(ANUNCIO_CANAL_ID)
        rol = discord.utils.get(bot.get_all_members(), id=ROL_AVISOS_ID) # Simplificado
        if canal: await canal.send(f"<@&{ROL_AVISOS_ID}> ES HORA DE JUGAR")

@bot.event
async def on_ready():
    print(f'Bot iniciado como: {bot.user}')
    if not anuncio_semanal.is_running(): anuncio_semanal.start()

if TOKEN:
    keep_alive()
    bot.run(TOKEN)


