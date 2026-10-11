ProBot Tounsi — Discord bot starter

المزايا:
- Slash commands: /help, /ping, /serverinfo, /userinfo, /rank
- Moderation: /ban, /kick, /timeout, /unban, /clear, /warn, /warnings
- Welcome + AutoRole + Logs: /setwelcome, /setautorole, /setlogs
- Tickets: /ticket, /close_ticket
- يحفظ XP والإنذارات والتذاكر في data.json

تشغيل Windows:
1) فك الضغط وافتح CMD داخل المجلد.
2) py -m pip install -r requirements.txt
3) من Discord Developer Portal أنشئ Bot وانسخ TOKEN.
4) فعّل Server Members Intent و Message Content Intent.
5) في CMD اكتب: set DISCORD_TOKEN=PASTE_YOUR_TOKEN_HERE
6) شغّل: py bot.py

مهم: لا تبعث TOKEN لأي شخص ولا تنشره.
24/24: يلزم استضافة دائمة أو PC يبقى شغال مع الإنترنت. المجاني موش مضمون 24/24.
على الاستضافة حط DISCORD_TOKEN في Secrets/Environment Variables. يلزم التخزين الدائم للملفين data.json و config.json.
هذا Starter قابل للتطوير، موش نسخة مطابقة من ProBot الرسمي.
