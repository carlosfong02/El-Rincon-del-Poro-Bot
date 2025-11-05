# El Rincón del Poro (Bot de Discord de LoL)

![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![Discord.py](https://img.shields.io/badge/py--cord-v2.6.1-7289DA?logo=discord)
![Status](https://img.shields.io/badge/status-BETA_v1.1.0-orange)

Un bot de Discord multifuncional en español que sirve como un pipeline de datos automatizado para la comunidad de League of Legends.

Este proyecto fue construido con Python y demuestra un pipeline de datos completo. Utiliza **web scraping** (`Requests` y `BeautifulSoup`) para extraer y parsear HTML no estructurado de la web oficial de LoL, y un **sistema de tareas proactivo** (`@tasks.loop`) consciente de la zona horaria (`pytz`) para enviar notificaciones automáticas y recordatorios con cuentas regresivas, entregando la información a través de la API de Discord.

---

## 🚀 Características Principales

* **Scraping Web Avanzado:** Extrae información detallada (texto, imágenes de resumen, íconos de habilidades) directamente de la página de notas de parche.
* **Sistema de Comandos Intuitivo:** Utiliza prefijos temáticos (`p!` para Parches, `c!` para Clash) para una navegación fácil e intuitiva.
* **Anuncios Proactivos:** El bot es "consciente del tiempo" gracias a la librería `pytz`. Revisa un calendario (`.json`) y envía anuncios automáticamente en la zona horaria de CDMX.
* **Anuncios de Clash:** Notifica a los usuarios sobre el inicio de la formación de equipos, los días del torneo y envía un recordatorio de "última llamada" 10 minutos antes del cierre de inscripciones.
* **Anuncios de Parche:** Avisa un día antes de un parche con una cuenta regresiva y anuncia las notas cuando están disponibles.
* **Respuestas Visuales:** Utiliza "Embeds" de Discord para presentar la información de manera limpia, profesional y visualmente atractiva, incluyendo imágenes de campeones, íconos de habilidades y resúmenes.
* **Gestión de Estado:** Utiliza archivos JSON (`sent_reminders.json`) y `.txt` (`last_patch_url.txt`) como una memoria simple para evitar anuncios duplicados.
* **Manejo Seguro de Secretos:** Todas las claves (token del bot, ID del canal) se gestionan de forma segura a través de variables de entorno (`.env`).

---

## 🛠️ Tecnologías Utilizadas

* **Lenguaje:** Python
* **API:** Py-cord (discord.py)
* **Extracción de Datos:** Requests, BeautifulSoup4
* **Manejo de Datos:** JSON
* **Manejo de Tareas/Tiempo:** Pytz, Datetime
* **Gestión de Secretos:** python-dotenv

---

## ⚙️ Comandos Disponibles

### --- 📜 Comandos de Parche ---
* `p!parche` - Información del último **parche**.
* `p!campeones` - Lista de **campeones** con cambios.
* `p!ver <campeón>` - Cambios detallados del **campeón**.
* `p!objetos` - Cambios a **objetos**.
* `p!runas` - Cambios a **runas**.
* `p!siguiente` - Muestra el **siguiente parche** programado.
* `p!calendario` - Visualiza el **calendario de parches** futuros.

### --- 🏆 Comandos de Clash ---
* `c!clash` - Próximo **Clash**.
* `c!calendario` - **Calendario** de Clash futuros.
* `c!horarios` - **Horarios** fase de confirmación.
* `c!premios` - Despliega los **premios**.

---

## 📦 Instalación Local

1.  Clona el repositorio:
    ```bash
    git clone [https://github.com/carlosfong02/tu-repositorio.git](https://github.com/carlosfong02/tu-repositorio.git)
    cd tu-repositorio
    ```
2.  Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```
3.  Crea un archivo `.env` en la raíz y añade tus secretos:
    ```
    DISCORD_TOKEN="TU_TOKEN_DE_BOT"
    DISCORD_CHANNEL_ID="EL_ID_DEL_CANAL_DE_ANUNCIOS"
    ```
4.  Ejecuta el bot:
    ```bash
    python bot.py
    ```

## 🚀 Despliegue 24/7 en Replit

Este bot está configurado para funcionar 24/7 de forma gratuita utilizando la plataforma [Replit](https://replit.com/) y un servicio de monitoreo externo.

### Cómo Funciona

El despliegue se basa en un truco simple para evitar que los "Repls" gratuitos se "duerman" por inactividad:

1.  **Servidor Web Ligero:** Se utiliza la biblioteca **Flask** (ver `keep_alive.py`) para crear un pequeño servidor web que se ejecuta en un hilo paralelo junto al bot de Discord.
2.  **Monitoreo Externo:** Un servicio gratuito como [UptimeRobot](https://uptimerobot.com/) se configura para "visitar" la URL pública de este servidor web (la dirección `.repl.app`) cada 5 minutos.
3.  **Actividad Constante:** Esta visita constante simula tráfico y le indica a Replit que el proyecto está activo, evitando que el bot se desconecte.

### Nuevas Dependencias para Despliegue

* **Flask:** Para crear el servidor web.
* **UptimeRobot:** (Servicio externo) Para el monitoreo.
* **keep_alive.py:** El script que contiene la lógica del servidor web.
