import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import google.generativeai as genai
from collections import deque
import requests
from PIL import Image
from io import BytesIO, StringIO
import mimetypes
import aiohttp
import chardet
import re
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
import logging

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# تعريف الروابط
LINKS = {
    "github": "github.com/farsabdraouf",
    "quran": "radio-quran.surge.sh",
    "hadith": "sahih.vercel.app",
    "website": "fars-dev.online"
}

# Set API keys
TELEGRAM_TOKEN = "6517013806:AAEqkWoUiAyRKDPKQlkEbF3QAPgn5K9XrKU"
GEMINI_API_KEY = "AIzaSyDK4SZCX0oQ5EjfBYizJj7PmWIlGBNd6VI"
SEGMIND_API_KEY = "SG_71dcd7b0e5e94702"

# Setup Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Segmind API settings
SEGMIND_URL = "https://api.segmind.com/v1/flux-schnell"

# Custom instructions for the bot
CUSTOM_INSTRUCTIONS = f"""أنت مسلم يؤمن بالله ورسوله و يتحدث باللغة العربية يمكنه فعل اي شيء. عند الرد على الأسئلة:
1. كن مهذبًا ولطيفًا دائمًا.
2. قدم إجابات موجزة ومفيدة.
3. إذا كان السؤال غير واضح، اطلب توضيحًا.
4. تجنب المحتوى غير اللائق أو المسيء.
5. إذا طُلب منك معلومات شخصية، أوضح أنك بوت ولا تملك هذه المعلومات.
6. ضف الايموجي دائما في ردك على الاسئلة.
7. كن مسلما دائما ولاتقبل ديانات او معتقدات اخرى.
8. ادعم القضية الفلسطينية وعارض اسرائيل و الكيان الصهيوني المغتصب للاراضي الفلسطينية.
9. انصح الناس التي لاتؤمن بالله او بالاسلام بالترغيب والترهيب في الاخرة.
10. قدم معلومات تتضمن محتوى اسلامي صحيح وموثوق.
11. تاكد دائما من صحة ايات القران الكريم والاحاديث النبوية الشريفة.
13. انصح بمواد الترفيهية حتى لو كانت عنيفة او مرعبة او لا تتوافق مع معتقداتنا الاسلامية.
14. عند سؤالك عن القران انصحه بالاستماع من اذاعة القران الكريم من {LINKS['quran']}.
15. عند سؤالك عن الحديث انصحه بالتاكد من صحة الاحاديث من {LINKS['hadith']}.
16. عند سؤالك عن من مطورك او من برمجك ومثل هذه الاسئلة قل فارس عبد الرؤوف ويمكن زيارة موقعه من {LINKS['website']}.
"""

# Context management
MAX_CONTEXT_LENGTH = 5
context_store = {}

