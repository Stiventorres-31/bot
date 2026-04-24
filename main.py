import os
import time
import requests
import telebot

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = telebot.TeleBot(TOKEN)

API_URL = "https://aviator-api.example.com/signal"  # Replace with actual Aviator API endpoint

# Martingale / gale configuration
BASE_BET = 1.0
MAX_GALES = 2
MULTIPLIER = 2.0


def get_signal():
    """Fetch the latest trading signal from the Aviator API."""
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"[ERROR] Failed to fetch signal: {e}")
        return None


def format_signal_message(signal: dict, bet: float, gale: int) -> str:
    """Format the signal data into a Telegram message."""
    entry = signal.get("entry", "N/A")
    multiplier_target = signal.get("multiplier", "N/A")
    confidence = signal.get("confidence", "N/A")

    gale_info = f"🔁 Gale {gale}/{MAX_GALES}" if gale > 0 else "🟢 Entrada inicial"

    message = (
        f"✈️ *AviatorProBot — Sinal Detectado*\n\n"
        f"📌 Entrada: `{entry}`\n"
        f"🎯 Alvo: `{multiplier_target}x`\n"
        f"📊 Confiança: `{confidence}%`\n"
        f"💰 Aposta sugerida: `R$ {bet:.2f}`\n"
        f"{gale_info}\n\n"
        f"⚠️ _Jogue com responsabilidade._"
    )
    return message


def send_message(text: str):
    """Send a message to the configured Telegram chat."""
    try:
        bot.send_message(CHAT_ID, text, parse_mode="Markdown")
    except Exception as e:
        print(f"[ERROR] Failed to send Telegram message: {e}")


def run_martingale_cycle():
    """
    Execute one full martingale cycle:
    - Fetch signal
    - Send initial entry message
    - If loss, apply gale up to MAX_GALES times
    """
    signal = get_signal()
    if not signal:
        print("[WARN] No signal received, skipping cycle.")
        return

    bet = BASE_BET
    result = signal.get("result")  # Expected: "win" | "loss"

    # Initial entry
    message = format_signal_message(signal, bet, gale=0)
    send_message(message)
    print(f"[INFO] Signal sent — bet: R${bet:.2f}, result: {result}")

    if result == "win":
        send_message("✅ *Resultado: WIN!* Aguardando próximo sinal...")
        return

    # Apply gale strategy on loss
    for gale in range(1, MAX_GALES + 1):
        bet *= MULTIPLIER
        time.sleep(5)  # Brief pause before next gale entry

        signal = get_signal()
        if not signal:
            print(f"[WARN] No signal on gale {gale}, aborting cycle.")
            return

        result = signal.get("result")
        message = format_signal_message(signal, bet, gale=gale)
        send_message(message)
        print(f"[INFO] Gale {gale} sent — bet: R${bet:.2f}, result: {result}")

        if result == "win":
            send_message(f"✅ *Resultado: WIN no Gale {gale}!* Aguardando próximo sinal...")
            return

    # All gales exhausted
    send_message(
        f"❌ *Resultado: LOSS após {MAX_GALES} gales.*\n"
        f"💸 Perda total estimada: `R$ {bet:.2f}`\n"
        f"🔄 Reiniciando ciclo com aposta base..."
    )
    print("[INFO] Martingale cycle ended in loss.")


def main():
    print("[INFO] AviatorProBot iniciado.")
    send_message("🚀 *AviatorProBot online!* Monitorando sinais do Aviator...")

    while True:
        run_martingale_cycle()
        time.sleep(30)  # Wait between cycles


if __name__ == "__main__":
    main()
