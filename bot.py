import telebot
from telebot import types
import json
import os
from datetime import datetime
from config import *

bot = telebot.TeleBot(BOT_TOKEN)

# ================== DATABASE ==================
DB_FILE = "database.json"

def load_db():
    if not os.path.exists(DB_FILE):
        data = {
            "packages": [
                {
                    "id": 1,
                    "name": "NAT VPS 1GB",
                    "ram": "1GB",
                    "cpu": "1 Core",
                    "price": 15000,
                    "description": "Cocok untuk bot & website ringan"
                },
                {
                    "id": 2,
                    "name": "NAT VPS 2GB",
                    "ram": "2GB",
                    "cpu": "1 Core",
                    "price": 25000,
                    "description": "Cocok untuk multiple bot"
                },
                {
                    "id": 3,
                    "name": "NAT VPS 4GB",
                    "ram": "4GB",
                    "cpu": "2 Core",
                    "price": 40000,
                    "description": "Performa lebih stabil"
                }
            ],
            "stock": {},      # package_id -> list of vps detail
            "orders": {},     # order_id -> order data
            "users": {}
        }
        save_db(data)
        return data
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

db = load_db()

def is_owner(user_id):
    return user_id == OWNER_ID

def format_rupiah(amount):
    return f"Rp{amount:,.0f}".replace(",", ".")

# ================== USER COMMANDS ==================
@bot.message_handler(commands=['start', 'menu'])
def start(message):
    user = message.from_user
    db["users"][str(user.id)] = {
        "id": user.id,
        "username": user.username or "",
        "name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
        "join": datetime.now().isoformat()
    }
    save_db(db)

    text = f"""
Halo *{user.first_name}* 👋

Selamat datang di *NAT VPS Store*

Kami menyediakan VPS NAT murah & stabil.

Ketik /belivps untuk melihat paket yang tersedia.
Ketik /cekorder untuk cek status order kamu.
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🛒 Beli VPS", callback_data="beli_vps"))
    markup.add(types.InlineKeyboardButton("📦 Cek Order", callback_data="cek_order"))
    if is_owner(user.id):
        markup.add(types.InlineKeyboardButton("⚙️ Admin Menu", callback_data="admin_menu"))

    if MENU_PHOTO:
        try:
            bot.send_photo(message.chat.id, MENU_PHOTO, caption=text, parse_mode="Markdown", reply_markup=markup)
            return
        except:
            pass
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['belivps'])
def beli_vps_cmd(message):
    show_packages(message.chat.id)

def show_packages(chat_id):
    text = "*📦 Daftar Paket NAT VPS*\n\nPilih paket yang ingin dibeli:\n"
    markup = types.InlineKeyboardMarkup()
    for pkg in db["packages"]:
        stock_count = len(db["stock"].get(str(pkg["id"]), []))
        btn_text = f"{pkg['name']} - {format_rupiah(pkg['price'])} (Stok: {stock_count})"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"pkg_{pkg['id']}"))
    markup.add(types.InlineKeyboardButton("🔙 Kembali", callback_data="back_start"))
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    data = call.data

    if data == "beli_vps":
        bot.answer_callback_query(call.id)
        show_packages(chat_id)

    elif data == "back_start":
        bot.answer_callback_query(call.id)
        start(call.message)

    elif data == "cek_order":
        bot.answer_callback_query(call.id)
        cek_order_user(chat_id, user_id)

    elif data.startswith("pkg_"):
        bot.answer_callback_query(call.id)
        pkg_id = data.split("_")[1]
        pkg = next((p for p in db["packages"] if str(p["id"]) == pkg_id), None)
        if not pkg:
            bot.send_message(chat_id, "Paket tidak ditemukan.")
            return

        stock = db["stock"].get(pkg_id, [])
        if not stock:
            bot.send_message(chat_id, f"❌ Maaf, stok *{pkg['name']}* sedang habis.", parse_mode="Markdown")
            return

        text = f"""
*Konfirmasi Pesanan*

📦 Paket: *{pkg['name']}*
💾 RAM: {pkg['ram']}
🖥️ CPU: {pkg['cpu']}
💰 Harga: *{format_rupiah(pkg['price'])}*
📝 {pkg.get('description', '-')}

