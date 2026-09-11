import asyncio
import os
import logging
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import ChatPermissions, ChatMemberUpdated
from aiogram.enums import ChatMemberStatus, ChatType
import yt_dlp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

ADMINS = [6939399272]

# قواعد البيانات
welcome_messages = {}
locked_chats = {}
warnings = {}
investments = {}

# ============================================
# دوال مساعدة
# ============================================
async def is_admin(message: types.Message) -> bool:
    if message.from_user.id in ADMINS:
        return True
    try:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return False

async def check_bot_admin(message: types.Message) -> bool:
    try:
        bot_member = await bot.get_chat_member(message.chat.id, (await bot.get_me()).id)
        if bot_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await message.answer("⚠️ يجب أن أكون **مشرفاً** لأعمل بشكل صحيح!", parse_mode="Markdown")
            return False
        return True
    except:
        return False

async def get_target_user_id(message: types.Message):
    if message.reply_to_message:
        return message.reply_to_message.from_user.id
    args = message.text.split()
    if len(args) >= 2:
        username = args[1].replace('@', '')
        try:
            member = await bot.get_chat_member(message.chat.id, f"@{username}")
            return member.user.id
        except:
            pass
    return None

# ============================================
# مراقبة انضمام البوت
# ============================================
@dp.my_chat_member()
async def on_bot_chat_member_update(my_chat_member: ChatMemberUpdated):
    chat = my_chat_member.chat
    
    if my_chat_member.new_chat_member.status == ChatMemberStatus.MEMBER:
        try:
            await bot.send_message(
                chat.id,
                "️ يجب أن أكون **مشرفاً** لأعمل بشكل صحيح!\n"
                "أعطني صلاحيات المشرف ثم أعد إضافتي.",
                parse_mode="Markdown"
            )
            await asyncio.sleep(5)
            await bot.leave_chat(chat.id)
        except Exception as e:
            logger.error(f"Error leaving chat: {e}")
    
    elif my_chat_member.new_chat_member.status == ChatMemberStatus.ADMINISTRATOR:
        try:
            await bot.send_message(
                chat.id,
                "✅ **تمت إضافتي كمشرف بنجاح!**\n\n"
                "🤖 أنا جاهز للعمل!\n\n"
                " **الأوامر:**\n"
                "/start - قائمة الأوامر\n"
                "/help - المساعدة\n"
                "/mute - كتم\n"
                "/kick - طرد\n"
                "/ban - حظر\n"
                "/warn - تحذير\n"
                "#all - منشن الجميع\n"
                "يوت <أغنية> - تحميل من يوتيوب",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error: {e}")

# ============================================
# 1. أمر /start
# ============================================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        text = (
            "🤖 *مرحباً بك في بوت الإدارة!*\n\n"
            " *الأوامر:*\n\n"
            "🔰 *إدارة الأعضاء:*\n"
            "`/mute` - كتم\n"
            "`/unmute` - إلغاء الكتم\n"
            "`/kick` - طرد\n"
            "`/ban` - حظر\n"
            "`/warn` - تحذير (3 = طرد)\n"
            "`/muted` - المكتومين\n"
            "`/clearmuted` - مسح المكتومين\n\n"
            
            "🔒 *المجموعة:*\n"
            "`/lock <نوع>` - قفل\n"
            "`/unlock <نوع>` - فتح\n"
            "`/pin` - تثبيت\n"
            "`/unpin` - إلغاء التثبيت\n"
            "`#all` - منشن الجميع\n\n"
            
            "🎵 *يوتيوب:*\n"
            "`يوت <اسم الأغنية>`\n"
            "`yt <اسم الأغنية>`\n\n"
            
            "💰 *الاستثمار:*\n"
            "`استثمار فلوسي`\n"
            "`/invest <مبلغ>`\n"
            "`/daily` - مكافأة يومية\n"
            "`/balance` - الرصيد\n\n"
            
            "📊 *أخرى:*\n"
            "`/stats` - إحصائيات\n"
            "`/id` - عرض ID"
        )
        await message.answer(text, parse_mode="Markdown")
    else:
        if not await check_bot_admin(message):
            await asyncio.sleep(3)
            await bot.leave_chat(message.chat.id)
            return
        await message.answer(" بوت الإدارة جاهز! /help")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await cmd_start(message)

