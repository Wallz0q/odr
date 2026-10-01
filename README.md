# NAT VPS Telegram Store Bot

Bot Telegram untuk jualan NAT VPS dengan sistem pembayaran manual (kirim foto bukti transfer).

## Fitur

### User
- `/start` → Menu utama + foto (opsional)
- Lihat daftar paket + stok real-time
- Order → dapat Order ID
- Kirim foto bukti transfer dengan caption `bayar ORDERID`
- Terima detail VPS otomatis setelah admin konfirmasi

### Admin
- Menu admin lengkap (inline keyboard)
- Ubah harga paket
- Tambah stok VPS dengan format mudah
- Lihat & konfirmasi/tolak order
- `/setmenu` → set foto menu
- `/setqris` → set foto QRIS

## Instalasi

1. Install dependency:
```bash
pip install -r requirements.txt
```

2. Edit `config.py`:
- Isi `BOT_TOKEN`
- Isi `OWNER_ID` (angka ID Telegram kamu)
- Isi `OWNER_USERNAME`
- Isi info pembayaran

3. Jalankan:
```bash
python bot.py
```

## Cara Set Foto Menu & QRIS

1. Kirim foto ke bot
2. Reply foto tersebut dengan perintah:
   - `/setmenu` → untuk foto menu
   - `/setqris` → untuk foto QRIS
3. Bot akan kasih File ID → copy ke `config.py`

## Format Tambah Stok

Di admin menu → Kelola Stok → pilih paket, lalu kirim:

```
IP|PortRange|Username|Password|Keterangan
```

Contoh:
```
103.xx.xx.xx|20000-20100|root|rahasia123|NAT Singapore
```

## License

MIT
