import datetime
import requests
import telebot
import time
import json
import os
import threading
from flask import Flask

TOKEN = "8747149594:AAEZq2vH5KVBofOG59LM3IXZAt0ITiqhjq4"
CHAT_ID = "-1003991608285"
URL_API = "https://aviator-round-production.up.railway.app/api/aviator/rounds/1?limit=10"

BANKROLL = 1000000
STAKE_1 = 0.01
STAKE_2 = 0.027
TARGET_MULTIPLIER = 1.70

STOP_LOSS = 0.10
MAX_TRADES = 15
PAUSE_TIME = 900

app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot Aviator 24/7 Running", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

class AviatorConservativeBot:
    def __init__(self):
        self.token = TOKEN
        self.chat_id = CHAT_ID
        self.url_API = URL_API
        
        self.balance = BANKROLL
        self.profit = 0
        self.trades = []
        self.results = []
        self.history_signals = []
        
        self.entrada_en_curso = False
        self.gale_pendiente = False
        self.session_active = True
        self.trades_count = 0
        self.pause_until = None
        
        self._init_bot()

    def _init_bot(self):
        try:
            self.bot = telebot.TeleBot(token=self.token, parse_mode='MARKDOWN')
            print("✅ Bot inicializado correctamente")
        except Exception as e:
            print(f"❌ Error inicializando bot: {e}")

    def send_telegram_with_retry(self, message, max_retries=3):
        for attempt in range(max_retries):
            try:
                self.bot.send_message(chat_id=self.chat_id, text=message)
                return True
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(2)
        return False

    def mensaje_entrada(self):
        msg = "🚀 ENTRADA DETECTADA\n\n"
        msg += "🎯 Juego: Aviator\n"
        msg += f"📈 Retiro: {TARGET_MULTIPLIER:.2f}\n\n"
        msg += f"💰 Apuesta: {STAKE_1*100:.0f}% de tu banca\n\n"
        msg += "🧠 Condición del mercado: ESTABLE\n"
        msg += "⏳ Ejecutar en la próxima ronda\n\n"
        msg += "⚠️ Recuerda: seguimos sistema, no emociones"
        self.send_telegram_with_retry(msg)
        print("✅ ENTRADA enviada")

    def mensaje_gale(self):
        msg = "⚠️ GALE ACTIVADO\n\n"
        msg += "🔁 Continuación del ciclo\n\n"
        msg += f"💰 Apuesta: {STAKE_2*100:.1f}% de tu banca\n"
        msg += f"🎯 Retiro: {TARGET_MULTIPLIER:.2f}\n\n"
        msg += "🧠 Movimiento de recuperación en curso\n\n"
        msg += "❗ Mantén la calma y respeta la estrategia ❗"
        self.send_telegram_with_retry(msg)
        print("✅ GALE enviado")

    def mensaje_win(self, resultado):
        msg = "✅ CICLO GANADO\n\n"
        msg += "📈 Operación exitosa\n\n"
        msg += f"🎯 Resultado: {resultado:.2f}x\n\n"
        msg += "💰 Resultado positivo en la banca\n\n"
        msg += "🧠 Disciplina aplicada correctamente"
        self.send_telegram_with_retry(msg)
        print(f"✅ WIN registrado: {resultado}x")

    def mensaje_loss(self, resultado):
        msg = "❌ CICLO PERDIDO\n\n"
        msg += "📉 Se activó pérdida completa del ciclo\n\n"
        msg += f"🎯 Resultado: {resultado:.2f}x\n\n"
        msg += "🧠 Esto hace parte del sistema\n"
        msg += "🔒 Control de riesgo activo\n\n"
        msg += "⏸️ Esperando nueva condición"
        self.send_telegram_with_retry(msg)
        print(f"❌ LOSS registrado: {resultado}x")

    def mensaje_stop(self):
        msg = "🛑 STOP ACTIVADO\n\n"
        msg += "⚠️ Condición de riesgo detectada\n\n"
        msg += "⏸️ Pausando operaciones temporalmente\n\n"
        msg += "🧠 El sistema protege tu capital\n"
        msg += "⌛ Retomaremos en mejores condiciones"
        self.send_telegram_with_retry(msg)
        print("✅ STOP enviado")

    def mensaje_cierre(self, motivo):
        msg = "📊 SESIÓN FINALIZADA\n\n"
        msg += f"🎯 {motivo}\n\n"
        msg += "💰 Resultado consolidado\n\n"
        msg += "🧠 Recuerda: menos operaciones, mejor precisión\n\n"
        msg += "🚀 Nos vemos en la próxima sesión"
        self.send_telegram_with_retry(msg)
        print(f"✅ SESIÓN CERRADA: {motivo}")

    def mensaje_resumen(self):
        if not self.history_signals:
            return
        msg = "📊 RESUMEN SEÑALES\n\n"
        for signal in self.history_signals:
            status = "WIN" if signal['status'] == 'win' else "LOSS"
            msg += f"{status} {signal['resultado']:.2f} GALE {signal['gale']}\n"
        profit_percent = (self.profit / BANKROLL) * 100
        msg += f"\n💰 PROFIT {profit_percent:.1f}%"
        self.send_telegram_with_retry(msg)
        self.history_signals = []
        print(f"✅ RESUMEN enviado (Profit: {profit_percent:.1f}%)")

    def filtro_valido(self):
        if len(self.results) < 5:
            return False
        last5 = self.results[:5]
        last4 = self.results[:4]
        last3 = self.results[:3]
        last2 = self.results[:2]
        if any(r < 1.30 for r in last3):
            return False
        if sum(1 for r in last4 if r < 1.50) >= 2:
            return False
        if len(self.trades) >= 2 and self.trades[-2:] == ["loss", "loss"]:
            return False
        if sum(1 for r in last5 if r >= 1.70) >= 3 and all(r >= 1.50 for r in last2):
            return True
        return False

    def control_riesgo(self):
        if self.profit <= -BANKROLL * STOP_LOSS:
            self.mensaje_cierre(f"Límite de pérdida alcanzado (-{STOP_LOSS*100}%)")
            self.session_active = False
            return "STOP_LOSS"
        if len(self.trades) >= 2 and self.trades[-2:] == ["loss", "loss"]:
            self.pause_until = datetime.datetime.now() + datetime.timedelta(seconds=PAUSE_TIME)
            self.mensaje_stop()
            return "PAUSE"
        if self.trades_count >= MAX_TRADES:
            self.mensaje_cierre(f"Máximo de operaciones alcanzado ({MAX_TRADES})")
            self.session_active = False
            return "MAX_TRADES"
        return "CONTINUE"

    def ejecutar_trade(self, apuesta, resultado):
        if resultado >= TARGET_MULTIPLIER:
            return apuesta * (TARGET_MULTIPLIER - 1)
        return -apuesta

    def procesar_entrada(self, resultado):
        apuesta = BANKROLL * STAKE_1
        ganancia = self.ejecutar_trade(apuesta, resultado)
        if ganancia > 0:
            self.balance += ganancia
            self.profit += ganancia
            self.trades.append("win")
            self.trades_count += 1
            self.history_signals.append({'status': 'win', 'gale': 0, 'resultado': resultado})
            self.mensaje_win(resultado)
            self.entrada_en_curso = False
        else:
            self.gale_pendiente = True
            self.entrada_en_curso = False
            self.mensaje_gale()

    def procesar_gale(self, resultado):
        apuesta_1 = BANKROLL * STAKE_1
        apuesta_2 = BANKROLL * STAKE_2
        ganancia_2 = self.ejecutar_trade(apuesta_2, resultado)
        if ganancia_2 > 0:
            neto = ganancia_2 - apuesta_1
            self.balance += neto
            self.profit += neto
            self.trades.append("win")
            self.trades_count += 1
            self.history_signals.append({'status': 'win', 'gale': 1, 'resultado': resultado})
            self.mensaje_win(resultado)
        else:
            perdida = apuesta_1 + apuesta_2
            self.balance -= perdida
            self.profit -= perdida
            self.trades.append("loss")
            self.trades_count += 1
            self.history_signals.append({'status': 'loss', 'gale': 1, 'resultado': resultado})
            self.mensaje_loss(resultado)
        self.gale_pendiente = False

    def obtener_resultados(self):
        try:
            response = requests.get(self.url_API, timeout=5)
            data = response.json()
            if isinstance(data, list):
                return [float(e['max_multiplier']) for e in data][:5]
            return None
        except Exception as e:
            print(f"❌ Error API: {e}")
            return None

    def start(self):
        print("🚀 Bot Conservador 1.70 Iniciado 24/7...")
        check = []
        while True:
            try:
                if not self.session_active:
                    time.sleep(3600)
                    self.session_active, self.balance, self.profit = True, BANKROLL, 0
                    self.trades, self.trades_count, self.results, check = [], 0, [], []
                    continue
                if self.pause_until:
                    if datetime.datetime.now() < self.pause_until:
                        time.sleep(10)
                        continue
                    self.pause_until = None
                if self.control_riesgo() != "CONTINUE":
                    time.sleep(60)
                    continue
                time.sleep(1)
                results = self.obtener_resultados()
                if not results or check == results:
                    continue
                check = results
                if not self.results or results[0] != self.results[0]:
                    if self.results: self.results.insert(0, results[0])
                    else: self.results = results[:5]
                    if len(self.results) > 20: self.results = self.results[:20]
                    print(f"📈 Resultado: {results[0]}x | Historial: {[f'{r:.2f}' for r in self.results[:5]]}")
                    if self.entrada_en_curso and not self.gale_pendiente:
                        self.procesar_entrada(results[0])
                    elif self.gale_pendiente:
                        self.procesar_gale(results[0])
                    elif not self.entrada_en_curso and not self.gale_pendiente:
                        if self.filtro_valido():
                            self.mensaje_entrada()
                            self.entrada_en_curso = True
                if len(self.history_signals) >= 10:
                    self.mensaje_resumen()
            except Exception as e:
                print(f"⚠️ Error: {e}")
                time.sleep(2)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot = AviatorConservativeBot()
    bot.start()