# ============================================
# 2. نظام التحذيرات
# ============================================
@dp.message(Command("warn"))
async def warn_user(message: types.Message):
    if not await is_admin(message):
        await message.answer("⛔ للأدمن فقط!")
        return
    if not await check_bot_admin(message):
        return
    
    user_id = await get_target_user_id(message)
    if not user_id:
        await message.answer("🚫 رد على المستخدم")
        return
    
    chat_id = message.chat.id
    if chat_id not in warnings:
        warnings[chat_id] = {}
    if user_id not in warnings[chat_id]:
        warnings[chat_id][user_id] = 0
    
    warnings[chat_id][user_id] += 1
    count = warnings[chat_id][user_id]
    user = await bot.get_chat_member(chat_id, user_id)
    
    if count >= 3:
        await message.chat.ban(user_id=user_id)
        await message.chat.unban(user_id=user_id)
        await message.answer(f"⚠️ **{user.user.first_name}** طُرد بعد 3 تحذيرات!", parse_mode="Markdown")
        warnings[chat_id][user_id] = 0
    else:
        await message.answer(f"⚠️ **{user.user.first_name}** تحذير {count}/3", parse_mode="Markdown")

@dp.message(Command("warnings"))
async def get_warnings(message: types.Message):
    user_id = await get_target_user_id(message)
    if not user_id:
        user_id = message.from_user.id
    
    chat_id = message.chat.id
    count = warnings.get(chat_id, {}).get(user_id, 0)
    user = await bot.get_chat_member(chat_id, user_id)
    await message.answer(f"️ **{user.user.first_name}** لديه {count}/3 تحذيرات", parse_mode="Markdown")

@dp.message(Command("resetwarn"))
async def reset_warnings(message: types.Message):
    if not await is_admin(message):
        await message.answer("⛔ للأدمن فقط!")
        return
    
    user_id = await get_target_user_id(message)
    if not user_id:
        await message.answer("🚫 حدد المستخدم")
        return
    
    chat_id = message.chat.id
    if chat_id in warnings and user_id in warnings[chat_id]:
        warnings[chat_id][user_id] = 0
        user = await bot.get_chat_member(chat_id, user_id)
        await message.answer(f"✅ تم تصفير تحذيرات **{user.user.first_name}**", parse_mode="Markdown")

# ============================================
# 3. الكتم
# ============================================
@dp.message(Command("mute"))
async def mute_user(message: types.Message):
    if not await is_admin(message):
        await message.answer(" للأدمن فقط!")
        return
    if not await check_bot_admin(message):
        return
    
    user_id = await get_target_user_id(message)
    if not user_id:
        await message.answer("🔇 رد على المستخدم")
        return
    
    try:
        user = await bot.get_chat_member(message.chat.id, user_id)
        await message.chat.restrict(user_id=user_id, permissions=ChatPermissions(can_send_messages=False))
        await message.answer(f"🔇 تم كتم **{user.user.first_name}**", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f" فشل: {str(e)[:100]}")

