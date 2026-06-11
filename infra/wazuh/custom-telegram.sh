#!/bin/bash
# ══════════════════════════════════════════════════════════════
# Medical CRM — Wazuh → Telegram Bot Alert Integration
# ══════════════════════════════════════════════════════════════
#
# APA INI?
# Script ini adalah "kurir" yang mengirim notifikasi ke Telegram
# setiap kali Wazuh mendeteksi serangan dengan severity tinggi.
#
# CARA KERJA:
# 1. Wazuh mendeteksi alert level >= 7
# 2. Wazuh menjalankan script ini dan memberikan file JSON berisi data alert
# 3. Script ini membaca data JSON tersebut (pakai jq)
# 4. Script memformat data jadi pesan yang mudah dibaca manusia
# 5. Script mengirim pesan ke Telegram API menggunakan curl
# 6. Tim kalian dapat notifikasi di HP: "TING! 🚨 Ada serangan!"
#
# CARA SETUP:
# 1. Ganti TELEGRAM_BOT_TOKEN dengan token dari @BotFather
# 2. Ganti TELEGRAM_CHAT_ID dengan chat ID grup Telegram kalian
# 3. Copy ke server:
#      sudo cp custom-telegram.sh /var/ossec/integrations/
#      sudo chmod 750 /var/ossec/integrations/custom-telegram.sh
#      sudo chown root:wazuh /var/ossec/integrations/custom-telegram.sh
# 4. Tambahkan konfigurasi di /var/ossec/etc/ossec.conf (lihat bagian bawah)
# 5. Restart Wazuh:
#      sudo systemctl restart wazuh-manager
#
# CARA DAPATKAN TOKEN & CHAT ID:
# - Token: Buka Telegram → cari @BotFather → /newbot → ikuti instruksi
# - Chat ID: Buat grup → invite bot → kirim pesan → buka browser:
#   https://api.telegram.org/bot<TOKEN>/getUpdates
#   Cari "chat":{"id": -xxxxxxx} (angka negatif = ID grup)
#
# DEPENDENSI:
# - jq (JSON processor): sudo apt install jq
# - curl: biasanya sudah ada di Ubuntu
# ══════════════════════════════════════════════════════════════

# ┌─────────────────────────────────────────────┐
# │  ⚠️  GANTI DUA VARIABEL DI BAWAH INI!  ⚠️  │
# └─────────────────────────────────────────────┘
TELEGRAM_BOT_TOKEN="GANTI_DENGAN_TOKEN_DARI_BOTFATHER"
TELEGRAM_CHAT_ID="GANTI_DENGAN_CHAT_ID_GRUP"

# ── Parameter dari Wazuh ──────────────────────
# Wazuh memanggil script ini dengan 3 argumen:
# $1 = Path ke file JSON berisi data alert
# $2 = API key (jika ada, dari konfigurasi ossec.conf)
# $3 = Hook URL (jika ada, dari konfigurasi ossec.conf)
ALERT_FILE="$1"

# ── Validasi: apakah file alert ada? ──────────
if [ ! -f "$ALERT_FILE" ]; then
    echo "ERROR: Alert file tidak ditemukan: $ALERT_FILE" >&2
    exit 1
fi

# ── Parse data dari JSON alert ────────────────
# jq = tool command line untuk membaca file JSON
# -r = output raw string (tanpa tanda kutip)
# // = fallback value jika field tidak ada
ALERT_LEVEL=$(jq -r '.rule.level // "?"' "$ALERT_FILE" 2>/dev/null)
ALERT_DESC=$(jq -r '.rule.description // "Tidak ada deskripsi"' "$ALERT_FILE" 2>/dev/null)
ALERT_SOURCE=$(jq -r '.data.source_ip // .agent.ip // "N/A"' "$ALERT_FILE" 2>/dev/null)
ALERT_TIME=$(jq -r '.timestamp // "?"' "$ALERT_FILE" 2>/dev/null)
RULE_ID=$(jq -r '.rule.id // "?"' "$ALERT_FILE" 2>/dev/null)
AGENT_NAME=$(jq -r '.agent.name // "medical-crm"' "$ALERT_FILE" 2>/dev/null)
FULL_LOG=$(jq -r '.full_log // "N/A"' "$ALERT_FILE" 2>/dev/null | head -c 200)

# ── Tentukan emoji dan label severity ─────────
# Level 10+ = CRITICAL (merah, paling mendesak)
# Level 7-9 = HIGH (oranye, perlu perhatian)
# Level < 7 = MEDIUM (kuning, informational)
if [ "$ALERT_LEVEL" -ge 10 ] 2>/dev/null; then
    EMOJI="🚨🔴"
    SEVERITY="CRITICAL"
elif [ "$ALERT_LEVEL" -ge 7 ] 2>/dev/null; then
    EMOJI="⚠️🟠"
    SEVERITY="HIGH"
else
    EMOJI="ℹ️🟡"
    SEVERITY="MEDIUM"
fi

# ── Format pesan Telegram ─────────────────────
# Menggunakan Markdown formatting agar pesan rapi dan mudah dibaca.
# *bold* = teks tebal
# `code` = teks monospace (untuk IP, ID, dll)
# _italic_ = teks miring
MESSAGE="${EMOJI} *MEDICAL CRM — SECURITY ALERT*

*Severity:* ${SEVERITY} (Level ${ALERT_LEVEL})
*Rule ID:* \`${RULE_ID}\`
*Deskripsi:* ${ALERT_DESC}

*Source IP:* \`${ALERT_SOURCE}\`
*Agent:* ${AGENT_NAME}
*Waktu:* ${ALERT_TIME}

*Log:* \`${FULL_LOG}\`

🛡️ _Blue Team Defense Active — Medical CRM EAS 2025_"

# ── Kirim ke Telegram ─────────────────────────
# curl = tool untuk mengirim HTTP request
# -s = silent mode (tidak tampilkan progress bar)
# -X POST = gunakan method POST
# sendMessage = API endpoint Telegram untuk kirim pesan
# parse_mode=Markdown = agar formatting *bold* _italic_ `code` bekerja
RESPONSE=$(curl -s -X POST \
    "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_CHAT_ID}" \
    -d "text=${MESSAGE}" \
    -d "parse_mode=Markdown" \
    -d "disable_web_page_preview=true" \
    2>&1)

# ── Cek apakah pengiriman berhasil ────────────
if echo "$RESPONSE" | jq -e '.ok == true' > /dev/null 2>&1; then
    echo "Telegram alert berhasil dikirim untuk Rule ID ${RULE_ID}"
else
    echo "ERROR: Gagal mengirim Telegram alert. Response: $RESPONSE" >&2
    exit 1
fi

exit 0
