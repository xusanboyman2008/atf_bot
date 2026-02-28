import asyncio
import json
import os
import shlex

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)

TOKEN = "8677623205:AAGkNG11FLzQe6CV0_DiK_cLly6LCyEyox8"
OWNER_ID = 6588631008

DATA_FILE = "files.json"

bot = Bot(TOKEN)
dp = Dispatcher()


# ---------- LOAD JSON ----------
if os.path.exists(DATA_FILE):
    USER_FILES = json.load(open(DATA_FILE))
else:
    USER_FILES = {}

RUNNING = {}
USER_STATE = {}  # create/edit/terminal/runfixed


def save():
    json.dump(USER_FILES, open(DATA_FILE, "w"), indent=2)


def allowed(user_id):
    return user_id == OWNER_ID


# ---------- UI ----------
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📂 My Files", callback_data="files")],
        [InlineKeyboardButton(text="➕ Create File", callback_data="create")],
        [InlineKeyboardButton(text="💻 Terminal", callback_data="terminal")]
    ])


def file_buttons(name):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="▶️ Run", callback_data=f"run:{name}"),
            InlineKeyboardButton(text="🛑 Stop", callback_data=f"stop:{name}")
        ],
        [
            InlineKeyboardButton(text="✏️ Edit", callback_data=f"edit:{name}"),
            InlineKeyboardButton(text="📄 Show", callback_data=f"show:{name}")
        ],
        [
            InlineKeyboardButton(text="🗑️ Delete", callback_data=f"delete:{name}")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back", callback_data="files")
        ]
    ])


# ---------- START ----------
@dp.message(Command("start"))
async def start(message: Message):
    if not allowed(message.from_user.id):
        return
    await message.answer("⚙️ Control Panel", reply_markup=main_menu())


# ---------- FILE LIST ----------
# ---------- UTILITY ----------
def clean_user_files(uid: str):
    """Remove non-existing files from USER_FILES and save JSON"""
    files = USER_FILES.get(uid, [])
    valid_files = []
    for name in files:
        path = f"{name}"
        if os.path.exists(path):
            valid_files.append(name)
        else:
            # also remove running process if any dangling
            proc = RUNNING.get(uid, {}).get(name)
            if proc:
                proc.kill()
                RUNNING[uid].pop(name, None)
    USER_FILES[uid] = valid_files
    save()
    return valid_files


