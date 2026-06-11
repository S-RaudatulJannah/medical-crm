#!/bin/bash
# ══════════════════════════════════════════════════════════════
# Medical CRM — Setup Monitoring & Alerting (Ubuntu Server)
# ══════════════════════════════════════════════════════════════
#
# Script ini mengotomasi pemasangan SELURUH komponen monitoring:
# 1. Suricata IDS custom rules
# 2. Wazuh SIEM decoder + rules
# 3. Telegram Bot notification script
# 4. Wazuh log monitoring configuration
#
# CARA PAKAI:
#   1. Copy folder infra/ ke Ubuntu Server kalian
#   2. cd infra/
#   3. chmod +x setup-monitoring.sh
#   4. sudo ./setup-monitoring.sh
#
# PRASYARAT (harus sudah terinstall di Ubuntu Server):
#   - Suricata  : sudo apt install suricata
#   - Wazuh     : ikuti panduan https://documentation.wazuh.com
#   - jq        : sudo apt install jq (untuk parsing JSON di script Telegram)
#   - curl      : biasanya sudah ada
#
# ⚠️  PENTING: Edit custom-telegram.sh terlebih dahulu!
#     Ganti TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID dengan nilai asli.
# ══════════════════════════════════════════════════════════════

set -e  # Hentikan script jika ada error

# Warna untuk output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Medical CRM — Monitoring & Alerting Setup${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo ""

# ── Cek apakah dijalankan sebagai root ────────
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERROR] Script ini harus dijalankan sebagai root (sudo).${NC}"
    echo "Gunakan: sudo ./setup-monitoring.sh"
    exit 1
fi

# ── Cek prasyarat ─────────────────────────────
echo -e "${YELLOW}[1/6] Mengecek prasyarat...${NC}"

check_installed() {
    if command -v "$1" &> /dev/null; then
        echo -e "  ✅ $1 terinstall"
        return 0
    else
        echo -e "  ${RED}❌ $1 TIDAK ditemukan. Install: sudo apt install $1${NC}"
        return 1
    fi
}

MISSING=0
check_installed "suricata" || MISSING=1
check_installed "jq" || MISSING=1
check_installed "curl" || MISSING=1

# Cek Wazuh
if [ -d "/var/ossec" ]; then
    echo -e "  ✅ Wazuh terinstall (/var/ossec)"
else
    echo -e "  ${RED}❌ Wazuh TIDAK ditemukan (/var/ossec tidak ada)${NC}"
    MISSING=1
fi

if [ $MISSING -eq 1 ]; then
    echo ""
    echo -e "${RED}[ERROR] Ada prasyarat yang belum terpenuhi. Install dulu lalu jalankan ulang.${NC}"
    exit 1
fi

echo ""

# ── Langkah 1: Pasang Suricata rules ─────────
echo -e "${YELLOW}[2/6] Memasang Suricata custom rules...${NC}"

SURICATA_RULES_DIR="/etc/suricata/rules"
if [ -d "$SURICATA_RULES_DIR" ]; then
    cp suricata/medical-crm.rules "$SURICATA_RULES_DIR/"
    echo -e "  ✅ Rules di-copy ke $SURICATA_RULES_DIR/medical-crm.rules"

    # Tambahkan ke suricata.yaml jika belum ada
    SURICATA_YAML="/etc/suricata/suricata.yaml"
    if grep -q "medical-crm.rules" "$SURICATA_YAML" 2>/dev/null; then
        echo -e "  ℹ️  medical-crm.rules sudah terdaftar di suricata.yaml"
    else
        # Tambahkan setelah baris "rule-files:" yang pertama ditemukan
        sed -i '/rule-files:/a\  - medical-crm.rules' "$SURICATA_YAML"
        echo -e "  ✅ medical-crm.rules ditambahkan ke suricata.yaml"
    fi
else
    echo -e "  ${RED}⚠️  Direktori $SURICATA_RULES_DIR tidak ditemukan, skip.${NC}"
fi

echo ""

# ── Langkah 2: Pasang Wazuh decoder ──────────
echo -e "${YELLOW}[3/6] Memasang Wazuh custom decoder...${NC}"

WAZUH_DECODERS_DIR="/var/ossec/etc/decoders"
if [ -d "$WAZUH_DECODERS_DIR" ]; then
    cp wazuh/medical-crm_decoder.xml "$WAZUH_DECODERS_DIR/"
    chown root:wazuh "$WAZUH_DECODERS_DIR/medical-crm_decoder.xml"
    chmod 640 "$WAZUH_DECODERS_DIR/medical-crm_decoder.xml"
    echo -e "  ✅ Decoder di-copy ke $WAZUH_DECODERS_DIR/"
else
    echo -e "  ${RED}⚠️  Direktori $WAZUH_DECODERS_DIR tidak ditemukan, skip.${NC}"
fi

echo ""

# ── Langkah 3: Pasang Wazuh rules ────────────
echo -e "${YELLOW}[4/6] Memasang Wazuh custom rules...${NC}"

WAZUH_RULES_DIR="/var/ossec/etc/rules"
if [ -d "$WAZUH_RULES_DIR" ]; then
    cp wazuh/medical-crm_rules.xml "$WAZUH_RULES_DIR/"
    chown root:wazuh "$WAZUH_RULES_DIR/medical-crm_rules.xml"
    chmod 640 "$WAZUH_RULES_DIR/medical-crm_rules.xml"
    echo -e "  ✅ Rules di-copy ke $WAZUH_RULES_DIR/"
