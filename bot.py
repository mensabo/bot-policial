# -*- coding: utf-8 -*-
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update
from telegram.constants import ParseMode
import logging
import google.generativeai as genai
import random
import os # Importamos la librería 'os' para leer las variables de entorno

# --- Configuración de Logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- ¡¡IMPORTANTE!! Leemos las claves secretas desde las Variables de Entorno ---
# Estas variables las configurarás en el panel de Render, NO aquí.
TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# --- Configuración de la API de Google ---
# Solo se configura si la clave API de Gemini se ha encontrado en el entorno.
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


# --- Lista de Frases Aleatorias ---
FRASES_POLICIALES = [
    "Las mañanas son para las gestiones del guardia.",
    "Chaval América ya fue descubierta.",
    "La mejor intervención es la que no se hace.",
    "¿No estás cansado de conducir? Anda, párate aquí un ratito para descansar.",
    "Levanta el pie chaval ¿Qué quieres que cuando lleguemos estén todavía allí?.",
    "Hoy en día para lo único que hay que ir con prisa y corriendo es para salir de aqui e irnos a casa.",
    "Esto es lo que hemos ganado con tanta policía científica... antes recuperábamos los coches enteros, ahora los queman todos.",
    "En este oficio hay que estar 29 días tonto y uno listo para cobrar.",
    "Vete despacio que a las peleas hay que llegar cuando ya hayan terminao.",
    "En la última hora de servicio hay que ponerse las gafas de madera.",
    "El trabajo no hay que buscarlo, ya viene solo.",
    "...Señor, llame usted al 091 porque este no es mi sector...",
    "¿Va Usted a denunciar? Porque si no, nosotros, aqui hemos terminado.",
    "No corras chaval, no corras... que a los realmente malos ya los castigará Dios...",
    "Estamos en la calle para solucionar problemas. No todo el mundo tiene que acabar en la cárcel.",
    "Chaval, cuando yo tenía 20 años como tú...",
    "Papeleta sin novedad muchas pagas cobrarás.",
    "Niño... No intentes hacer intervenciones Americanas con medios Africanos.",
    "Nos engañarán con el sueldo, pero no con el trabajo.",
    "Chaval, tú aqui aprender no vas a aprender na, pero los huevos te los vas a tocar con las dos manos.",
    "Bueno, vamos a parar un rato, que tampoco es plan de reventar el coche a kilómetros.",
    "Los garbanzos del estado son duros pero son seguros.",
    "Chaval,... ves esa silla, si tienes ganas de trabajar siéntate en ella y espera a que se te pasen.",
    "El trabajo en un patrulla se basa en tener mucha mano izquierda y buen toreo de capote.",
    "Los funcionarios somos todos ateos, porque no conocemos otra vida mejor que esta.",
    "Compañero no te preocupes, entre lobos no se muerden, solo se ladran.",
    "A estas aturas de la noche lo único que encontramos son borrachos y problemas.",
    "Vale mas un día en la calle que 10 años de academia.",
    "Al amigo culo, al enemigo por el culo y al indiferente la legislación vigente.",
    "Que trabaje el Jefe, que pa eso cobra más.",
    "Como se que no voy a hacer bien la intervención, que la haga otro más cualificao.",
    "Reunión de pastores, oveja muerta.",
    "Aquí no he visto a nadie que lo echaran por tocarse los huevos, ahora eso sí, por currar he visto a muchos fuera.",
    "Hazte a la idea de que aquí se viene a descansar, el dinero se gana fuera.",
    "Y aquí, ¿cuándo tomamos café?.",
    "Tránquilo, a ver si te crees que vas a heredar la empresa.",
    "A mi no me pagan para esto.",
    "Desde que se inventaron eso de la Constitución, esto ya no es lo que era.",
    "De Cabo para arriba, todos son malos mientras no demuestren lo contrario.",
    "Quieto, no contestes a la radio, ya se cansarán de llamar.",
    "De las 12 p'alante, todos los gatos son pardos....",
    "Papeleta sin novedad, a fin de mes a cobrar.",
    "Chaval, tranquilo, no pasa nada si ese se escapa hoy... hay más días que longanizas.",
    "La noche está para dormir y el día para descansar.",
    "Aquí lo que se busca es la tranquilidad."
]

# --- Lista Blanca de Usuarios Autorizados ---
# Aquí SÍ puedes poner los IDs, ya que no son información secreta crítica.
# Reemplaza 123456789 con tu ID real.
USUARIOS_AUTORIZADOS = [123456789, 987654321] 