@dp.callback_query(F.data == "files")
async def files_panel(call: CallbackQuery):
    uid = str(call.from_user.id)
    files = clean_user_files(uid)  # <--- clean non-existing files first

    buttons = [
        [InlineKeyboardButton(text=f"📄 {f}", callback_data=f"file:{f}")]
        for f in files
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ Menu", callback_data="menu")])
    await call.message.edit_text(
        "📂 Your files:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


@dp.callback_query(F.data == "menu")
async def back_menu(call: CallbackQuery):
    await call.message.edit_text("⚙️ Control Panel", reply_markup=main_menu())


# ---------- CREATE ----------
@dp.callback_query(F.data == "create")
async def create(call: CallbackQuery):
    USER_STATE[call.from_user.id] = ("create", None)
    await call.message.answer("Send filename and code:\nExample:\nmyfile.py\nprint('hello')")


# ---------- FILE MENU ----------
@dp.callback_query(F.data.startswith("file:"))
async def file_open(call: CallbackQuery):
    name = call.data.split(":")[1]
    await call.message.edit_text(f"📄 {name}", reply_markup=file_buttons(name))


# ---------- SHOW ----------
@dp.callback_query(F.data.startswith("show:"))
async def show(call: CallbackQuery):
    uid = str(call.from_user.id)
    name = call.data.split(":")[1]
    path = f"{name}"
    if not os.path.exists(path):
        return await call.answer("File not found", show_alert=True)

    text = open(path, encoding="utf-8").read()[:3500]
    await call.message.answer(f"```\n{text}\n```", parse_mode="Markdown")


# ---------- DELETE ----------
@dp.callback_query(F.data.startswith("delete:"))
async def delete_file(call: CallbackQuery):
    uid = str(call.from_user.id)
    name = call.data.split(":")[1]

    # Stop running process if any
    proc = RUNNING.get(uid, {}).get(name)
    if proc:
        if proc.returncode is None:  # process is still running
            proc.kill()
            await proc.wait()
        # Remove from RUNNING anyway
        del RUNNING[uid][name]

    # Remove file from disk
    path = f"{name}"
    if os.path.exists(path):
        os.remove(path)

    # Remove from JSON
    if uid in USER_FILES and name in USER_FILES[uid]:
        USER_FILES[uid].remove(name)
        save()

    await call.message.answer(f"🗑️ File `{name}` deleted", parse_mode="Markdown")


# ---------- EDIT ----------
@dp.callback_query(F.data.startswith("edit:"))
async def edit(call: CallbackQuery):
    name = call.data.split(":")[1]
    USER_STATE[call.from_user.id] = ("edit", name)
    await call.message.answer("Send new code:")


# ---------- RUN FILE ----------
async def run_file(uid, name, timeout=None):
    path = f"{name}"
    if not os.path.exists(path):
        return "File not found"

    proc = await asyncio.create_subprocess_exec(
        "python", "-u", path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    RUNNING.setdefault(uid, {})[name] = proc

    try:
        if timeout:
            out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        else:
            out, err = await proc.communicate()
        result = (out + err).decode().strip() or "No output"
    except asyncio.TimeoutError:
        result = f"⏳ Running {timeout or '24/7'}..."
    return result[:3000]


@dp.callback_query(F.data.startswith("run:"))
async def run(call: CallbackQuery):
    uid = str(call.from_user.id)
    clean_user_files(uid)  # remove deleted/missing files
    name = call.data.split(":")[1]
    result = await run_file(uid, name, timeout=20)
    await call.message.answer(f"```\n{result}\n```", parse_mode="Markdown")


@dp.callback_query(F.data.startswith("stop:"))
async def stop(call: CallbackQuery):
    uid = str(call.from_user.id)
    name = call.data.split(":")[1]
    path = f"{name}"

    # kill nohup process
    os.system(f"pkill -f {shlex.quote(path)}")

    # remove from RUNNING dict if exists
    if RUNNING.get(uid, {}).get(name):
        del RUNNING[uid][name]

    await call.message.answer(f"🛑 File `{name}` stopped")


# ---------- POST-CREATION OPTIONS ----------
@dp.callback_query(F.data.startswith("runonce:"))
async def run_once(call: CallbackQuery):
    uid = str(call.from_user.id)
    name = call.data.split(":")[1]
    result = await run_file(uid, name, timeout=20)
    await call.message.answer(f"```\n{result}\n```", parse_mode="Markdown")


@dp.callback_query(F.data.startswith("run24:"))
async def run_24(call: CallbackQuery):
    uid = str(call.from_user.id)
    name = call.data.split(":")[1]
    path = f"{name}"

    if not os.path.exists(path):
        return await call.answer("File not found", show_alert=True)

    # Stop existing process if running
    proc = RUNNING.get(uid, {}).get(name)
    if proc:
        proc.kill()
        await proc.wait()
        del RUNNING[uid][name]

    # Run with nohup in background
    cmd = f"nohup python3 {path} > {path + '.log'} 2>&1 &"
    os.system(cmd)

    await call.message.answer(
        f"⏳ File `{name}` is now running 24/7 with nohup. "
        f"Output is logged to `{name}.log`. Use Stop to terminate."
    )
    return None


@dp.callback_query(F.data.startswith("runfixed:"))
async def run_fixed_prompt(call: CallbackQuery):
    name = call.data.split(":")[1]
    USER_STATE[call.from_user.id] = ("runfixed", name)
    await call.message.answer("Send duration in seconds:")


# ---------- TERMINAL ----------
@dp.callback_query(F.data == "terminal")
async def terminal(call: CallbackQuery):
    USER_STATE[call.from_user.id] = ("terminal", None)
    await call.message.answer("💻 Send terminal command")


# ---------- TEXT HANDLER ----------
# ---------- CREATE ----------
@dp.message()
async def text_handler(message: Message):
    state = USER_STATE.get(message.from_user.id)
    if not state:
        return

    mode, filename = state
    uid = str(message.from_user.id)

    if mode == "create":
        try:
            # Split safely
            lines = message.text.strip().split("\n")
            if len(lines) < 2:
                return await message.answer(
                    "❌ Invalid format! Send:\nfilename.py\nCODE"
                )

            name = lines[0].strip()
            code = "\n".join(lines[1:])

            # Save to JSON
            USER_FILES.setdefault(uid, []).append(name)
            save()

            # Write file
            path = f"{name}"
            with open(path, "w", encoding="utf-8") as f:
                f.write(code)

            # Ask next action
            buttons = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="▶️ Run Once (20s)", callback_data=f"runonce:{name}")],
                [InlineKeyboardButton(text="⏳ Run 24/7", callback_data=f"run24:{name}")],
                [InlineKeyboardButton(text="🗑️ Delete", callback_data=f"delete:{name}")],
                [InlineKeyboardButton(text="⬅️ Back", callback_data="files")]
            ])
            await message.answer(
                f"✅ File `{name}` created! What do you want to do now?",
                reply_markup=buttons
            )
        except Exception as e:
            await message.answer(f"❌ Error creating file: {e}")
        finally:
            USER_STATE.pop(message.from_user.id)
    elif mode == "edit":
        path = f"{filename}"
        with open(path, "w", encoding="utf-8") as f:
            f.write(message.text)
        await message.answer("✏️ Edited")
        USER_STATE.pop(message.from_user.id)

    # TERMINAL
    elif mode == "terminal":
        proc = await asyncio.create_subprocess_shell(
            message.text,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        out, err = await proc.communicate()
        result = (out + err).decode()[:3000]
        await message.answer(f"```\n{result}\n```", parse_mode="Markdown")

    # RUN FIXED
    elif mode == "runfixed":
        try:
            seconds = int(message.text.strip())
            result = await run_file(uid, filename, timeout=seconds)
            await message.answer(f"```\n{result}\n```", parse_mode="Markdown")
        except ValueError:
            await message.answer("❌ Invalid number")
        finally:
            USER_STATE.pop(message.from_user.id)


@dp.message(CommandStart)
async def clear_all(message: Message):
    if message.text == 'clear':
        for i in range(message.message_id, message.message_id - 30, -1):
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=i)
            except:
                pass
        return
    await message.delete()


# ---------- MAIN ----------
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