Apakah kamu yakin ingin membeli paket ini?
"""
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("✅ Ya, Beli", callback_data=f"confirm_{pkg_id}"),
            types.InlineKeyboardButton("❌ Batal", callback_data="beli_vps")
        )
        bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)

    elif data.startswith("confirm_"):
        bot.answer_callback_query(call.id)
        pkg_id = data.split("_")[1]
        pkg = next((p for p in db["packages"] if str(p["id"]) == pkg_id), None)
        if not pkg:
            return

        order_id = f"ORD{int(datetime.now().timestamp())}"
        db["orders"][order_id] = {
            "order_id": order_id,
            "user_id": user_id,
            "username": call.from_user.username or "",
            "name": call.from_user.first_name or "",
            "package_id": pkg_id,
            "package_name": pkg["name"],
            "price": pkg["price"],
            "status": "menunggu_pembayaran",
            "created_at": datetime.now().isoformat(),
            "proof": None
        }
        save_db(db)

        text = f"""
*Order Berhasil Dibuat!*

🆔 Order ID: `{order_id}`
📦 Paket: {pkg['name']}
💰 Total: *{format_rupiah(pkg['price'])}*

{PAYMENT_INFO}

Setelah transfer, *kirim foto bukti pembayaran* dengan caption:
`bayar {order_id}`
"""
        bot.send_message(chat_id, text, parse_mode="Markdown")

        # Kirim QRIS jika ada
        if QRIS_PHOTO:
            try:
                bot.send_photo(chat_id, QRIS_PHOTO, caption="Scan QRIS di atas")
            except:
                pass

        # Notifikasi ke owner
        try:
            bot.send_message(OWNER_ID,
                f"🛒 *Order Baru!*\n\n"
                f"Order ID: `{order_id}`\n"
                f"User: {call.from_user.first_name} (@{call.from_user.username or '-'})\n"
                f"Paket: {pkg['name']}\n"
                f"Harga: {format_rupiah(pkg['price'])}",
                parse_mode="Markdown"
            )
        except:
            pass

    elif data == "admin_menu":
        if not is_owner(user_id):
            bot.answer_callback_query(call.id, "Owner only!", show_alert=True)
            return
        bot.answer_callback_query(call.id)
        admin_menu(chat_id)

    elif data == "admin_packages":
        if not is_owner(user_id): return
        bot.answer_callback_query(call.id)
        admin_packages(chat_id)

    elif data == "admin_stock":
        if not is_owner(user_id): return
        bot.answer_callback_query(call.id)
        admin_stock_menu(chat_id)

    elif data == "admin_orders":
        if not is_owner(user_id): return
        bot.answer_callback_query(call.id)
        admin_orders(chat_id)

    elif data.startswith("addstock_"):
        if not is_owner(user_id): return
        bot.answer_callback_query(call.id)
        pkg_id = data.split("_")[1]
        msg = bot.send_message(chat_id,
            f"Kirim detail VPS untuk paket ID `{pkg_id}` dengan format:\n\n"
            f"`IP|PortRange|Username|Password|Keterangan`\n\n"
            f"Contoh:\n`192.168.1.1|10000-10100|root|pass123|NAT SG`",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(msg, lambda m: process_add_stock(m, pkg_id))

    elif data.startswith("setprice_"):
        if not is_owner(user_id): return
        bot.answer_callback_query(call.id)
        pkg_id = data.split("_")[1]
        msg = bot.send_message(chat_id, f"Masukkan harga baru untuk paket ID `{pkg_id}` (angka saja):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, lambda m: process_set_price(m, pkg_id))

    elif data.startswith("confirmorder_"):
        if not is_owner(user_id): return
        bot.answer_callback_query(call.id)
        order_id = data.split("_")[1]
        confirm_order(chat_id, order_id)

    elif data.startswith("rejectorder_"):
        if not is_owner(user_id): return
        bot.answer_callback_query(call.id)
        order_id = data.split("_")[1]
        if order_id in db["orders"]:
            db["orders"][order_id]["status"] = "ditolak"
            save_db(db)
            bot.send_message(chat_id, f"Order `{order_id}` ditolak.", parse_mode="Markdown")
            try:
                bot.send_message(db["orders"][order_id]["user_id"],
                    f"❌ Order `{order_id}` ditolak.\nSilakan hubungi admin @{OWNER_USERNAME}",
                    parse_mode="Markdown")
            except:
                pass

def cek_order_user(chat_id, user_id):
    user_orders = [o for o in db["orders"].values() if o["user_id"] == user_id]
    if not user_orders:
        bot.send_message(chat_id, "Kamu belum memiliki order.")
        return
    text = "*Riwayat Order Kamu:*\n\n"
    for o in sorted(user_orders, key=lambda x: x["created_at"], reverse=True)[:10]:
        text += f"🆔 `{o['order_id']}`\n📦 {o['package_name']}\n💰 {format_rupiah(o['price'])}\n📊 Status: *{o['status']}*\n\n"
    bot.send_message(chat_id, text, parse_mode="Markdown")

# ================== ADMIN ==================
def admin_menu(chat_id):
    text = "*⚙️ Admin Menu*\n\nPilih menu:"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📦 Kelola Paket", callback_data="admin_packages"))
    markup.add(types.InlineKeyboardButton("📥 Kelola Stok", callback_data="admin_stock"))
    markup.add(types.InlineKeyboardButton("📋 Order Masuk", callback_data="admin_orders"))
    markup.add(types.InlineKeyboardButton("🔙 Kembali", callback_data="back_start"))
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)

def admin_packages(chat_id):
    text = "*📦 Daftar Paket*\n\n"
    markup = types.InlineKeyboardMarkup()
    for pkg in db["packages"]:
        text += f"ID: `{pkg['id']}` | {pkg['name']} | {format_rupiah(pkg['price'])}\n"
        markup.add(types.InlineKeyboardButton(
            f"Ubah Harga: {pkg['name']}", callback_data=f"setprice_{pkg['id']}"
        ))
    markup.add(types.InlineKeyboardButton("🔙 Kembali", callback_data="admin_menu"))
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)

def admin_stock_menu(chat_id):
    text = "*📥 Kelola Stok VPS*\n\nPilih paket untuk menambah stok:"
    markup = types.InlineKeyboardMarkup()
    for pkg in db["packages"]:
        count = len(db["stock"].get(str(pkg["id"]), []))
        markup.add(types.InlineKeyboardButton(
            f"{pkg['name']} (Stok: {count})", callback_data=f"addstock_{pkg['id']}"
        ))
    markup.add(types.InlineKeyboardButton("🔙 Kembali", callback_data="admin_menu"))
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)

def process_add_stock(message, pkg_id):
    if not is_owner(message.from_user.id):
        return
    try:
        parts = message.text.strip().split("|")
        if len(parts) < 4:
            bot.reply_to(message, "Format salah! Minimal: IP|PortRange|Username|Password")
            return
        vps = {
            "ip": parts[0].strip(),
            "port_range": parts[1].strip(),
            "username": parts[2].strip(),
            "password": parts[3].strip(),
            "note": parts[4].strip() if len(parts) > 4 else "",
            "added_at": datetime.now().isoformat()
        }
        if str(pkg_id) not in db["stock"]:
            db["stock"][str(pkg_id)] = []
        db["stock"][str(pkg_id)].append(vps)
        save_db(db)
        bot.reply_to(message, f"✅ Stok berhasil ditambahkan untuk paket ID {pkg_id}\nTotal stok sekarang: {len(db['stock'][str(pkg_id)])}")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

def process_set_price(message, pkg_id):
    if not is_owner(message.from_user.id):
        return
    try:
        price = int(message.text.strip())
        for pkg in db["packages"]:
            if str(pkg["id"]) == str(pkg_id):
                pkg["price"] = price
                save_db(db)
                bot.reply_to(message, f"✅ Harga paket ID {pkg_id} diubah menjadi {format_rupiah(price)}")
                return
        bot.reply_to(message, "Paket tidak ditemukan.")
    except:
        bot.reply_to(message, "Harga harus berupa angka!")

def admin_orders(chat_id):
    pending = [o for o in db["orders"].values() if o["status"] == "menunggu_konfirmasi"]
    if not pending:
        bot.send_message(chat_id, "Tidak ada order yang menunggu konfirmasi.")
        return
    for o in pending:
        text = f"""
