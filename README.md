# El Rincón del Poro (Bot de Discord de LoL)

![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![Discord.py](https://img.shields.io/badge/py--cord-v2.6.1-7289DA?logo=discord)
![Status](https://img.shields.io/badge/status-BETA_v1.1.0-orange)

Un bot de Discord multifuncional en español que sirve como un pipeline de datos automatizado para la comunidad de League of Legends.

Este proyecto fue construido con Python y demuestra un pipeline de datos completo. Utiliza **web scraping** (`Requests` y `BeautifulSoup`) para extraer y parsear HTML no estructurado de la web oficial de LoL, y un **sistema de tareas proactivo** (`@tasks.loop`) consciente de la zona horaria (`pytz`) para enviar notificaciones automáticas y recordatorios con cuentas regresivas, entregando la información a través de la API de Discord.

---

## 🚀 Características Principales

* [cite_start]**Scraping Web Avanzado:** Extrae información detallada (texto, imágenes de resumen, íconos de habilidades) [cite: 180-186, 188-202] directamente de la página de notas de parche.
* [cite_start]**Sistema de Comandos Intuitivo:** Utiliza prefijos temáticos (`p!` para Parches, `c!` para Clash) [cite: 225-231] para una navegación fácil e intuitiva.
* [cite_start]**Anuncios Proactivos:** El bot es "consciente del tiempo" gracias a la librería `pytz` [cite: 174-175, 204-207]. [cite_start]Revisa un calendario (`.json`) y envía anuncios automáticamente en la zona horaria de CDMX [cite: 207-215].
* [cite_start]**Anuncios de Clash:** Notifica a los usuarios sobre el inicio de la formación de equipos [cite: 216-220][cite_start], los días del torneo [cite: 220-223] [cite_start]y envía un recordatorio de "última llamada" 10 minutos antes del cierre de inscripciones [cite: 223-227].
* [cite_start]**Anuncios de Parche:** Avisa un día antes de un parche con una cuenta regresiva [cite: 207-212] [cite_start]y anuncia las notas cuando están disponibles [cite: 212-215].
* [cite_start]**Respuestas Visuales:** Utiliza "Embeds" de Discord [cite: 232-234, 237-239] para presentar la información de manera limpia, profesional y visualmente atractiva, incluyendo imágenes de campeones, íconos de habilidades y resúmenes.
* [cite_start]**Gestión de Estado:** Utiliza archivos JSON (`sent_reminders.json`) y `.txt` (`last_patch_url.txt`) [cite: 203, 214-215] como una memoria simple para evitar anuncios duplicados.
* [cite_start]**Manejo Seguro de Secretos:** Todas las claves (token del bot, ID del canal) se gestionan de forma segura a través de variables de entorno (`.env`) [cite: 173-174].

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

[cite_start](Esta es la versión final y limpia de tu comando de ayuda [cite: 253-257])

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
4.  Crea los archivos de configuración (`champions.txt`, `patch_dates.json`, `clash_dates.json`, `clash_info.json`).
5.  Ejecuta el bot:
    ```bash
    python bot.py
    ```