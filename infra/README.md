# 🛡️ Infrastruktur Monitoring & Alerting — Medical CRM

## Apa Ini?

Folder ini berisi semua konfigurasi untuk sistem **monitoring real-time** yang mendeteksi serangan dan mengirim notifikasi ke **Telegram** secara instan.

## Alur Kerja

```
Lawan serang server → Suricata mendeteksi → Wazuh menganalisis → Telegram TING! 🚨
                       (traffic jaringan)    (korelasi & severity)  (notifikasi HP)

Aplikasi CRM log event → Wazuh membaca → Level ≥ 7 → Telegram TING! 🚨
(login gagal, WAF block)  (file JSON)     (berbahaya!)
```

## Struktur Folder

```
infra/
├── setup-monitoring.sh          ← 🚀 Script otomatis (jalankan ini!)
├── README.md                    ← 📖 Dokumen ini
├── suricata/
│   └── medical-crm.rules       ← 🔍 Rule deteksi serangan di jaringan
└── wazuh/
    ├── medical-crm_decoder.xml  ← 📝 Penerjemah format log kita
    ├── medical-crm_rules.xml    ← ⚖️ Penilaian severity setiap event
    ├── custom-telegram.sh       ← 📱 Pengirim notifikasi ke Telegram
    └── ossec-snippet.conf       ← ⚙️ Konfigurasi untuk ossec.conf
```

## Cara Pasang (Quick Start)

### Prasyarat di Ubuntu Server
```bash
# Install Suricata (IDS)
sudo apt update
sudo apt install suricata jq -y

# Install Wazuh (ikuti panduan resmi)
# https://documentation.wazuh.com/current/installation-guide/
```

### Langkah 1: Edit Token Telegram
```bash
nano infra/wazuh/custom-telegram.sh
# Ganti baris:
#   TELEGRAM_BOT_TOKEN="GANTI_DENGAN_TOKEN_DARI_BOTFATHER"
#   TELEGRAM_CHAT_ID="GANTI_DENGAN_CHAT_ID_GRUP"
```

### Langkah 2: Jalankan Setup Otomatis
```bash
cd infra/
chmod +x setup-monitoring.sh
sudo ./setup-monitoring.sh
```

### Langkah 3: Test
```bash
# Cek Suricata berjalan
sudo systemctl status suricata

# Cek Wazuh berjalan
sudo systemctl status wazuh-manager

# Test notifikasi Telegram
curl -s -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  -d "chat_id=<CHAT_ID>" \
  -d "text=🚨 TEST: Medical CRM monitoring aktif!"
```

## Cara Dapatkan Token Telegram

1. Buka Telegram, cari **@BotFather**
2. Ketik `/newbot`
3. Beri nama: `MediCRM Alert Bot`
4. Beri username: `medicrm_eas_bot`
5. **Simpan token** yang diberikan (contoh: `7123456789:AAH1234...`)
6. Buat **grup Telegram** untuk tim
7. **Invite bot** ke grup
8. Kirim pesan apapun di grup
9. Buka: `https://api.telegram.org/bot<TOKEN>/getUpdates`
10. Cari `"chat":{"id":-123456789}` — itu **Chat ID** grup kalian