*Order Menunggu Konfirmasi*

🆔 `{o['order_id']}`
👤 {o['name']} (@{o['username'] or '-'})
📦 {o['package_name']}
💰 {format_rupiah(o['price'])}
📅 {o['created_at'][:16]}
"""
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("✅ Konfirmasi", callback_data=f"confirmorder_{o['order_id']}"),
            types.InlineKeyboardButton("❌ Tolak", callback_data=f"rejectorder_{o['order_id']}")
        )
        bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)

def confirm_order(chat_id, order_id):
    order = db["orders"].get(order_id)
    if not order:
        bot.send_message(chat_id, "Order tidak ditemukan.")
        return
    if order["status"] not in ["menunggu_pembayaran", "menunggu_konfirmasi"]:
        bot.send_message(chat_id, "Order sudah diproses.")
        return

    pkg_id = str(order["package_id"])
    stock = db["stock"].get(pkg_id, [])
    if not stock:
        bot.send_message(chat_id, "❌ Stok habis! Tidak bisa konfirmasi.")
        return

    vps = stock.pop(0)
    db["stock"][pkg_id] = stock
    order["status"] = "selesai"
    order["vps"] = vps
    order["completed_at"] = datetime.now().isoformat()
    save_db(db)

    # Kirim ke pembeli
    detail = f"""
✅ *Pembayaran Dikonfirmasi!*

Order ID: `{order_id}`
Paket: {order['package_name']}