# --- Función para dividir mensajes largos ---
def dividir_mensaje(texto, limite=4096):
    trozos = []
    while len(texto) > limite:
        corte = texto.rfind('\n', 0, limite)
        if corte == -1: corte = limite
        trozos.append(texto[:corte])
        texto = texto[corte:]
    trozos.append(texto)
    return trozos

# --- Función para el comando /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in USUARIOS_AUTORIZADOS:
        await update.message.reply_text("⛔️ Acceso denegado. No tienes permiso para usar este bot.")
        return
    
    nombre_usuario = update.message.from_user.first_name
    await update.message.reply_text(
        f"¡Hola, {nombre_usuario}! Soy tu asistente policial avanzado. "
        "Hazme cualquier consulta sobre legislación o procedimientos."
    )

# --- Función principal de respuesta con IA ---
async def responder_con_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in USUARIOS_AUTORIZADOS:
        await update.message.reply_text("⛔️ Acceso denegado. No tienes permiso para usar este bot.")
        return
    
    texto_usuario = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    texto_respuesta_gemini = ""

    try:
        # Asegúrate de que este es el nombre del modelo que te funciona
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        prompt_mejorado = (
            "TÚ ERES UN ASISTENTE VIRTUAL PARA LA POLICÍA DE ESPAÑA. Tu único propósito es proporcionar información operativa y legal a agentes en servicio. "
            "Todas tus respuestas deben estar redactadas DESDE LA PERSPECTIVA DE UN AGENTE DE POLICÍA y PARA un agente de policía.\n\n"
            "Un agente de policía te plantea la siguiente consulta operativa. Tu respuesta debe ser una guía de actuación profesional, basada en la legislación española "
            "(Código Penal, LECrim, LO 4/2015) y en los protocolos policiales estandarizados.\n\n"
            "Aplica el siguiente formato HTML estrictamente:\n"
            "- Usa <b>títulos en negrita</b> para secciones.\n"
            "- Usa <u>texto subrayado</u> para citar artículos de ley.\n"
            "- Para enumerar puntos o pasos, usa el emoji del círculo azul (🔵) seguido de un espacio.\n"
            "- Usa <i>texto en cursiva</i> para notas aclaratorias.\n"
            "- Usa saltos de línea para estructurar la información.\n"
            "- NO uses ninguna otra etiqueta HTML aparte de <b>, <i>, y <u>.\n\n"
            "CONSULTA DEL AGENTE:\n"
            f'"{texto_usuario}"'
        )
        
        response = model.generate_content(prompt_mejorado)
        texto_respuesta_gemini = response.text
        
        frase_aleatoria = random.choice(FRASES_POLICIALES)
        descargo_responsabilidad = (
            "\n\n---\n"
            f"<i>{frase_aleatoria}</i>"
        )
        respuesta_completa = texto_respuesta_gemini + descargo_responsabilidad
        
        trozos_mensaje = dividir_mensaje(respuesta_completa)
        
        for trozo in trozos_mensaje:
            await update.message.reply_text(
                text=trozo,
                parse_mode=ParseMode.HTML
            )
        
    except Exception as e:
        logging.error(f"Error al procesar y enviar la respuesta: {e}")
        if "Can't parse entities" in str(e):
            logging.warning("Error de formato HTML. Enviando como texto plano.")
            trozos_sin_formato = dividir_mensaje(texto_respuesta_gemini)
            for trozo in trozos_sin_formato:
                 await update.message.reply_text(trozo)
        else:
            await update.message.reply_text("Lo siento, he tenido un problema al procesar la consulta. Inténtalo de nuevo más tarde.")

# --- Función principal que inicia el bot ---
def main():
    """Configura y ejecuta el bot, verificando primero las claves de entorno."""
    
    # Comprobación para asegurarse de que las claves existen en el entorno del servidor
    if not TOKEN_TELEGRAM or not GEMINI_API_KEY:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! ERROR CRÍTICO: Faltan las variables de entorno TOKEN_TELEGRAM o GEMINI_API_KEY.")
        print("!!! Asegúrate de haberlas configurado en el panel de tu servidor (Render).")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return # Detiene el bot si no encuentra las claves

    application = Application.builder().token(TOKEN_TELEGRAM).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_con_gemini))
    
    print("Bot seguro iniciado (leyendo claves desde el entorno).")
    application.run_polling()

if __name__ == '__main__':
    main()