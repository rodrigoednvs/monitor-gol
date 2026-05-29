# ============================================================
# MONITOR DE PASSAGEM AÉREA - GOL
# ALERTAS VIA TELEGRAM
#
# Rota:
# NAT -> GRU
#
# Data:
# 27/11/2026
#
# Horário:
# 18h15 -> 21h50
#
# Envia alerta SOMENTE quando o preço cair.
#
# ============================================================
#
# INSTALAÇÃO:
#
# pip3 install playwright requests
#
# depois execute:
#
# playwright install
#
# ============================================================

import json
import os
import re
import time
import requests

from datetime import datetime
from playwright.sync_api import sync_playwright

# ============================================================
# CONFIGURAÇÕES
# ============================================================

ORIGIN = "Natal"
DESTINATION = "São Paulo"

DATE = "2026-11-27"

DEPARTURE_TIME = "18:15"
ARRIVAL_TIME = "21:50"

# Verificação a cada 2 horas
CHECK_INTERVAL = 7200

PRICE_FILE = "last_price.json"

# ============================================================
# TELEGRAM
# ============================================================

TELEGRAM_BOT_TOKEN = "8813866033:AAE8XrTihw9kmwTW2n7NUbeYMxqTmmz50r4"

TELEGRAM_CHAT_ID = "8990010103"

# ============================================================
# FUNÇÕES
# ============================================================

def load_last_price():

    if os.path.exists(PRICE_FILE):

        with open(PRICE_FILE, "r", encoding="utf-8") as f:

            data = json.load(f)

            return data.get("price")

    return None


def save_last_price(price):

    with open(PRICE_FILE, "w", encoding="utf-8") as f:

        json.dump({
            "price": price,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, f, ensure_ascii=False, indent=4)


def send_telegram_message(old_price, new_price):

    economy = old_price - new_price

    message = f"""
✈️ GOL — NAT → GRU

📅 27/11/2026
🕕 18h15 → 21h50

💸 O preço caiu!

De: R$ {old_price:.2f}
Para: R$ {new_price:.2f}

🔥 Economia: R$ {economy:.2f}
"""

    url = f"https://api.telegram.org/bot8813866033:AAE8XrTihw9kmwTW2n7NUbeYMxqTmmz50r4/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    response = requests.post(url, data=payload)

    if response.status_code == 200:
        print("Mensagem Telegram enviada.")
    else:
        print("Erro ao enviar mensagem Telegram.")
        print(response.text)


def extract_price(text):

    match = re.search(r"R\$\s?([\d\.]+,\d{2})", text)

    if not match:
        return None

    value = match.group(1)

    value = value.replace(".", "").replace(",", ".")

    return float(value)


def check_flight_price():

    print(f"\n[{datetime.now()}] Verificando preços...")

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page()

        # ====================================================
        # SITE GOL
        # ====================================================

        page.goto(
            "https://www.voegol.com.br/",
            timeout=120000
        )

        page.wait_for_timeout(5000)

        try:

            # ====================================================
            # ORIGEM
            # ====================================================

            page.fill(
                'input[placeholder*="Origem"]',
                ORIGIN
            )

            page.wait_for_timeout(1000)

            page.keyboard.press("ArrowDown")
            page.keyboard.press("Enter")

            # ====================================================
            # DESTINO
            # ====================================================

            page.fill(
                'input[placeholder*="Destino"]',
                DESTINATION
            )

            page.wait_for_timeout(1000)

            page.keyboard.press("ArrowDown")
            page.keyboard.press("Enter")

            # ====================================================
            # DATA
            # ====================================================

            page.fill(
                'input[type="date"]',
                DATE
            )

            page.wait_for_timeout(1000)

            # ====================================================
            # BUSCAR
            # ====================================================

            page.click('button:has-text("Buscar")')

            print("Pesquisando voo...")

            page.wait_for_timeout(15000)

            # ====================================================
            # CAPTURA TEXTO DA PÁGINA
            # ====================================================

            content = page.locator("body").inner_text()

            # ====================================================
            # PROCURA VOO ESPECÍFICO
            # ====================================================

            if (
                DEPARTURE_TIME in content and
                ARRIVAL_TIME in content
            ):

                price = extract_price(content)

                if price is None:

                    print("Preço não encontrado.")

                    browser.close()

                    return

                print(f"Preço encontrado: R$ {price:.2f}")

                last_price = load_last_price()

                # ====================================================
                # PRIMEIRA EXECUÇÃO
                # ====================================================

                if last_price is None:

                    print("Primeiro preço salvo.")

                    save_last_price(price)

                # ====================================================
                # PREÇO CAIU
                # ====================================================

                elif price < last_price:

                    print("Preço caiu!")

                    send_telegram_message(
                        last_price,
                        price
                    )

                    save_last_price(price)

                else:

                    print("Nenhuma queda de preço.")

            else:

                print("Voo específico não encontrado.")

        except Exception as e:

            print(f"Erro: {e}")

        browser.close()


# ============================================================
# LOOP PRINCIPAL
# ============================================================

if __name__ == "__main__":

    print("====================================")
    print(" MONITOR GOL + TELEGRAM INICIADO ")
    print("====================================")

    while True:

        try:

            check_flight_price()

        except Exception as e:

            print(f"Erro geral: {e}")

        print(
            f"Aguardando {CHECK_INTERVAL / 60:.0f} minutos..."
        )

        time.sleep(CHECK_INTERVAL)
