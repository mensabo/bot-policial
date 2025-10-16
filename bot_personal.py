# -*- coding: utf-8 -*-
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update
from telegram.constants import ParseMode
import logging
import google.generativeai as genai
import random
import os

# --- Configuración de Logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- Leemos las claves secretas desde las Variables de Entorno ---
TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM_PERSONAL") 
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# --- Configuración de la API de Google ---
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


# --- Lista Blanca de Usuarios Autorizados ---
# ¡IMPORTANTE! Pon aquí tu ID y el ID de Yaiza.
USUARIOS_AUTORIZADOS = [5055449, 1234567890] 


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
        await update.message.reply_text("⛔️ Hola, soy un bot privado.")
        return
    
    nombre_usuario = update.message.from_user.first_name
    await update.message.reply_text(
        f"¡Hola, {nombre_usuario}! Estoy aquí para ayudaros en lo que necesitéis. 😊"
    )

# --- Función principal de respuesta con IA (VERSIÓN CON ESTÉTICA MEJORADA) ---
async def responder_con_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in USUARIOS_AUTORIZADOS:
        await update.message.reply_text("⛔️ Hola, soy un bot privado.")
        return
    
    texto_usuario = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    texto_respuesta_gemini = ""

    try:
        model = genai.GenerativeModel('gemini-2.5-pro') # O el modelo que te funcione
        
        # --- ¡¡PROMPT CON REGLAS DE ESTILO DETALLADAS!! ---
        prompt_mejorado = (
            "Eres un asistente de IA amable, creativo, servicial y muy capaz. Estás en un chat privado con Yaiza y Diego. "
            "Tu objetivo es ayudar a Yaiza con sus proyectos, responder a sus dudas generales y facilitar cualquier tarea que necesiten. "
            "Dirígete a ellos de forma cercana y positiva.\n\n"
            
            "Aplica el siguiente formato HTML estrictamente para que tus respuestas sean visualmente atractivas:\n"
            "- Usa <b>títulos en negrita</b> para las ideas principales o secciones.\n"
            "- Usa <u>texto subrayado</u> para resaltar palabras o conceptos muy importantes.\n"
            "- Para listas o pasos, usa el emoji de la chispa (✨) seguido de un espacio.\n"
            "- Usa <i>texto en cursiva</i> para notas, ejemplos o comentarios adicionales.\n"
            "- Usa saltos de línea para estructurar bien la información.\n"
            "- NO uses ninguna otra etiqueta HTML aparte de <b>, <i>, y <u>.\n\n"
            
            "La consulta es:\n"
            f'"{texto_usuario}"'
        )
        
        response = model.generate_content(prompt_mejorado)
        texto_respuesta_gemini = response.text
        
        # Pie de mensaje personalizado
        pie_mensaje = "\n\n---\n<i>Vuestro asistente personal ✨</i>"
        respuesta_completa = texto_respuesta_gemini + pie_mensaje
        
        trozos_mensaje = dividir_mensaje(respuesta_completa)
        
        for trozo in trozos_mensaje:
            await update.message.reply_text(
                text=trozo,
                parse_mode=ParseMode.HTML
            )
        
    except Exception as e:
        logging.error(f"Error al procesar la respuesta: {e}")
        if "Can't parse entities" in str(e):
            logging.warning("Error de formato HTML. Enviando como texto plano.")
            trozos_sin_formato = dividir_mensaje(texto_respuesta_gemini)
            for trozo in trozos_sin_formato:
                 await update.message.reply_text(trozo)
        else:
            await update.message.reply_text("Lo siento, he tenido un problema al procesar la consulta. Inténtalo de nuevo más tarde.")

# --- Función principal que inicia el bot ---
def main():
    if not TOKEN_TELEGRAM or not GEMINI_API_KEY:
        print("!!! ERROR CRÍTICO: Faltan las variables de entorno TOKEN_TELEGRAM_PERSONAL o GEMINI_API_KEY.")
        return

    application = Application.builder().token(TOKEN_TELEGRAM).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_con_gemini))
    
    print("Bot personal para Yaiza y Diego (v. Estilo Mejorado) iniciado.")
    application.run_polling()

if __name__ == '__main__':
    main()