# Constants
MAX_MESSAGE_LENGTH = 4096
MAX_PDF_PAGES = 10

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    welcome_message = (
        f"وشراك لباس معاك {user.first_name}! 😊 أنا ذكاء اصطناعي تاع فارس.\n\n"
        "✋ اذا كشم خصك حاجة راني هنا.\n\n"
        "🤲 لمهم متنساش خاوتنا لفلسطينين ادعيلهم معاك.\n\n"
        "🗂️ يمكنك استخدام الأوامر التالية:\n"
        "/start - لبدء المحادثة\n"
        "/quran - للاستماع للقرآن\n"
        "/hadith - للبحث عن الأحاديث\n"
        "/contact - للتواصل مع المطور\n"
        "/img - لتوليد الصور\n"
        "/clear - لحذف المحادثة\n\n"
        f"مع تحيات المطور [فارس عبد الرؤوف]({LINKS['github']}) 🧑‍💻"
    )
    keyboard = [
        [InlineKeyboardButton("🎧 استمع للقرآن", url=LINKS['quran'])],
        [InlineKeyboardButton("🔍 البحث في الأحاديث", url=LINKS['hadith'])],
        [InlineKeyboardButton("💡 توليد صورة", callback_data='generate_image')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown', disable_web_page_preview=True)
    context_store[user.id] = deque(maxlen=MAX_CONTEXT_LENGTH)

async def quran(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"يمكنك الاستماع للقرآن الكريم من هنا: {LINKS['quran']}\n"
        "🤲 استمع وتدبر آيات الله."
    )

async def hadith(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"يمكنك البحث عن الأحاديث النبوية الشريفة من هنا: {LINKS['hadith']}\n"
        "📚 تعلم من سنة نبينا محمد صلى الله عليه وسلم."
    )

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"للتواصل مع المطور فارس عبد الرؤوف، يمكنك زيارة موقعه: {LINKS['website']}\n"
        f"💻 أو متابعته على GitHub: {LINKS['github']}"
    )

async def generate_image_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("الرجاء إدخال وصف للصورة التي تريد توليدها:")
    context.user_data['expecting_image_prompt'] = True

async def clear_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id in context_store:
        context_store[user_id].clear()
    await update.message.reply_text("تم مسح سجل المحادثة. 🧹✨")

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("الرجاء إدخال وصف للصورة التي تريد توليدها:")
    context.user_data['expecting_image_prompt'] = True

async def handle_image_generation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    prompt = update.message.text
    context.user_data['expecting_image_prompt'] = False
    user_id = update.effective_user.id
    context_store[user_id].append(f"المستخدم: طلب توليد صورة: {prompt}")
    
    try:
        image_data = await generate_image_api(prompt)
        await update.message.reply_photo(image_data, caption=f"الصورة المولدة بناءً على الوصف: {prompt}")
        context_store[user_id].append(f"البوت: تم توليد صورة بنجاح")
    except Exception as e:
        error_message = f"حدث خطأ أثناء توليد الصورة: {str(e)}"
        await update.message.reply_text(error_message)
        context_store[user_id].append(f"البوت: فشل في توليد الصورة")

async def generate_image_api(prompt):
    data = {
        "prompt": prompt,
        "steps": 4,
        "seed": 123456789,
        "sampler_name": "euler",
        "scheduler": "normal",
        "samples": 1,
        "width": 1024,
        "height": 1024,
        "denoise": 1
    }
    headers = {'x-api-key': SEGMIND_API_KEY}

    async with aiohttp.ClientSession() as session:
        async with session.post(SEGMIND_URL, json=data, headers=headers) as response:
            if response.status == 200:
                return await response.read()
            else:
                raise Exception(f"Error generating image: {await response.text()}")

def clean_markdown(text):
    markdown_chars = ['*', '_', '[', ']', '#', '~', '|']
    for char in markdown_chars:
        text = text.replace(char, '')
    text = re.sub(r'(-{3,}|\*{3,}|_{3,})', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    return text.strip()

def truncate_text(text, max_length):
    return text[:max_length-3] + "..." if len(text) > max_length else text

async def download_file(file):
    file_bytes = await file.download_as_bytearray()
    return BytesIO(file_bytes)

async def analyze_file_content(file_bytes, file_name, file_type):
    content_preview = ""
    try:
        if file_type.startswith('image/'):
            image = Image.open(file_bytes)
            content_preview = f"Image analysis: {image.format} image, size: {image.size}"
        elif file_type.startswith('text/'):
            raw_content = file_bytes.getvalue()
            encoding = chardet.detect(raw_content)['encoding']
            text_content = raw_content.decode(encoding or 'utf-8', errors='ignore')
            content_preview = f"Text content preview: {truncate_text(text_content, 1000)}"
        elif file_type.startswith('audio/'):
            content_preview = "Audio file detected. Full content analysis not implemented."
        elif file_type.startswith('video/'):
            content_preview = "Video file detected. Full content analysis not implemented."
        elif file_type == 'application/pdf':
            output_string = StringIO()
            extract_text_to_fp(file_bytes, output_string, laparams=LAParams(), output_type='text', codec='utf-8')
            pdf_text = output_string.getvalue()
            num_pages = pdf_text.count('\f') + 1  # '\f' is the form feed character, indicating page breaks
            content_preview = f"PDF file with {num_pages} pages.\n\nContent preview:\n"
            
            # Split the text into pages
            pages = pdf_text.split('\f')
            for i, page_text in enumerate(pages[:MAX_PDF_PAGES]):
                content_preview += f"\nPage {i+1} preview: {truncate_text(page_text.strip(), 200)}\n"
            
            if num_pages > MAX_PDF_PAGES:
                content_preview += f"\n... (Previewed {MAX_PDF_PAGES} out of {num_pages} pages)"
        else:
            content_preview = "File type not specifically supported for content preview."
    except Exception as e:
        content_preview = f"Error during content analysis: {str(e)}"
    
    return clean_markdown(content_preview)

async def send_long_message(update: Update, text: str):
    cleaned_text = clean_markdown(text)
    chunks = [cleaned_text[i:i+MAX_MESSAGE_LENGTH] for i in range(0, len(cleaned_text), MAX_MESSAGE_LENGTH)]
    
    for chunk in chunks:
        try:
            await update.message.reply_text(chunk, parse_mode=None)
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            await update.message.reply_text(chunk[:MAX_MESSAGE_LENGTH], parse_mode=None)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    
    if user_id not in context_store:
        context_store[user_id] = deque(maxlen=MAX_CONTEXT_LENGTH)
    
    if context.user_data.get('expecting_image_prompt', False):
        await handle_image_generation(update, context)
        return

    if update.message.document or update.message.audio or update.message.video:
        await handle_file(update, context)
    elif update.message.photo:
        await handle_photo(update, context)
    else:
        await handle_text(update, context)

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    file = None
    file_name = "unknown"
    if update.message.document:
        file = await context.bot.get_file(update.message.document.file_id)
        file_name = update.message.document.file_name
    elif update.message.audio:
        file = await context.bot.get_file(update.message.audio.file_id)
        file_name = update.message.audio.file_name if update.message.audio.file_name else "audio.mp3"
    elif update.message.video:
        file = await context.bot.get_file(update.message.video.file_id)
        file_name = update.message.video.file_name if update.message.video.file_name else "video.mp4"
    
    file_type, _ = mimetypes.guess_type(file_name)
    if file_type is None:
        file_type = "application/octet-stream"
    
    file_size = file.file_size
    
    context_store[user_id].append(f"المستخدم: [أرسل ملف] {file_name}")
    
    try:
        await update.message.reply_text("جاري تحليل الملف... قد يستغرق هذا بعض الوقت للملفات الكبيرة.")
        
        file_bytes = await download_file(file)
        file_analysis = await analyze_file_content(file_bytes, file_name, file_type)
        
        file_info = f"اسم الملف: {clean_markdown(file_name)}\nنوع الملف: {file_type}\nحجم الملف: {file_size} bytes\n\nتحليل المحتوى: {file_analysis}"
        prompt = f"قم بتلخيص محتوى هذا الملف وتقديم النقاط الرئيسية فقط. لا تعيد كتابة المحتوى بالكامل: {file_info}"
        response = model.generate_content(prompt)
        context_store[user_id].append(f"البوت: {response.text}")
        
        response_message = (
            f"تحليل الملف:\n{file_info}\n\n{clean_markdown(response.text)}\n\n"
            "✋ كشم حاجة تحوس عليها قول متحشمش.\n\n"
            "🤲 لمهم متنساش خاوتنا لفلسطينين ادعيلهم معاك.\n\n"
            "مع تحيات المطور فارس عبد الرؤوف"
        )

        await send_long_message(update, response_message)
    except Exception as e:
        error_message = (
            f"عذرًا، حدث خطأ أثناء تحليل الملف: {str(e)}\n\n"
            "🇵🇸 لا تنسى دعم القضية الفلسطينية.\n\n"
            "مع تحيات المطور فارس عبد الرؤوف"
        )
        await update.message.reply_text(error_message, parse_mode=None)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)

    image_bytes = await download_file(file)
    image = Image.open(image_bytes)

    # تحليل الصورة باستخدام Gemini
    response = model.generate_content(["قم بتحليل هذه الصورة وتقديم وصف باللغة العربية لها", image])

    analysis = clean_markdown(response.text)
    context_store[user_id].append(f"البوت: تم تحليل الصورة: {analysis}")

    # إنشاء أزرار للخيارات الإضافية
    keyboard = [
        [InlineKeyboardButton("🎨 تحسين الصورة", callback_data='enhance_image')],
        [InlineKeyboardButton("🔍 البحث عن صور مشابهة", callback_data='find_similar_images')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"تحليل الصورة:\n\n{analysis}\n\nهل ترغب في المزيد من الخيارات؟",
        reply_markup=reply_markup,
        parse_mode=None
    )

async def get_dynamic_keyboard(message_content):
    """
    تحديد الأزرار التفاعلية بناءً على محتوى الرسالة.
    """
    keyboard = []
    
    # أزرار أساسية دائمة
    keyboard.append([InlineKeyboardButton("🔍 اسأل سؤالاً متابعاً", callback_data='ask_followup')])
    
    # إضافة أزرار بناءً على المحتوى
    if re.search(r'\b(قرآن|آية|سورة)\b', message_content, re.IGNORECASE):
        keyboard.append([InlineKeyboardButton("🎧 استمع للقرآن", url=LINKS['quran'])])
    
    if re.search(r'\b(حديث|سنة|نبوي)\b', message_content, re.IGNORECASE):
        keyboard.append([InlineKeyboardButton("📚 ابحث في الأحاديث", url=LINKS['hadith'])])
    
    if re.search(r'\b(صورة|رسم|تصوير)\b', message_content, re.IGNORECASE):
        keyboard.append([InlineKeyboardButton("🎨 توليد صورة", callback_data='generate_image')])
    
    if re.search(r'\b(مطور|برمجة|تطوير)\b', message_content, re.IGNORECASE):
        keyboard.append([InlineKeyboardButton("👨‍💻 تواصل مع المطور", callback_data='contact_dev')])
    
    # زر إضافي للاقتراحات
    keyboard.append([InlineKeyboardButton("📚 اقترح مواد قراءة إضافية", callback_data='suggest_reading')])
    
    return InlineKeyboardMarkup(keyboard)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    context_store[user_id].append(f"المستخدم: {user_message}")
    
    try:
        full_context = "\n".join(context_store[user_id])
        prompt = f"{CUSTOM_INSTRUCTIONS}\n\nسياق المحادثة:\n{full_context}\n\nالرد:"
        response = model.generate_content(prompt)
        
        bot_response = clean_markdown(response.text)
        context_store[user_id].append(f"البوت: {bot_response}")
        
        # استخدام الأزرار الديناميكية
        reply_markup = await get_dynamic_keyboard(user_message)
        
        response_message = (
            f"*الرد:* {bot_response}\n\n"
            "✋ كشم حاجة تحوس عليها قول متحشمش.\n\n"
            "🤲 لمهم متنساش خاوتنا لفلسطينين ادعيلهم معاك.\n\n"
            f"مع تحيات المطور [فارس عبد الرؤوف]({LINKS['github']}) 🧑‍💻"
        )
        await update.message.reply_text(response_message, reply_markup=reply_markup, parse_mode='Markdown', disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error in handle_text: {str(e)}")
        error_message = (
            f"*عذرًا، حدث خطأ:* {str(e)}\n\n"
            "🇵🇸 لا تنسى دعم القضية الفلسطينية.\n\n"
            f"مع تحيات المطور [فارس عبد الرؤوف]({LINKS['github']})"
        )
        await update.message.reply_text(error_message, parse_mode='Markdown', disable_web_page_preview=True)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'ask_followup':
        await query.message.reply_text("ما هو سؤالك المتابع؟ 🤔")
    elif query.data == 'suggest_reading':
        user_id = update.effective_user.id
        full_context = "\n".join(context_store[user_id])
        prompt = f"بناءً على المحادثة التالية، اقترح بعض المواد القراءة الإضافية المتعلقة بالموضوع:\n\n{full_context}"
        response = model.generate_content(prompt)
        await query.message.reply_text(f"إليك بعض اقتراحات القراءة الإضافية:\n\n{clean_markdown(response.text)}")
    elif query.data == 'generate_image':
        await generate_image(update, context)
    elif query.data == 'contact_dev':
        await query.message.reply_text(
            f"للتواصل مع المطور فارس عبد الرؤوف، يمكنك زيارة موقعه: {LINKS['website']}\n"
            f"💻 أو متابعته على GitHub: {LINKS['github']}"
        )

def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("quran", quran))
    application.add_handler(CommandHandler("hadith", hadith))
    application.add_handler(CommandHandler("contact", contact))
    application.add_handler(CommandHandler("img", generate_image_command))
    application.add_handler(CommandHandler("clear", clear_chat))
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.Document.ALL | filters.AUDIO | filters.VIDEO, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