else
    echo -e "  ${RED}⚠️  Direktori $WAZUH_RULES_DIR tidak ditemukan, skip.${NC}"
fi

echo ""

# ── Langkah 4: Pasang Telegram script ────────
echo -e "${YELLOW}[5/6] Memasang Telegram notification script...${NC}"

WAZUH_INTEGRATIONS_DIR="/var/ossec/integrations"
if [ -d "$WAZUH_INTEGRATIONS_DIR" ]; then
    cp wazuh/custom-telegram.sh "$WAZUH_INTEGRATIONS_DIR/"
    chmod 750 "$WAZUH_INTEGRATIONS_DIR/custom-telegram.sh"
    chown root:wazuh "$WAZUH_INTEGRATIONS_DIR/custom-telegram.sh"
    echo -e "  ✅ Script di-copy ke $WAZUH_INTEGRATIONS_DIR/"

    # Cek apakah token sudah diganti
    if grep -q "GANTI_DENGAN_TOKEN" "$WAZUH_INTEGRATIONS_DIR/custom-telegram.sh"; then
        echo -e "  ${RED}⚠️  PENTING: Edit file dan ganti TELEGRAM_BOT_TOKEN serta TELEGRAM_CHAT_ID!${NC}"
        echo -e "  ${RED}     sudo nano $WAZUH_INTEGRATIONS_DIR/custom-telegram.sh${NC}"
    fi
else
    echo -e "  ${RED}⚠️  Direktori $WAZUH_INTEGRATIONS_DIR tidak ditemukan, skip.${NC}"
fi

echo ""

# ── Langkah 5: Update ossec.conf ─────────────
echo -e "${YELLOW}[6/6] Mengupdate Wazuh ossec.conf...${NC}"

OSSEC_CONF="/var/ossec/etc/ossec.conf"
if [ -f "$OSSEC_CONF" ]; then
    # Cek apakah konfigurasi Medical CRM sudah ada
    if grep -q "medical-crm" "$OSSEC_CONF"; then
        echo -e "  ℹ️  Konfigurasi Medical CRM sudah ada di ossec.conf"
    else
        # Tambahkan sebelum tag </ossec_config> penutup
        # Baca snippet dan masukkan
        SNIPPET=$(cat wazuh/ossec-snippet.conf | grep -v '^<!--' | grep -v '^-->' | grep -v '^$' | head -20)

        # Tambahkan blok localfile dan integration
        sed -i '/<\/ossec_config>/i \
\n  <!-- Medical CRM Monitoring -->\
  <localfile>\
    <log_format>json<\/log_format>\
    <location>\/var\/log\/medical-crm\/security_events.json<\/location>\
  <\/localfile>\
\n  <!-- Medical CRM Telegram Alert -->\
  <integration>\
    <name>custom-telegram.sh<\/name>\
    <level>7<\/level>\
    <group>medical-crm<\/group>\
    <alert_format>json<\/alert_format>\
  <\/integration>' "$OSSEC_CONF"

        echo -e "  ✅ Konfigurasi Medical CRM ditambahkan ke ossec.conf"
    fi
else
    echo -e "  ${RED}⚠️  File $OSSEC_CONF tidak ditemukan, skip.${NC}"
fi

echo ""

# ── Buat direktori log ────────────────────────
echo -e "${YELLOW}Membuat direktori log...${NC}"
mkdir -p /var/log/medical-crm
chown -R root:root /var/log/medical-crm
chmod 755 /var/log/medical-crm
echo -e "  ✅ /var/log/medical-crm/ siap"

echo ""

# ── Restart services ─────────────────────────
echo -e "${YELLOW}Merestart services...${NC}"

if systemctl is-active --quiet suricata; then
    systemctl restart suricata
    echo -e "  ✅ Suricata di-restart"
else
    echo -e "  ${YELLOW}ℹ️  Suricata tidak berjalan, jalankan manual: sudo systemctl start suricata${NC}"
fi

if systemctl is-active --quiet wazuh-manager; then
    systemctl restart wazuh-manager
    echo -e "  ✅ Wazuh Manager di-restart"
elif systemctl is-active --quiet wazuh-agent; then
    systemctl restart wazuh-agent
    echo -e "  ✅ Wazuh Agent di-restart"
else
    echo -e "  ${YELLOW}ℹ️  Wazuh tidak berjalan, jalankan manual: sudo systemctl start wazuh-manager${NC}"
fi

echo ""
echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ SETUP SELESAI!${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Langkah selanjutnya:"
echo "  1. Edit token Telegram di /var/ossec/integrations/custom-telegram.sh"
echo "  2. Test Suricata: sudo tail -f /var/log/suricata/fast.log"
echo "  3. Test Wazuh: sudo tail -f /var/ossec/logs/alerts/alerts.json"
echo "  4. Test Telegram manual:"
echo "     curl -s -X POST 'https://api.telegram.org/bot<TOKEN>/sendMessage' \\"
echo "       -d 'chat_id=<CHAT_ID>' -d 'text=🚨 TEST: Medical CRM alert aktif!'"
echo ""
