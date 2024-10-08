# بوت التيليجرام الذكي 🤖

<div dir="rtl">

## نظرة عامة 🌟

بوت التيليجرام الذكي هو روبوت محادثة متطور يستخدم تقنيات الذكاء الاصطناعي لتوفير تجربة تفاعلية غنية للمستخدمين. يتميز البوت بقدرته على الإجابة عن الأسئلة، وتحليل الصور، وتوليد النصوص والصور، بالإضافة إلى توفير معلومات قيمة حول القرآن الكريم والأحاديث النبوية الشريفة.

## المميزات الرئيسية 🚀

- **محادثة ذكية**: يستخدم نموذج Gemini من Google لتوفير ردود دقيقة ومفيدة.
- **تحليل الصور**: قادر على وصف وتحليل الصور المرسلة.
- **توليد الصور**: يمكنه إنشاء صور بناءً على وصف نصي باستخدام API Segmind.
- **دعم متعدد الوسائط**: يتعامل مع النصوص والصور والملفات (PDF, الصوت، الفيديو).
- **محتوى إسلامي**: يوفر روابط للاستماع للقرآن الكريم والبحث في الأحاديث النبوية.
- **واجهة تفاعلية**: يستخدم أزرار وقوائم تفاعلية لتسهيل التنقل والاستخدام.

## الأوامر الرئيسية 📋

- `/start`: بدء المحادثة مع البوت
- `/quran`: الحصول على رابط للاستماع للقرآن الكريم
- `/hadith`: الحصول على رابط للبحث في الأحاديث النبوية
- `/contact`: معلومات التواصل مع المطور
- `/img`: بدء عملية توليد صورة
- `/clear`: مسح سجل المحادثة

## التثبيت والإعداد 🛠️

1. **المتطلبات الأساسية**:
   - Python 3.7+
   - حساب Telegram Bot
   - مفتاح API لـ Google Gemini
   - مفتاح API لـ Segmind (لتوليد الصور)

2. **تثبيت المكتبات المطلوبة**:
   ```
   pip install python-telegram-bot google-generativeai Pillow PyPDF2 aiohttp chardet
   ```

3. **إعداد المتغيرات البيئية**:
   - قم بإنشاء ملف `.env` في مجلد المشروع وأضف المتغيرات التالية:
     ```
     TELEGRAM_TOKEN=your_telegram_bot_token
     GEMINI_API_KEY=your_gemini_api_key
     SEGMIND_API_KEY=your_segmind_api_key
     ```

4. **تشغيل البوت**:
   ```
   python telegram_ai_bot.py
   ```

## الاستخدام 💬

1. ابدأ محادثة مع البوت على Telegram باستخدام الأمر `/start`.
2. اطرح أسئلتك أو أرسل صورًا للتحليل.
3. استخدم الأزرار التفاعلية للوصول إلى مزيد من الخيارات والمعلومات.

## التخصيص 🎨

يمكنك تخصيص سلوك البوت عن طريق تعديل المتغير `CUSTOM_INSTRUCTIONS` في الكود. هذا يتيح لك تغيير شخصية البوت وطريقة استجابته.

## المساهمة 🤝

نرحب بالمساهمات لتحسين هذا البوت! إذا كان لديك اقتراحات أو تحسينات، يرجى فتح issue أو تقديم pull request.

## الترخيص 📄

هذا المشروع مرخص تحت [MIT License](LICENSE).

## الاتصال 📞

للمزيد من المعلومات أو الاستفسارات، يمكنك التواصل مع المطور [فارس عبد الرؤوف](https://github.com/farsabdraouf).

---

🌟 لا تنسوا دعم القضية الفلسطينية 🇵🇸

</div>
