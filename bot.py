#bot.py (BETA v1.2.0 - Enhanced Version)

import discord
import os
import requests
import json
import locale
import pytz
from bs4 import BeautifulSoup, NavigableString
from dotenv import load_dotenv
from discord.ext import tasks, commands
from datetime import datetime, timedelta
from keep_alive import keep_alive

# --- Configuración y Carga ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# --- Configuración de Zona Horaria ---
try:
    TIMEZONE_CDMX = pytz.timezone('America/Mexico_City')
except pytz.exceptions.UnknownTimeZoneError:
    print("Error: No se pudo encontrar la zona horaria 'America/Mexico_City'.")
    print("Asegúrate de haber instalado 'pytz' (pip install pytz). Saliendo.")
    exit()

# --- Variables Globales de Memoria ---
PATCH_DATES = []
CLASH_EVENTS = []
CLASH_INFO = {}
VALID_CHAMPIONS = set()
PATCH_REMINDERS_SENT = []
CLASH_REMINDERS_SENT = []
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
PATCH_LIST_URL = "https://www.leagueoflegends.com/es-mx/news/tags/patch-notes/"


def load_config():
    """Carga toda la configuración inicial."""
    global PATCH_DATES, VALID_CHAMPIONS, CLASH_EVENTS, CLASH_INFO, PATCH_REMINDERS_SENT, CLASH_REMINDERS_SENT
    
    # Carga de campeones
    try:
        with open("champions.txt", "r", encoding="utf-8") as f:
            VALID_CHAMPIONS = {line.strip().lower() for line in f}
        print(f"Se cargaron {len(VALID_CHAMPIONS)} campeones.")
    except FileNotFoundError:
        print("Advertencia: No se encontró champions.txt.")
    
    # Carga de calendarios
    try:
        with open("patch_dates.json", "r") as f:
            data = json.load(f)
            PATCH_DATES = sorted(data.get("patch_dates", []))
        print(f"Se cargaron {len(PATCH_DATES)} fechas de parches.")
    except FileNotFoundError:
        print("Advertencia: No se encontró patch_dates.json.")
        
    try:
        with open("clash_dates.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            CLASH_EVENTS = sorted(data.get("clash_events", []), key=lambda x: x['team_formation_start'])
        print(f"Se cargaron {len(CLASH_EVENTS)} eventos de Clash.")
    except FileNotFoundError:
        print("Advertencia: No se encontró clash_dates.json.")

    try:
        with open("clash_info.json", "r", encoding="utf-8") as f:
            CLASH_INFO = json.load(f)
        print("Se cargó la información de Clash (horarios y premios).")
    except FileNotFoundError:
        print("Advertencia: No se encontró clash_info.json.")

    # Carga de memoria de recordatorios
    try:
        with open("sent_reminders.json", "r") as f:
            data = json.load(f)
            PATCH_REMINDERS_SENT = data.get("patch_reminders_sent", [])
            CLASH_REMINDERS_SENT = data.get("clash_reminders_sent", [])
        print("Se cargó la memoria de recordatorios.")
    except (FileNotFoundError, json.JSONDecodeError):
        print("Advertencia: No se encontró sent_reminders.json o está corrupto. Se creará uno nuevo.")
        PATCH_REMINDERS_SENT = []
        CLASH_REMINDERS_SENT = []
    
    # Configuración de locale en español
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, 'Spanish')
        except locale.Error:
            print("Advertencia: No se pudo establecer el locale a español.")

