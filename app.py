import datetime
import requests
import telebot
import time
import os
import threading
from flask import Flask

# --- CONFIGURACIÓN PRINCIPAL ---
TOKEN = "8747149594:AAEZq2vH5KVBofOG59LM3IXZAt0ITiqhjq4"
CHAT_ID = "-1003991608285"
URL_API = "https://aviator-round-production.up.railway.app/api/aviator/rounds/1?limit=10"

# --- PARÁMETROS DE ESTRATEGIA ---
BANKROLL = 1000000
STAKE_1 = 0.01   # 1% de la banca
STAKE_2 = 0.027  # 2.7% de la banca (Gale)
TARGET_MULTIPLIER = 1.70

# --- GESTIÓN DE RIESGO ---
STOP_LOSS_TOTAL = 0.20  # Pausa larga si se pierde el 20%
PAUSE_TIME_LOSS = 900   # 15 minutos de pausa si se pierde un Gale

app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot Aviator 24/7 Operativo", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

class AviatorInfinityBot:
    def __init__(self):
        self.bot = telebot.TeleBot(token=TOKEN, parse_mode='MARKDOWN')
        self.balance = BANKROLL
        self.profit = 0
        self.history_signals = []
        
        # Estados de la operación
        self.entrada_en_curso = False
        self.gale_pendiente = False
        self.pause_until = None
        self.last_id_procesado = None # Para evitar mensajes dobles

    def enviar_telegram(self, texto):
        try:
            self.bot.send_message(chat_id=CHAT_ID, text=texto)
        except Exception as e:
            print(f"❌ Error enviando a Telegram: {e}")

    # --- MENSAJES ---
    def msg_entrada(self):
        msg = "🚀 *ENTRADA DETECTADA*\n\n"
        msg += f"🎯 Punto de Retiro: *{TARGET_MULTIPLIER:.2f}x*\n"
        msg += f"💰 Inversión sugerida: *{STAKE_1*100:.1f}%*\n\n"
        msg += "⚠️ *Ejecutar en la siguiente ronda*"
        self.enviar_telegram(msg)

    def msg_gale(self):
        msg = "⚠️ *MARTINGALA 1*\n\n"
        msg += "El avión se fue antes. Entramos de nuevo.\n"
        msg += f"💰 Inversión: *{STAKE_2*100:.1f}%*\n"
        msg += f"🎯 Retiro: *{TARGET_MULTIPLIER:.2f}x*"
        self.enviar_telegram(msg)

    def msg_win(self, valor):
        msg = f"✅ *¡WIN {valor:.2f}x!*\n"
        msg += "Estrategia aplicada con éxito."
        self.enviar_telegram(msg)

    def msg_loss(self, valor):
        msg = f"❌ *CICLO CERRADO {valor:.2f}x*\n"
        msg += "Gale fallido. Pausamos 15 min para analizar."
        self.enviar_telegram(msg)

    def msg_resumen(self):
        if not self.history_signals: return
        msg = "📊 *RESUMEN DE OPERACIONES*\n\n"
        for s in self.history_signals:
            icon = "✅" if s['status'] == 'win' else "❌"
            msg += f"{icon} Multiplicador: {s['res']:.2f}x (G{s['gale']})\n"
        
        profit_perc = (self.profit / BANKROLL) * 100
        msg += f"\n💰 *Profit Neto: {profit_perc:.2f}%*"
        self.enviar_telegram(msg)
        self.history_signals = []

    # --- LÓGICA DE FILTRADO ---
    def analizar_mercado(self, lista_multiplicadores):
        if len(lista_multiplicadores) < 5: return False
        
        # Evitamos entrar si hay rachas muy malas (velas < 1.10)
        if any(r < 1.10 for r in lista_multiplicadores[:3]): return False
        
        # Patrón de entrada: Si las últimas 2 rondas fueron estables (> 1.50 y > 1.20)
        # y no hay exceso de velas rosas recientes (para no entrar al final de la racha)
        if lista_multiplicadores[0] >= 1.50 and lista_multiplicadores[1] >= 1.20:
            return True
        return False

    def obtener_api(self):
        try:
            response = requests.get(URL_API, timeout=10)
            return response.json()
        except Exception as e:
            print(f"⚠️ Error de conexión API: {e}")
            return None

    def ejecutar_ciclo(self):
        print("🚀 Bot Aviator Infinity 24/7 iniciado...")
        
        while True:
            try:
                # 1. Control de Pausa
                if self.pause_until:
                    if datetime.datetime.now() < self.pause_until:
                        time.sleep(30)
                        continue
                    else:
                        print("⏳ Pausa terminada. Retomando búsqueda...")
                        self.pause_until = None

                # 2. Obtener datos
                data = self.obtener_api()
                if not data or not isinstance(data, list):
                    time.sleep(2)
                    continue

                ronda_actual = data[0]
                ronda_id = ronda_actual['id'] # El ID de tu API (ej: 31359)
                ronda_val = float(ronda_actual['max_multiplier'])
                historial_completo = [float(x['max_multiplier']) for x in data]

                # 3. FILTRO ANTI-DUPLICADOS (Crucial para no enviar mensajes dobles)
                if ronda_id == self.last_id_procesado:
                    time.sleep(1) # Esperar que la API actualice la siguiente ronda
                    continue
                
                # Si llegamos aquí, es una ronda nueva
                self.last_id_procesado = ronda_id
                print(f"📈 Nueva Ronda detectada: {ronda_id} -> {ronda_val}x")

                # 4. PROCESAR SI HAY UNA APUESTA ACTIVA
                if self.entrada_en_curso and not self.gale_pendiente:
                    if ronda_val >= TARGET_MULTIPLIER:
                        ganancia = (BANKROLL * STAKE_1) * (TARGET_MULTIPLIER - 1)
                        self.profit += ganancia
                        self.history_signals.append({'status': 'win', 'gale': 0, 'res': ronda_val})
                        self.msg_win(ronda_val)
                        self.entrada_en_curso = False
                    else:
                        # Falló la primera, activar Gale
                        self.gale_pendiente = True
                        self.msg_gale()
                    continue

                elif self.gale_pendiente:
                    if ronda_val >= TARGET_MULTIPLIER:
                        ganancia_neta = ((BANKROLL * STAKE_2) * (TARGET_MULTIPLIER - 1)) - (BANKROLL * STAKE_1)
                        self.profit += ganancia_neta
                        self.history_signals.append({'status': 'win', 'gale': 1, 'res': ronda_val})
                        self.msg_win(ronda_val)
                    else:
                        perdida_total = (BANKROLL * STAKE_1) + (BANKROLL * STAKE_2)
                        self.profit -= perdida_total
                        self.history_signals.append({'status': 'loss', 'gale': 1, 'res': ronda_val})
                        self.msg_loss(ronda_val)
                        # Pausar tras pérdida de ciclo
                        self.pause_until = datetime.datetime.now() + datetime.timedelta(seconds=PAUSE_TIME_LOSS)
                    
                    self.entrada_en_curso = False
                    self.gale_pendiente = False
                    continue

                # 5. BUSCAR NUEVA SEÑAL (Si no hay nada en curso)
                if self.analizar_mercado(historial_completo):
                    self.msg_entrada()
                    self.entrada_en_curso = True

                # 6. ENVIAR RESUMEN CADA 10 SEÑALES
                if len(self.history_signals) >= 10:
                    self.msg_resumen()

            except Exception as e:
                print(f"💥 Error en el bucle: {e}")
                time.sleep(5)

if __name__ == "__main__":
    # Iniciar servidor web para que el hosting no se apague
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Iniciar Bot
    aviator_bot = AviatorInfinityBot()
    aviator_bot.ejecutar_ciclo()