*Detail VPS:*
🌐 IP: `{vps['ip']}`
🔌 Port Range: `{vps['port_range']}`
👤 Username: `{vps['username']}`
🔑 Password: `{vps['password']}`
📝 Note: {vps.get('note', '-')}

Simpan data ini baik-baik.
Terima kasih sudah order!
"""
    try:
        bot.send_message(order["user_id"], detail, parse_mode="Markdown")
    except:
        pass

    bot.send_message(chat_id, f"✅ Order `{order_id}` berhasil dikonfirmasi & VPS dikirim ke pembeli.", parse_mode="Markdown")

    # ===== AUTO KIRIM TESTIMONI KE GRUP =====
    if TESTIMONI_GROUP:
        try:
            buyer_name = order.get("name") or "Pembeli"
            buyer_username = f"@{order['username']}" if order.get("username") else "Private"
            waktu = datetime.now().strftime("%d/%m/%Y %H:%M")

            testi_text = f"""
✅ *TESTIMONI ORDER BERHASIL*

👤 Pembeli : {buyer_name} ({buyer_username})
📦 Paket   : {order['package_name']}
💰 Nominal : {format_rupiah(order['price'])}
🆔 Order   : `{order_id}`
📅 Waktu   : {waktu}

Terima kasih sudah mempercayai kami!
"""
            bot.send_message(TESTIMONI_GROUP, testi_text, parse_mode="Markdown")
        except Exception as e:
            print(f"Gagal kirim testimoni ke grup: {e}")

# ================== TERIMA BUKTI PEMBAYARAN ==================
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    caption = (message.caption or "").strip().lower()
    if not caption.startswith("bayar "):
        return

    order_id = caption.replace("bayar ", "").strip().upper()
    if order_id not in db["orders"]:
        bot.reply_to(message, "Order ID tidak ditemukan. Pastikan format: `bayar ORDxxxxxxxxxx`", parse_mode="Markdown")
        return

    order = db["orders"][order_id]
    if order["user_id"] != message.from_user.id:
        bot.reply_to(message, "Ini bukan order kamu.")
        return

    if order["status"] != "menunggu_pembayaran":
        bot.reply_to(message, f"Status order saat ini: {order['status']}")
        return

    # Simpan file_id bukti
    file_id = message.photo[-1].file_id
    order["proof"] = file_id
    order["status"] = "menunggu_konfirmasi"
    save_db(db)

    bot.reply_to(message, f"✅ Bukti pembayaran untuk `{order_id}` diterima.\nMohon tunggu konfirmasi admin.", parse_mode="Markdown")

    # Forward ke owner
    try:
        bot.send_photo(OWNER_ID, file_id,
            caption=f"🧾 *Bukti Pembayaran*\n\nOrder ID: `{order_id}`\nUser: {message.from_user.first_name}\nPaket: {order['package_name']}\nHarga: {format_rupiah(order['price'])}",
            parse_mode="Markdown")
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("✅ Konfirmasi", callback_data=f"confirmorder_{order_id}"),
            types.InlineKeyboardButton("❌ Tolak", callback_data=f"rejectorder_{order_id}")
        )
        bot.send_message(OWNER_ID, "Pilih aksi:", reply_markup=markup)
    except Exception as e:
        print("Gagal kirim ke owner:", e)

# ================== OWNER COMMANDS ==================
@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if not is_owner(message.from_user.id):
        return
    admin_menu(message.chat.id)

@bot.message_handler(commands=['setmenu'])
def set_menu_photo(message):
    if not is_owner(message.from_user.id):
        return
    if not message.reply_to_message or not message.reply_to_message.photo:
        bot.reply_to(message, "Reply foto yang ingin dijadikan foto menu, lalu ketik /setmenu")
        return
    file_id = message.reply_to_message.photo[-1].file_id
    # Simpan ke config (sementara print saja, user bisa copy)
    bot.reply_to(message, f"✅ File ID foto menu:\n`{file_id}`\n\nCopy lalu tempel ke `MENU_PHOTO` di config.py", parse_mode="Markdown")

@bot.message_handler(commands=['setqris'])
def set_qris_photo(message):
    if not is_owner(message.from_user.id):
        return
    if not message.reply_to_message or not message.reply_to_message.photo:
        bot.reply_to(message, "Reply foto QRIS, lalu ketik /setqris")
        return
    file_id = message.reply_to_message.photo[-1].file_id
    bot.reply_to(message, f"✅ File ID QRIS:\n`{file_id}`\n\nCopy lalu tempel ke `QRIS_PHOTO` di config.py", parse_mode="Markdown")

print("NAT VPS Bot sedang berjalan...")
bot.infinity_polling()
