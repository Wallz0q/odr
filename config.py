import os
from dotenv import load_dotenv
load_dotenv()

# ============ CONFIG ============
BOT_TOKEN = os.getenv("BOT_TOKEN", "ISI_TOKEN_BOT_KAMU")
OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "usernamekamu")
TESTIMONI_GROUP = int(os.getenv("TESTIMONI_GROUP", "-1001234567890"))

MENU_PHOTO = None
QRIS_PHOTO = None
PAYMENT_INFO = """
*Informasi Pembayaran*

Silakan transfer sesuai nominal ke:
• Dana / OVO / GoPay : 08xxxxxxxxxx
• Bank BCA : 1234567890 a.n. Nama Kamu

Setelah transfer, kirim *foto bukti pembayaran*.
"""