# --- Funciones de Scraping y Ayuda ---
def get_latest_patch_info():
    try:
        response = requests.get(PATCH_LIST_URL, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        latest_article_link = soup.find('a', href=lambda href: href and '/news/game-updates/patch-' in href)
        if latest_article_link:
            title_element = latest_article_link.find('div', attrs={'data-testid': 'card-title'})
            patch_title = title_element.text.strip() if title_element else "Título no encontrado"
            patch_date = ""
            date_element = latest_article_link.find('time')
            if date_element and date_element.has_attr('datetime'):
                timestamp_str = date_element['datetime']
                date_obj = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                patch_date = date_obj.strftime('%d/%m/%Y')
            patch_url_partial = latest_article_link['href']
            patch_url_full = "https://www.leagueoflegends.com" + patch_url_partial
            return patch_title, patch_url_full, patch_date
        return None, None, None
    except Exception as e:
        print(f"Error en get_latest_patch_info: {e}")
        return None, None, None

def scrape_summary_image(patch_url):
    try:
        response = requests.get(patch_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        summary_link = soup.find('a', class_='cboxElement')
        if summary_link:
            image_tag = summary_link.find('img')
            if image_tag and image_tag.has_attr('src'):
                return image_tag['src']
        return None
    except Exception as e:
        print(f"Error en scrape_summary_image: {e}")
        return None

def scrape_champion_list(patch_url):
    try:
        response = requests.get(patch_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        champion_links = soup.find_all('a', href=lambda href: href and '/champions/' in href)
        champion_names = []
        for link in champion_links:
            name = link.text.strip()
            if name and name not in champion_names:
                champion_names.append(name)
        return champion_names
    except Exception as e:
        print(f"Error en scrape_champion_list: {e}")
        return []

def format_change_li(li_element):
    parts = []
    for content in li_element.contents:
        if content.name == 'strong':
            parts.append(f"**{content.get_text(strip=True)}**")
        elif isinstance(content, NavigableString):
            text = str(content).replace('⇒', ' ⇒ ')
            parts.append(text.strip())
    return ' '.join(filter(None, parts))

def scrape_champion_details(patch_url, champion_name):
    """Extrae TODOS los bloques de cambios de un campeón (habilidades, estadísticas, etc.)."""
    try:
        response = requests.get(patch_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        normalized_name = champion_name.lower().replace(' ', '').replace('.', '').replace("'", "")
        target_id = f"patch-{normalized_name}"
        
        champion_header = soup.find('h3', id=target_id)
        if not champion_header: return None

        champion_data = { "name": champion_name.title(), "portrait_url": None, "summary": "", "change_blocks": [] }

        portrait_link = champion_header.find_previous('a', class_='reference-link')
        if portrait_link and portrait_link.find('img'):
            champion_data['portrait_url'] = portrait_link.find('img')['src']
        
        summary_tag = champion_header.find_next_sibling('blockquote')
        if summary_tag:
            champion_data['summary'] = summary_tag.get_text(strip=True)

        all_siblings = champion_header.find_next_siblings()
        change_headers = []
        for sibling in all_siblings:
            if sibling.name == 'h3':
                break
            if sibling.name == 'h4' and 'change-detail-title' in sibling.get('class', []):
                change_headers.append(sibling)

        for header in change_headers:
            icon_tag = header.find('img')
            icon_url = icon_tag['src'] if icon_tag else None
            
            changes_list_tag = header.find_next_sibling('ul')
            changes = []
            if changes_list_tag:
                changes = [f"• {format_change_li(li)}" for li in changes_list_tag.find_all('li')]
            
            current_block = {
                "title": header.get_text(strip=True),
                "icon_url": icon_url,
                "changes": changes
            }
            champion_data['change_blocks'].append(current_block)

        return champion_data
    except Exception as e:
        print(f"Error en scrape_champion_details: {e}")
        return None

def scrape_section_details(patch_url, section_id, header_tag='h2'):
    """
    Extrae una lista de todos los bloques de cambio (para objetos o runas)
    dentro de una sección.
    """
    try:
        response = requests.get(patch_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. Encontramos el encabezado principal (ej. <h2 id="patch-items">)
        main_header = soup.find(header_tag, id=section_id)
        if not main_header:
            return [] # Devolvemos una lista vacía si la sección no existe

        # 2. Determinamos el "padre" desde donde iterar
        iterate_from = main_header
        if main_header.parent.name == 'header':
            iterate_from = main_header.parent

        change_blocks_data = []
        
        # 3. Iteramos sobre los "hermanos" del encabezado
        for sibling in iterate_from.find_next_siblings():
            # 4. Condición de parada (si encontramos el siguiente encabezado principal)
            if (sibling.name == header_tag) or (sibling.name == 'header' and sibling.find(header_tag)):
                break
            
            # 5. Encontramos todos los sub-bloques de cambio (ej. cada item)
            # Buscamos por la misma estructura que 'p!ver' (h3, h4, etc.)
            item_headers = sibling.find_all(['h3', 'h4'], class_='change-title')
            
            for item_header in item_headers:
                item_data = { "title": item_header.get_text(strip=True), "icon_url": None, "summary": "", "changes": [] }
                
                # Buscar el ícono (igual que en campeones)
                icon_link = item_header.find_previous('a', class_='reference-link')
                if icon_link and icon_link.find('img'):
                    item_data['icon_url'] = icon_link.find('img')['src']
                
                # Buscar el resumen (blockquote) y la lista (ul)
                current_element = item_header
                while hasattr(current_element, 'next_sibling') and current_element.next_sibling:
                    current_element = current_element.next_sibling
                    if current_element.name == 'h3' or current_element.name == 'h4': # Parar si encontramos el siguiente item
                        break
                    if current_element.name == 'blockquote':
                        item_data['summary'] = current_element.get_text(strip=True)
                    if current_element.name == 'ul':
                        item_data['changes'] = [f"• {format_change_li(li)}" for li in current_element.find_all('li')]
                        # A diferencia de !ver, a veces el resumen viene DESPUÉS de la lista
                        # así que no rompemos el bucle aquí.
                
                change_blocks_data.append(item_data)

        return change_blocks_data
    except Exception as e:
        print(f"Error en scrape_section_details: {e}")
        return []
    
def format_timedelta(delta):
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    parts = []
    if days > 0:
        parts.append(f"{days} día{'s' if days > 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hora{'s' if hours > 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minuto{'s' if minutes > 1 else ''}")
    return ", ".join(parts) if parts else "en menos de un minuto"

# --- Configuración del Bot ---
intents = discord.Intents.default()
intents.message_content = True 
# Usamos un prefijo que no exista para que el sistema de comandos no interfiera con nuestro on_message.
bot = commands.Bot(command_prefix='&', intents=intents)

# --- TAREAS AUTOMÁTICAS (NUEVA LÓGICA) ---

def update_reminders_file():
    """Función de ayuda para guardar el estado de la memoria en el JSON."""
    with open("sent_reminders.json", "w") as f:
        json.dump({
            "patch_reminders_sent": PATCH_REMINDERS_SENT,
            "clash_reminders_sent": CLASH_REMINDERS_SENT
        }, f, indent=4)

@tasks.loop(minutes=1)
async def patch_scheduler():
    """Revisa cada minuto si debe enviar un anuncio relacionado con los parches."""
    now_cdmx = datetime.now(TIMEZONE_CDMX)
    channel = bot.get_channel(CHANNEL_ID)
    if not channel: return

    # --- 1. Lógica del Recordatorio Pre-Parche (10:00 AM del día anterior) ---
    for date_str in PATCH_DATES:
        patch_date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        reminder_time = patch_date_obj - timedelta(days=1)
        reminder_id = f"{date_str}-prepatch"

        if (now_cdmx.year == reminder_time.year and
            now_cdmx.month == reminder_time.month and
            now_cdmx.day == reminder_time.day and
            now_cdmx.hour == 10 and now_cdmx.minute == 0 and
            reminder_id not in PATCH_REMINDERS_SENT):
            
            disable_time = patch_date_obj.replace(hour=1, minute=30)
            # Aseguramos que el tiempo de CDMX esté asignado
            disable_time = TIMEZONE_CDMX.localize(disable_time) 
            time_remaining = disable_time - now_cdmx
            
            embed = discord.Embed(title="⏰ ¡Recordatorio de Parche!", description=f"Mañana, **{patch_date_obj.strftime('%d de %B')}**, es día de parche. Las colas clasificatorias se desactivarán aproximadamente a la 1:30 AM (CDMX).", color=discord.Color.orange())
            embed.add_field(name="Tiempo Restante para la Desactivación", value=format_timedelta(time_remaining))
            await channel.send(embed=embed)
            
            PATCH_REMINDERS_SENT.append(reminder_id)
            update_reminders_file()
            break # Solo un anuncio de parche por ciclo

    # --- 2. Lógica del Anuncio de Notas (Medianoche del día del parche) ---
    for date_str in PATCH_DATES:
        patch_date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        reminder_id = f"{date_str}-notes-published"

        if (now_cdmx.date() == patch_date_obj and
            now_cdmx.hour == 0 and now_cdmx.minute == 0 and
            reminder_id not in PATCH_REMINDERS_SENT):
            
            title, url, date = get_latest_patch_info()
            if url and (date_str in url or (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d') in url):
                embed = discord.Embed(title=f"✅ ¡Notas del Parche ya Disponibles!", description=f"Ya puedes consultar las notas de la versión **{title}**.", color=discord.Color.green(), url=url)
                await channel.send(embed=embed)
                
                PATCH_REMINDERS_SENT.append(reminder_id)
                update_reminders_file()
                break

    # --- 3. Lógica de Revisión de Página (cada 30 mins) ---
    # Revisa si hay un parche nuevo que no estaba en el calendario
    if now_cdmx.minute % 30 == 0:
        title, url, date = get_latest_patch_info()
        if not url: return
        
        try:
            with open("last_patch_url.txt", "r") as f: last_url = f.read().strip()
        except FileNotFoundError: last_url = ""
            
        if url != last_url:
            print(f"Nuevo parche detectado por scraping: {title}")
            image_url = scrape_summary_image(url)
            embed = discord.Embed(title=f"¡Nuevas Notas de Parche Disponibles!", description=f"**{title}** - Publicado el {date}", color=discord.Color.gold(), url=url)
            if image_url:
                embed.set_image(url=image_url)
            await channel.send(embed=embed)
            with open("last_patch_url.txt", "w") as f: f.write(url)

@tasks.loop(minutes=1)
async def clash_scheduler():
    """Revisa cada minuto si debe enviar un anuncio relacionado con Clash."""
    now_cdmx = datetime.now(TIMEZONE_CDMX)
    channel = bot.get_channel(CHANNEL_ID)
    if not channel: return
    
    reminders_updated = False
    for event in CLASH_EVENTS:
        formation_date = datetime.strptime(event['team_formation_start'], "%Y-%m-%d").date()
        reminder_id_formation = f"{event['name']}-{event['team_formation_start']}-formation"

        if (now_cdmx.date() == formation_date and
            now_cdmx.hour == 10 and now_cdmx.minute == 0 and
            reminder_id_formation not in CLASH_REMINDERS_SENT):
            
            first_tournament_day = TIMEZONE_CDMX.localize(datetime.strptime(event['tournament_days'][0], "%Y-%m-%d"))
            time_remaining = first_tournament_day - now_cdmx
            tournament_days_str = " y ".join([datetime.strptime(d, "%Y-%m-%d").strftime("%d") for d in event['tournament_days']])
            month_year = datetime.strptime(event['tournament_days'][0], "%Y-%m-%d").strftime("%B")
            
            embed = discord.Embed(title=f"📢 ¡La Formación de Equipos para Clash: {event['name']} ha comenzado!", color=discord.Color.green())
            embed.add_field(name="Días del Torneo", value=f"{tournament_days_str} de {month_year}", inline=False)
            embed.add_field(name="Tiempo Restante para el Torneo", value=format_timedelta(time_remaining), inline=False)
            embed.add_field(name="Hora de Confirmación General", value="A partir de las 17:00 CDMX.", inline=False)
            await channel.send(embed=embed)
            
            CLASH_REMINDERS_SENT.append(reminder_id_formation)
            reminders_updated = True

        for day_str in event['tournament_days']:
            tournament_date = datetime.strptime(day_str, "%Y-%m-%d").date()
            
            # Recordatorio 10:00 AM
            reminder_id_morning = f"{event['name']}-{day_str}-morning"
            if (now_cdmx.date() == tournament_date and
                now_cdmx.hour == 10 and now_cdmx.minute == 0 and
                reminder_id_morning not in CLASH_REMINDERS_SENT):
                
                confirmation_start_time = TIMEZONE_CDMX.localize(now_cdmx.replace(hour=17, minute=0, second=0))
                time_remaining = confirmation_start_time - now_cdmx
                first_place_prize = CLASH_INFO.get("premios", {}).get("lista", [{}])[0].get("recompensa", "Recompensas épicas")

                embed = discord.Embed(title=f"⚔️ ¡Hoy es día de Torneo Clash: {event['name']}!", color=discord.Color.gold())
                embed.add_field(name="Premio del 1er Lugar", value=first_place_prize, inline=False)
                embed.add_field(name="La Fase de Confirmación inicia a las 17:00 CDMX", value=f"(Faltan: {format_timedelta(time_remaining)})", inline=False)
                await channel.send(embed=embed)
                
                CLASH_REMINDERS_SENT.append(reminder_id_morning)
                reminders_updated = True
            
            # Recordatorio 18:50 PM
            reminder_id_final = f"{event['name']}-{day_str}-final"
            if (now_cdmx.date() == tournament_date and
                now_cdmx.hour == 18 and now_cdmx.minute == 50 and
                reminder_id_final not in CLASH_REMINDERS_SENT):
                
                confirmation_end_time = TIMEZONE_CDMX.localize(now_cdmx.replace(hour=19, minute=0, second=0))
                time_remaining = confirmation_end_time - now_cdmx
                first_place_prize = CLASH_INFO.get("premios", {}).get("lista", [{}])[0].get("recompensa", "Recompensas épicas")

                embed = discord.Embed(title=f"🚨 ¡ÚLTIMA LLAMADA PARA CLASH: {event['name']}!", description="**¡SOLO QUEDAN 10 MINUTOS PARA CONFIRMAR!**", color=discord.Color.dark_red())
                embed.add_field(name="Premio del 1er Lugar", value=first_place_prize, inline=False)
                embed.add_field(name="La Fase de Confirmación termina a las 19:00 CDMX", value=f"(Cierra en: {format_timedelta(time_remaining)})", inline=False)
                await channel.send(embed=embed)

                CLASH_REMINDERS_SENT.append(reminder_id_final)
                reminders_updated = True

    if reminders_updated:
        update_reminders_file()

# --- EVENTOS DEL BOT ---
@bot.event
async def on_ready():
    print(f"¡{bot.user} se ha conectado a Discord!")
    if not patch_scheduler.is_running():
        patch_scheduler.start()
    if not clash_scheduler.is_running():
        clash_scheduler.start()

# --- NUEVO "PORTERO" (MANEJADOR DE MENSAJES) ---
@bot.event
async def on_message(message):
    # Ignorar mensajes del propio bot
    if message.author == bot.user:
        return

    # Definir los prefijos
    PREFIX_PATCH = 'p!'
    PREFIX_CLASH = 'c!'
    PREFIX_GLOBAL = '!'

    msg = message.content

    # --- ENRUTADOR GLOBAL ---
    if msg.startswith(PREFIX_GLOBAL):
        command_string = msg[len(PREFIX_GLOBAL):] # Quita el '!'
        parts = command_string.split(maxsplit=1)
        command = parts[0].lower()

        if command == "ayuda":
            await handle_ayuda(message)

    # --- ENRUTADOR DE PARCHES ---
    elif msg.startswith(PREFIX_PATCH):
        command_string = msg[len(PREFIX_PATCH):] # Quita el 'p!'
        parts = command_string.split(maxsplit=1)
        command = parts[0].lower()
        argument = parts[1] if len(parts) > 1 else None

        if command == "parche":
            await handle_parche(message)
        elif command == "campeones":
            await handle_campeones(message)
        elif command == "ver":
            if argument:
                await handle_ver_champ(message, champion_name=argument)
            else:
                await message.channel.send("Debes especificar un campeón. Ej: `p!ver Ahri`")
        elif command == "objetos":
            await handle_objetos(message)
        elif command == "runas":
            await handle_runas(message)
        elif command == "calendario":
            await handle_cparche(message)
        elif command == "siguiente":
            await handle_sparche(message)

    # --- ENRUTADOR DE CLASH ---
    elif msg.startswith(PREFIX_CLASH):
        command_string = msg[len(PREFIX_CLASH):] # Quita el 'c!'
        parts = command_string.split(maxsplit=1)
        command = parts[0].lower()

        if command == "clash":
            await handle_sclash(message)
        elif command == "calendario":
            await handle_cclash(message)
        elif command == "horarios":
            await handle_hclash(message)
        elif command == "premios":
            await handle_pclash(message)

# --- MANEJADORES DE COMANDOS DE PARCHE ---
async def handle_parche(message):
    async with message.channel.typing():
        title, url, date = get_latest_patch_info()
        if title and url:
            image_url = scrape_summary_image(url)
            embed = discord.Embed(title=f"Notas del Parche: {title}", description=f"Anunciadas el {date}.", color=discord.Color.blue(), url=url)
            if image_url:
                embed.set_image(url=image_url)
            await message.channel.send(embed=embed)
        else:
            await message.channel.send("No se pudo obtener la información del parche en este momento.")


async def handle_campeones(message):
    async with message.channel.typing():
        title, url, date = get_latest_patch_info()
        if not url:
            await message.channel.send("Error: No se pudo encontrar el último parche.")
            return
        champ_list = scrape_champion_list(url)
    if champ_list:
        description = "- " + "\n- ".join(champ_list)
        embed = discord.Embed(title=f"Campeones en el Parche: {title}", description=description, color=discord.Color.teal())
        await message.channel.send(embed=embed)
    else:
        await message.channel.send("No se encontraron campeones en estas notas del parche.")

async def handle_ver_champ(message, champion_name: str):
    clean_name = champion_name.lower().strip()
    if clean_name not in VALID_CHAMPIONS:
        embed = discord.Embed(
            title="❌ Error: Campeón no encontrado",
            description=f"No se encontró un campeón llamado **'{champion_name}'**.\n\nRevisa la ortografía o usa `p!campeones` para ver la lista.",
            color=discord.Color.red()
        )
        await message.channel.send(embed=embed)
        return

    async with message.channel.typing():
        title, url, date = get_latest_patch_info()
        if not url:
            await message.channel.send("Error: No se pudo encontrar el último parche.")
            return
        details = scrape_champion_details(url, clean_name)

    if not details:
        embed = discord.Embed(
            description=f"No se encontraron cambios para **{champion_name.title()}** en las notas del parche actual.",
            color=discord.Color.light_grey()
        )
        await message.channel.send(embed=embed)
        return

    main_embed = discord.Embed(title=f"Cambios para {details['name']} ({title})", description=details.get('summary', 'Sin resumen.'), color=discord.Color.purple())
    if details['portrait_url']:
        main_embed.set_thumbnail(url=details['portrait_url'])
    await message.channel.send(embed=main_embed)

    for block in details.get('change_blocks', []):
        changes_text = "\n".join(block['changes'])
        if not changes_text: changes_text = "Sin detalles específicos."
        block_embed = discord.Embed(color=discord.Color.purple())
        if block['icon_url']:
            block_embed.set_author(name=block['title'], icon_url=block['icon_url'])
        else:
            block_embed.set_author(name=block['title'])
        block_embed.description = changes_text
        await message.channel.send(embed=block_embed)


async def handle_objetos(message):
    async with message.channel.typing():
        title, url, date = get_latest_patch_info()
        if not url:
            await message.channel.send("Error: No se pudo encontrar el último parche.")
            return
        
        item_list = scrape_section_details(url, "patch-items")

    if not item_list:
        embed = discord.Embed(description=f"No hay cambios a objetos en el parche **{title}**.", color=discord.Color.orange())
        await message.channel.send(embed=embed)
        return

    main_embed = discord.Embed(title=f"Cambios a Objetos ({title})", color=discord.Color.orange())
    await message.channel.send(embed=main_embed)
    
    for item in item_list:
        summary_text = item.get('summary', 'Sin resumen.')
        changes_text = "\n".join(item['changes'])
        
        description = summary_text
        if changes_text:
            description += f"\n\n**Cambios:**\n{changes_text}"
        
        embed = discord.Embed(
            title=item['title'],
            description=description,
            color=discord.Color.orange()
        )
        if item['icon_url']:
            embed.set_thumbnail(url=item['icon_url'])
        
        await message.channel.send(embed=embed)


async def handle_runas(message):
    async with message.channel.typing():
        title, url, date = get_latest_patch_info()
        if not url:
            await message.channel.send("Error: No se pudo encontrar el último parche.")
            return
            
        rune_list = scrape_section_details(url, "patch-runes")

    if not rune_list:
        embed = discord.Embed(description=f"No hay cambios a runas en el parche **{title}**.", color=discord.Color.light_grey())
        await message.channel.send(embed=embed)
        return

    main_embed = discord.Embed(title=f"Cambios a Runas ({title})", color=discord.Color.light_grey())
    await message.channel.send(embed=main_embed)
    
    for rune in rune_list:
        summary_text = rune.get('summary', 'Sin resumen.')
        changes_text = "\n".join(rune['changes'])
        
        description = summary_text
        if changes_text:
            description += f"\n\n**Cambios:**\n{changes_text}"
        
        embed = discord.Embed(
            title=rune['title'],
            description=description,
            color=discord.Color.light_grey()
        )
        if rune['icon_url']:
            embed.set_thumbnail(url=rune['icon_url'])
        
        await message.channel.send(embed=embed)


async def handle_cparche(message):
    now = datetime.now()
    future_patches = [date for date in PATCH_DATES if datetime.strptime(date, "%Y-%m-%d") > now]
    if future_patches:
        next_patch_str = future_patches[0]
        description_lines = []
        for date_str in future_patches:
            patch_date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = patch_date_obj.strftime('%d de %B de %Y')
            if date_str == next_patch_str:
                next_patch_datetime = datetime.strptime(date_str + " 03:00", "%Y-%m-%d %H:%M")
                time_remaining = next_patch_datetime - now
                description_lines.append(f"• **{formatted_date}** (Faltan: {format_timedelta(time_remaining)})")
            else:
                description_lines.append(f"• {formatted_date}")
        embed = discord.Embed(title="🗓️ Calendario de Futuros Parches", description="\n".join(description_lines), color=discord.Color.dark_purple())
        await message.channel.send(embed=embed)
    else:
        await message.channel.send("No hay más parches programados en el calendario.")

async def handle_sparche(message):
    now = datetime.now()
    next_patch_date = None
    for date_str in PATCH_DATES:
        patch_date = datetime.strptime(date_str + " 03:00", "%Y-%m-%d %H:%M")
        if patch_date > now:
            next_patch_date = patch_date
            break
    if next_patch_date:
        time_remaining = next_patch_date - now
        embed = discord.Embed(title="📅 Próximo Parche de LoL", description=f"La próxima actualización está programada para el **{next_patch_date.strftime('%d de %B de %Y')}**.", color=discord.Color.blue())
        embed.add_field(name="Tiempo Restante", value=format_timedelta(time_remaining))
        await message.channel.send(embed=embed)
    else:
        await message.channel.send("No hay más parches programados en el calendario para este año.")

# --- MANEJADORES DE COMANDOS DE CLASH ---
async def handle_sclash(message):
    now = datetime.now()
    next_clash = None
    for event in CLASH_EVENTS:
        event_start_date = datetime.strptime(event['team_formation_start'], "%Y-%m-%d")
        if event_start_date > now:
            next_clash = event
            break
    if next_clash:
        time_remaining = event_start_date - now
        tournament_days_str = " y ".join([datetime.strptime(day, "%Y-%m-%d").strftime("%d") for day in next_clash['tournament_days']])
        month_year = datetime.strptime(next_clash['tournament_days'][0], "%Y-%m-%d").strftime("%B de %Y")
        team_formation_date = datetime.strptime(next_clash['team_formation_start'], "%Y-%m-%d").strftime("%d de %B")
        description = (f"Corresponde a la versión {next_clash['version']}.\n\n"
                       f"**Inicio de Formación de Equipos:** {team_formation_date}\n"
                       f"**Días del Torneo:** {tournament_days_str} de {month_year}\n\n"
                       f"**Tiempo para Formar Equipo:** {format_timedelta(time_remaining)}")
        embed = discord.Embed(title=f"🏆 Próximo Clash: {next_clash['name']}", description=description, color=discord.Color.red())
        await message.channel.send(embed=embed)
    else:
        await message.channel.send("No hay más torneos de Clash programados.")

async def handle_cclash(message):
    now = datetime.now()
    future_clash = [event for event in CLASH_EVENTS if datetime.strptime(event['team_formation_start'], "%Y-%m-%d") > now]
    if future_clash:
        embed = discord.Embed(title="⚔️ Calendario de Futuros Torneos de Clash", color=discord.Color.dark_red())
        for event in future_clash:
            tournament_days_str = " y ".join([datetime.strptime(day, "%Y-%m-%d").strftime("%d") for day in event['tournament_days']])
            month_year = datetime.strptime(event['tournament_days'][0], "%Y-%m-%d").strftime("%B de %Y")
            value = f"Torneo: **{tournament_days_str} de {month_year}**."
            embed.add_field(name=f"{event['name']} (Versión {event['version']})", value=value, inline=False)
        await message.channel.send(embed=embed)
    else:
        await message.channel.send("No hay más torneos de Clash programados.")

async def handle_hclash(message):
    if "horarios" in CLASH_INFO:
        horarios_data = CLASH_INFO["horarios"]
        embed = discord.Embed(title=horarios_data.get("titulo", "Horarios de Clash"), color=discord.Color.light_grey())
        for nivel in horarios_data.get("niveles", []):
            embed.add_field(name=nivel.get("nombre", ""), value=nivel.get("horario", ""), inline=False)
        await message.channel.send(embed=embed)
    else:
        await message.channel.send("No se encontró la información de horarios de Clash.")

async def handle_pclash(message):
    if "premios" in CLASH_INFO:
        premios_data = CLASH_INFO["premios"]
        embed = discord.Embed(title=premios_data.get("titulo", "Premios de Clash"), description=premios_data.get("descripcion", ""), color=discord.Color.gold())
        for premio in premios_data.get("lista", []):
            embed.add_field(name=premio.get("lugar", ""), value=premio.get("recompensa", ""), inline=False)
        await message.channel.send(embed=embed)
    else:
        await message.channel.send("No se encontró la información de premios de Clash.")

# --- MANEJADOR DE AYUDA GLOBAL ---
async def handle_ayuda(message):
    embed = discord.Embed(title="Ayuda - El Rincón del Poro", description="Comandos disponibles:", color=discord.Color.dark_green())
    patch_commands = (
        "`p!parche` - Información del último **parche**.\n"
        "`p!campeones` - Lista de **campeones** con cambios.\n"
        "`p!ver <campeón>` - Cambios detallados del **campeón**.\n"
        "`p!objetos` - Cambios a **objetos**.\n"
        "`p!runas` - Cambios a **runas**.\n"
        "`p!siguiente` - Muestra el **siguiente parche** programado.\n"
        "`p!calendario` - Visualiza el **calendario de parches** futuros."
    )
    embed.add_field(name="--- 📜 Comandos de Parche ---", value=patch_commands, inline=False)

    clash_commands = (
        "`c!clash` - Próximo **Clash**.\n"
        "`c!calendario` - **Calendario** de Clash futuros.\n"
        "`c!horarios` - **Horarios** fase de confirmación.\n"
        "`c!premios` - Despliega los **premios**."
    )
    embed.add_field(name="--- 🏆 Comandos de Clash ---", value=clash_commands, inline=False)
    await message.channel.send(embed=embed)

# --- Punto de Entrada ---
load_config()
keep_alive()
bot.run(TOKEN)