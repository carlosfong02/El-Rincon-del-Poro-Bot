# El Rincón del Poro - Bot de Discord (BETA v1.1.0)

¡Bienvenido a "El Rincón del Poro"! Este es un bot de Discord multifuncional diseñado para la comunidad de League of Legends de habla hispana. Proporciona anuncios automáticos y comandos interactivos para toda la información relevante sobre parches y torneos de Clash.

Este proyecto fue construido con Python y demuestra un pipeline de datos completo, desde la extracción (Web Scraping) y el procesamiento (lógica de calendario) hasta la entrega de información a través de una API (Discord).

## 🚀 Características Principales

* **Scraping Web Avanzado:** Extrae información detallada (texto, imágenes, íconos y estadísticas) directamente de la página oficial de notas de parche de LoL usando `Requests` y `BeautifulSoup`.
* **Sistema de Comandos Intuitivo:** Utiliza prefijos temáticos (`p!` para Parches, `c!` para Clash) para una fácil navegación.
* **Anuncios Proactivos:** El bot es "consciente del tiempo" gracias a la librería `pytz`. Revisa un calendario (`.json`) y envía anuncios automáticamente en la zona horaria de CDMX.
* [cite_start]**Anuncios de Clash:** Notifica a los usuarios sobre el inicio de la formación de equipos, los días del torneo y envía un recordatorio de "última llamada" 10 minutos antes del cierre de inscripciones [cite: 141-151].
* [cite_start]**Anuncios de Parche:** Avisa un día antes de un parche con una cuenta regresiva [cite: 132-135] [cite_start]y anuncia las notas cuando están disponibles [cite: 136-138].
* **Respuestas Visuales:** Utiliza "Embeds" de Discord para presentar la información de manera limpia, profesional y visualmente atractiva, incluyendo imágenes de campeones, íconos de habilidades y resúmenes de parches.
* **Gestión de Estado:** Utiliza archivos JSON (`sent_reminders.json`) y `.txt` (`last_patch_url.txt`) como una memoria simple para evitar anuncios duplicados.
* **Manejo Seguro de Secretos:** Todas las claves (token del bot, ID del canal) se gestionan de forma segura a través de variables de entorno (`.env`).

## 🛠️ Tecnologías Utilizadas
* **Lenguaje:** Python
* **API:** Py-cord (discord.py)
* **Extracción de Datos:** Requests, BeautifulSoup4
* **Manejo de Datos:** JSON
* **Manejo de Tareas/Tiempo:** Pytz, Datetime
* **Gestión de Secretos:** python-dotenv

## ⚙️ Comandos Disponibles
(Extraído del comando `!ayuda` del bot) [cite_start][cite: 182-184]

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