@dp.message(Command("unmute"))
async def unmute_user(message: types.Message):
    if not await is_admin(message):
        await message.answer("⛔ للأدمن فقط!")
        return
    if not await check_bot_admin(message):
        return
    
    user_id = await get_target_user_id(message)
    if not user_id:
        await message.answer("🔊 رد على المستخدم")
        return
    
    try:
        user = await bot.get_chat_member(message.chat.id, user_id)
        await message.chat.restrict(
            user_id=user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            )
        )
        await message.answer(f"🔊 تم إلغاء كتم **{user.user.first_name}**", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ فشل: {str(e)[:100]}")

@dp.message(Command("muted"))
async def list_muted_users(message: types.Message):
    if not await is_admin(message):
        await message.answer("⛔ للأدمن فقط!")
        return
    
    try:
        chat_id = message.chat.id
        members = await bot.get_chat_members(chat_id)
        muted_list = []
        
        for member in members:
            if member.status == ChatMemberStatus.RESTRICTED:
                if not member.permissions.can_send_messages:
                    username = f"@{member.user.username}" if member.user.username else "بدون يوزر"
                    muted_list.append(f"🔇 {member.user.first_name} ({username})")
        
        if muted_list:
            text = " **المكتومين:**\n\n" + "\n".join(muted_list)
            await message.answer(text, parse_mode="Markdown")
        else:
            await message.answer("✅ لا يوجد مكتومين!")
    except Exception as e:
        await message.answer(f"❌ خطأ: {str(e)[:100]}")

@dp.message(Command("clearmuted"))
async def clear_muted_users(message: types.Message):
    if not await is_admin(message):
        await message.answer("⛔ للأدمن فقط!")
        return
    if not await check_bot_admin(message):
        return
    
    try:
        chat_id = message.chat.id
        members = await bot.get_chat_members(chat_id)
        unmuted_count = 0
        
        for member in members:
            if member.status == ChatMemberStatus.RESTRICTED:
                if not member.permissions.can_send_messages:
                    await bot.restrict_chat_member(
                        chat_id, member.user.id,
                        ChatPermissions(
                            can_send_messages=True,
                            can_send_media_messages=True,
                            can_send_polls=True,
                            can_send_other_messages=True,
                            can_add_web_page_previews=True,
                        )
                    )
                    unmuted_count += 1
        
        await message.answer(f"✅ تم إلغاء كتم **{unmuted_count}** مستخدم!", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ خطأ: {str(e)[:100]}")

# ============================================
# 4. الطرد والحظر
# ============================================
@dp.message(Command("kick"))
async def kick_user(message: types.Message):
    if not await is_admin(message):
        await message.answer("⛔ للأدمن فقط!")
        return
    if not await check_bot_admin(message):
        return
    
    user_id = await get_target_user_id(message)
    if not user_id:
        await message.answer("🚫 رد على المستخدم")
        return
    
    try:
        user = await bot.get_chat_member(message.chat.id, user_id)
        await message.chat.ban(user_id=user_id)
        await message.chat.unban(user_id=user_id)
        await message.answer(f"🚫 تم طرد **{user.user.first_name}**", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ فشل: {str(e)[:100]}")

@dp.message(Command("ban"))
async def ban_user(message: types.Message):
    if not await is_admin(message):
        await message.answer("⛔ للأدمن فقط!")
        return
    if not await check_bot_admin(message):
        return
    
    user_id = await get_target_user_id(message)
    if not user_id:
        await message.answer("🔨 رد على المستخدم")
        return
    
    try:
        user = await bot.get_chat_member(message.chat.id, user_id)
        await message.chat.ban(user_id=user_id)
        await message.answer(f"🔨 تم حظر **{user.user.first_name}**", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ فشل: {str(e)[:100]}")

@dp.message(Command("unban"))
async def unban_user(message: types.Message):
    if not await is_admin(message):
        await message.answer("⛔ للأدمن فقط!")
        return
    if not await check_bot_admin(message):
        return
    
    if not message.reply_to_message and len(message.text.split()) < 2:
        await message.answer("✅ استخدم: /unban @username")
        return
    
    try:
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
        else:
            username = message.text.split()[1].replace('@', '')
            user = await bot.get_chat_member(message.chat.id, f"@{username}")
            user_id = user.user.id
        
        user = await bot.get_chat_member(message.chat.id, user_id)
        await message.chat.unban(user_id=user_id)
        await message.answer(f"✅ تم إلغاء حظر **{user.user.first_name}**", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ فشل: {str(e)[:100]}")

# ============================================
# 5. قفل/فتح
# ============================================
@dp.message(Command("lock"))
async def lock_content(message: types.Message):
    if not await is_admin(message):
        await message.answer(" للأدمن فقط!")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("🔒 استخدم: /lock <links|media|stickers|photos|all>")
        return
    
    lock_type = args[1].lower()
    chat_id = message.chat.id
    
    if chat_id not in locked_chats:
        locked_chats[chat_id] = []
    
    if lock_type == "all":
        locked_chats[chat_id] = ["links", "media", "stickers", "photos"]
        await message.answer("🔒 تم قفل الكل!")
    elif lock_type not in locked_chats[chat_id]:
        locked_chats[chat_id].append(lock_type)
        await message.answer(f"🔒 تم قفل: {lock_type}")
    else:
        await message.answer(f"️ {lock_type} مقفل!")

@dp.message(Command("unlock"))
async def unlock_content(message: types.Message):
    if not await is_admin(message):
        await message.answer("⛔ للأدمن فقط!")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("🔓 استخدم: /unlock <links|media|stickers|photos|all>")
        return
    
    lock_type = args[1].lower()
    chat_id = message.chat.id
    
    if lock_type == "all":
        locked_chats[chat_id] = []
        await message.answer("🔓 تم فتح الكل!")
    elif chat_id in locked_chats and lock_type in locked_chats[chat_id]:
        locked_chats[chat_id].remove(lock_type)
        await message.answer(f"🔓 تم فتح: {lock_type}")
    else:
        await message.answer(f"⚠️ {lock_type} مفتوح!")

# ============================================
# 6. التثبيت
# ============================================
@dp.message(Command("pin"))
async def pin_message(message: types.Message):
    if not await is_admin(message):
        await message.answer("⛔ للأدمن فقط!")
        return
    
    if not message.reply_to_message:
        await message.answer("📌 رد على الرسالة")
        return
    
    try:
        await message.reply_to_message.pin(disable_notification=True)
        await message.answer("✅ تم التثبيت")
    except Exception as e:
        await message.answer(f"❌ فشل: {str(e)[:100]}")

@dp.message(Command("unpin"))
async def unpin_message(message: types.Message):
    if not await is_admin(message):
        await message.answer(" للأدمن فقط!")
        return
    
    try:
        await bot.unpin_chat_message(message.chat.id)
        await message.answer("✅ تم إلغاء التثبيت")
    except Exception as e:
        await message.answer(f"❌ فشل: {str(e)[:100]}")

# ============================================
# 7. منشن الجميع (#all / @all)
# ============================================
@dp.message(F.text & (F.text.startswith("#all") | F.text.startswith("@all")))
async def tag_all_members(message: types.Message):
    if not await is_admin(message):
        await message.answer("⛔ للأدمن فقط!")
        return
    
    if not await check_bot_admin(message):
        return
    
    try:
        chat_id = message.chat.id
        members = await bot.get_chat_members(chat_id)
        
        members_per_message = 5
        total_members = len([m for m in members if not m.user.is_bot])
        
        await message.answer(f"📢 **#all**\nجاري منشن {total_members} عضو...")
        
        non_bot_members = [m for m in members if not m.user.is_bot]
        
        for i in range(0, len(non_bot_members), members_per_message):
            batch = non_bot_members[i:i + members_per_message]
            mentions = ", ".join([f"**{m.user.first_name}**" for m in batch])
            
            if mentions:
                await message.answer(f"#all\n{mentions}", parse_mode="Markdown")
                await asyncio.sleep(1)
        
        await message.answer(f"✅ تم منشن {total_members} عضو!")
        
    except Exception as e:
        await message.answer(f"❌ خطأ: {str(e)[:100]}")

# ============================================
# 8. لعبة الاستثمار 💰
# ============================================
@dp.message(Command("investment") | Command("invest"))
async def investment_game(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in investments:
        investments[user_id] = {"balance": 10000, "invested": 0, "total_profit": 0}
    
    user_data = investments[user_id]
    
    stats_text = (
        f"💰 **لوحة الاستثمار**\n\n"
        f"💵 رصيدك: `{user_data['balance']}` ريال 💸\n"
        f"📊 مستثمر: `{user_data['invested']}` ريال\n"
        f"📈 إجمالي الربح: `{user_data['total_profit']}` ريال\n\n"
        f"💡 **الأوامر:**\n"
        f"`/invest <المبلغ>` - استثمار\n"
        f"`/withdraw <المبلغ>` - سحب\n"
        f"`/daily` - مكافأة يومية\n"
        f"`/balance` - الرصيد"
    )
    
    await message.answer(stats_text, parse_mode="Markdown")

@dp.message(Command("invest"))
async def invest_money(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in investments:
        investments[user_id] = {"balance": 10000, "invested": 0, "total_profit": 0}
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("💰 استخدم: /invest <المبلغ>\nمثال: /invest 1000")
        return
    
    try:
        amount = int(args[1])
        user_data = investments[user_id]
        
        if amount <= 0:
            await message.answer(" المبلغ يجب أن يكون > 0!")
            return
        
        if amount > user_data["balance"]:
            await message.answer("❌ رصيدك غير كافي!")
            return
        
        user_data["balance"] -= amount
        user_data["invested"] += amount
        
        profit_percentage = random.randint(5, 15)
        profit = int(amount * profit_percentage / 100)
        
        user_data["balance"] += amount + profit
        user_data["total_profit"] += profit
        user_data["invested"] -= amount
        
        result_text = (
            f"🎉 **مبرووووك نجح الإستثمار!** 🎊\n\n"
            f"📊 نسبة الربح: `{profit_percentage}%`\n"
            f" مبلغ الربح: `{profit}` ريال 💸\n"
            f"💵 فلوسك صارت: `{user_data['balance']}` ريال 🤑"
        )
        
        await message.answer(result_text, parse_mode="Markdown")
        
    except ValueError:
        await message.answer(" استخدم رقماً صحيحاً!")
    except Exception as e:
        await message.answer(f"❌ خطأ: {str(e)[:100]}")

@dp.message(Command("withdraw"))
async def withdraw_money(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in investments:
        await message.answer("❌ ليس لديك رصيد!")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("💸 استخدم: /withdraw <المبلغ>")
        return
    
    try:
        amount = int(args[1])
        user_data = investments[user_id]
        
        if amount <= 0:
            await message.answer("❌ المبلغ يجب أن يكون > 0!")
            return
        
        if amount > user_data["balance"]:
            await message.answer("❌ رصيدك غير كافي!")
            return
        
        user_data["balance"] -= amount
        await message.answer(f"✅ تم سحب `{amount}` ريال!\n💵 رصيدك: `{user_data['balance']}` ريال")
        
    except ValueError:
        await message.answer("❌ استخدم رقماً صحيحاً!")

@dp.message(Command("balance"))
async def check_balance(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in investments:
        investments[user_id] = {"balance": 10000, "invested": 0, "total_profit": 0}
    
    user_data = investments[user_id]
    await message.answer(f"💵 **رصيدك:** `{user_data['balance']}` ريال", parse_mode="Markdown")

@dp.message(Command("daily"))
async def daily_bonus(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in investments:
        investments[user_id] = {"balance": 10000, "invested": 0, "total_profit": 0}
    
    bonus = random.randint(500, 2000)
    investments[user_id]["balance"] += bonus
    
    await message.answer(
        f"🎁 **مكافأتك اليومية!**\n\n"
        f"💰 حصلت على `{bonus}` ريال!\n"
        f" رصيدك: `{investments[user_id]['balance']}` ريال 🤑",
        parse_mode="Markdown"
    )

# ============================================
# 9. تحميل يوتيوب التلقائي
# ============================================
@dp.message(F.text & ~F.command)
async def auto_youtube_download(message: types.Message):
    text = message.text.strip()
    
    if not (text.lower().startswith('يوت ') or text.lower().startswith('yt ')):
        return
    
    if text.lower().startswith('يوت '):
        query = text[4:].strip()
    elif text.lower().startswith('yt '):
        query = text[3:].strip()
    else:
        return
    
    if not query:
        return
    
    status_msg = await message.reply(f"⏳ جاري البحث عن: {query}...")
    
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(f"ytsearch1:{query}", download=False)
            
            if not search_results or 'entries' not in search_results or not search_results['entries']:
                await status_msg.edit_text("❌ لم يتم العثور على نتائج!")
                return
            
            video_info = search_results['entries'][0]
            video_url = video_info['url'] if 'url' in video_info else f"https://www.youtube.com/watch?v={video_info['id']}"
            title = video_info.get('title', query)
            duration = video_info.get('duration', 0)
            
            await status_msg.edit_text(f"⬇️ جاري التحميل: {title}")
            
            audio_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'song.%(ext)s',
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            
            with yt_dlp.YoutubeDL(audio_opts) as ydl2:
                ydl2.download([video_url])
            
            audio_file = 'song.mp3'
            if os.path.exists(audio_file):
                with open(audio_file, 'rb') as audio:
                    await message.reply_audio(
                        audio=audio,
                        title=title,
                        performer="ROZ-Bot 🎵",
                        caption=f" {title}\n⏱️ المدة: {duration} ثانية",
                    )
                os.remove(audio_file)
                await status_msg.delete()
            else:
                await status_msg.edit_text("❌ فشل التحميل!")
                
    except Exception as e:
        logger.error(f"Error: {e}")
        await status_msg.edit_text(f"❌ خطأ: {str(e)[:100]}")

# ============================================
# 10. إحصائيات و ID
# ============================================
@dp.message(Command("stats"))
async def group_stats(message: types.Message):
    chat = message.chat
    member_count = await bot.get_chat_member_count(chat.id)
    
    stats_text = (
        f"📊 *إحصائيات المجموعة*\n\n"
        f"📛 الاسم: {chat.title}\n"
        f"👥 الأعضاء: {member_count}\n"
        f"🆔 ID: `{chat.id}`\n"
        f"📝 النوع: {chat.type}"
    )
    
    await message.answer(stats_text, parse_mode="Markdown")

@dp.message(Command("id"))
async def get_id(message: types.Message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        user = await bot.get_chat_member(message.chat.id, user_id)
        await message.answer(f"🆔 ID: `{user_id}`\n👤 الاسم: {user.user.first_name}", parse_mode="Markdown")
    else:
        await message.answer(f"🆔 ID المجموعة: `{message.chat.id}`", parse_mode="Markdown")

# ============================================
# تشغيل البوت
# ============================================
async def main():
    print(" بوت الإدارة المتطور يعمل الآن...")
    print("✅ الميزات:")
    print("  - يوت/yt <اسم الأغنية>")
    print("  - الخروج إذا لم يكن مشرفاً")
    print("  - كتم/طرد/حظر/تحذير")
    print("  - #all - منشن الجميع")
    print("  - استثمار فلوسي - لعبة الاستثمار")
    print("  - /clearmuted - مسح المكتومين")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
