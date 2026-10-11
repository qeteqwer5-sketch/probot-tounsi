import os, json, logging
from datetime import timedelta
import discord
from discord import app_commands
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
logging.basicConfig(level=logging.INFO)
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

def load(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): return default
def save(path, obj):
    with open(path, "w", encoding="utf-8") as f: json.dump(obj, f, ensure_ascii=False, indent=2)

config = load("config.json", {"welcome_channel_id":0,"log_channel_id":0,"autorole_id":0,"ticket_counter":0})
data = load("data.json", {"warnings":{},"levels":{},"tickets":{}})

class ProBot(commands.Bot):
    async def setup_hook(self):
        await self.tree.sync()
bot = ProBot(command_prefix="!", intents=intents)

async def log(guild, msg):
    ch = guild.get_channel(config.get("log_channel_id", 0))
    if ch:
        try: await ch.send(msg)
        except discord.HTTPException: pass

@bot.event
async def on_ready():
    print(f"ProBot online: {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="/help"))

@bot.event
async def on_member_join(member):
    role = member.guild.get_role(config.get("autorole_id", 0))
    if role:
        try: await member.add_roles(role, reason="AutoRole")
        except discord.HTTPException: pass
    ch = member.guild.get_channel(config.get("welcome_channel_id", 0))
    if ch:
        e = discord.Embed(title="👋 مرحبا بيك!", description=f"مرحبا {member.mention} في **{member.guild.name}** 🎉", color=discord.Color.blurple())
        e.set_thumbnail(url=member.display_avatar.url)
        await ch.send(embed=e)
    await log(member.guild, f"📥 دخل: {member}")

@bot.event
async def on_member_remove(member):
    await log(member.guild, f"📤 خرج: {member}")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return
    k = f"{message.guild.id}:{message.author.id}"
    data["levels"][k] = data["levels"].get(k, 0) + 1
    if data["levels"][k] % 20 == 0:
        await message.channel.send(f"✨ {message.author.mention} عندك {data['levels'][k]} XP")
    save("data.json", data)
    await bot.process_commands(message)

@bot.tree.command(name="help", description="قائمة أوامر ProBot")
async def help_cmd(i):
    e=discord.Embed(title="🤖 ProBot — الأوامر", color=discord.Color.blurple())
    e.add_field(name="إدارة", value="/ban /kick /timeout /unban /clear /warn /warnings", inline=False)
    e.add_field(name="إعدادات", value="/setwelcome /setlogs /setautorole", inline=False)
    e.add_field(name="Tickets", value="/ticket /close_ticket", inline=False)
    e.add_field(name="معلومات", value="/ping /serverinfo /userinfo /rank", inline=False)
    await i.response.send_message(embed=e, ephemeral=True)

@bot.tree.command(name="ping", description="سرعة البوت")
async def ping(i): await i.response.send_message(f"Pong! {round(bot.latency*1000)}ms")

@bot.tree.command(name="serverinfo", description="معلومات السيرفر")
async def serverinfo(i):
    g=i.guild; e=discord.Embed(title=g.name, color=discord.Color.blurple())
    e.add_field(name="الأعضاء", value=str(g.member_count)); e.add_field(name="القنوات", value=str(len(g.channels)))
    if g.icon: e.set_thumbnail(url=g.icon.url)
    await i.response.send_message(embed=e)

@bot.tree.command(name="userinfo", description="معلومات عضو")
async def userinfo(i, member: discord.Member=None):
    m=member or i.user; e=discord.Embed(title=str(m), color=discord.Color.blurple())
    e.add_field(name="ID", value=str(m.id)); e.add_field(name="الحساب من", value=discord.utils.format_dt(m.created_at, style="D"))
    e.set_thumbnail(url=m.display_avatar.url); await i.response.send_message(embed=e)

@bot.tree.command(name="rank", description="XP متاع عضو")
async def rank(i, member: discord.Member=None):
    m=member or i.user; xp=data["levels"].get(f"{i.guild_id}:{m.id}",0)
    await i.response.send_message(f"🏆 {m.mention}: **{xp} XP**")

@bot.tree.command(name="clear", description="امسح رسائل")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(i, amount: app_commands.Range[int,1,100]):
    await i.response.defer(ephemeral=True); msgs=await i.channel.purge(limit=amount)
    await i.followup.send(f"🧹 تم مسح {len(msgs)} رسالة", ephemeral=True)

@bot.tree.command(name="kick", description="طرد عضو")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(i, member: discord.Member, reason: str="ما تحددش"):
    await member.kick(reason=reason); await i.response.send_message(f"👢 تم طرد {member.mention}: {reason}")
    await log(i.guild, f"Kick: {member} بواسطة {i.user} — {reason}")

@bot.tree.command(name="ban", description="حظر عضو")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(i, member: discord.Member, reason: str="ما تحددش"):
    await member.ban(reason=reason); await i.response.send_message(f"🔨 تم حظر {member.mention}: {reason}")
    await log(i.guild, f"Ban: {member} بواسطة {i.user} — {reason}")

@bot.tree.command(name="timeout", description="Timeout بالدقايق")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(i, member: discord.Member, minutes: app_commands.Range[int,1,10080], reason: str="ما تحددش"):
    await member.timeout(timedelta(minutes=minutes), reason=reason)
    await i.response.send_message(f"⏳ Timeout لـ {member.mention}: {minutes} دقيقة")

@bot.tree.command(name="unban", description="فك الحظر باستعمال ID")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(i, user_id: str):
    try:
        u=await bot.fetch_user(int(user_id)); await i.guild.unban(u)
        await i.response.send_message(f"✅ تفك الحظر على {u}")
    except (ValueError, discord.NotFound):
        await i.response.send_message("❌ ما لقيتش العضو في قائمة الحظر", ephemeral=True)

@bot.tree.command(name="warn", description="إنذار عضو")
@app_commands.checks.has_permissions(moderate_members=True)
async def warn(i, member: discord.Member, reason: str="ما تحددش"):
    k=f"{i.guild_id}:{member.id}"; data["warnings"].setdefault(k,[]).append({"by":i.user.id,"reason":reason}); save("data.json",data)
    await i.response.send_message(f"⚠️ تسجّل إنذار لـ {member.mention}: {reason}")

@bot.tree.command(name="warnings", description="عرض إنذارات عضو")
@app_commands.checks.has_permissions(moderate_members=True)
async def warnings(i, member: discord.Member):
    items=data["warnings"].get(f"{i.guild_id}:{member.id}",[])
    await i.response.send_message("\n".join(f"{n+1}. {x['reason']}" for n,x in enumerate(items[-10:])) or "ما عندوش إنذارات", ephemeral=True)

@bot.tree.command(name="setwelcome", description="قناة الترحيب")
@app_commands.checks.has_permissions(administrator=True)
async def setwelcome(i, channel: discord.TextChannel):
    config["welcome_channel_id"]=channel.id; save("config.json",config); await i.response.send_message(f"✅ {channel.mention}",ephemeral=True)

@bot.tree.command(name="setlogs", description="قناة Logs")
@app_commands.checks.has_permissions(administrator=True)
async def setlogs(i, channel: discord.TextChannel):
    config["log_channel_id"]=channel.id; save("config.json",config); await i.response.send_message(f"✅ {channel.mention}",ephemeral=True)

@bot.tree.command(name="setautorole", description="رتبة آلية")
@app_commands.checks.has_permissions(administrator=True)
async def setautorole(i, role: discord.Role):
    config["autorole_id"]=role.id; save("config.json",config); await i.response.send_message(f"✅ {role.mention}",ephemeral=True)

@bot.tree.command(name="ticket", description="افتح تذكرة خاصة")
async def ticket(i):
    name=f"ticket-{i.user.id}"
    if discord.utils.get(i.guild.text_channels,name=name):
        return await i.response.send_message("عندك تذكرة مفتوحة بالفعل",ephemeral=True)
    config["ticket_counter"]=config.get("ticket_counter",0)+1; save("config.json",config)
    overwrites={i.guild.default_role:discord.PermissionOverwrite(view_channel=False),i.user:discord.PermissionOverwrite(view_channel=True,send_messages=True),i.guild.me:discord.PermissionOverwrite(view_channel=True,send_messages=True,manage_channels=True)}
    ch=await i.guild.create_text_channel(f"ticket-{config['ticket_counter']:03d}",overwrites=overwrites)
    data["tickets"][str(ch.id)]={"owner":i.user.id}; save("data.json",data)
    await ch.send(f"🎫 مرحبا {i.user.mention}! اكتب مشكلتك. استعمل /close_ticket كي تكمل.")
    await i.response.send_message(f"تفتحت تذكرتك: {ch.mention}",ephemeral=True)

@bot.tree.command(name="close_ticket", description="سكر التذكرة")
async def close_ticket(i):
    info=data["tickets"].get(str(i.channel_id))
    if not info: return await i.response.send_message("الأمر هذا يتخدم داخل ticket",ephemeral=True)
    if info["owner"] != i.user.id and not i.user.guild_permissions.manage_channels:
        return await i.response.send_message("كان صاحب التذكرة أو الإدارة",ephemeral=True)
    await i.response.send_message("🔒 باش نسكر التذكرة...")
    import asyncio
    await asyncio.sleep(2); data["tickets"].pop(str(i.channel_id),None); save("data.json",data); await i.channel.delete()

@bot.tree.error
async def on_error(i, error):
    msg="❌ ما عندكش الصلاحيات اللازمة." if isinstance(error, app_commands.MissingPermissions) else "❌ صار خطأ؛ شوف Console."
    try:
        if i.response.is_done(): await i.followup.send(msg,ephemeral=True)
        else: await i.response.send_message(msg,ephemeral=True)
    except discord.HTTPException: pass

if not TOKEN:
    print("حط التوكن في DISCORD_TOKEN قبل التشغيل.")
else:
    bot.run(TOKEN)
