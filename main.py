import telebot
from telebot import types
import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
import threading
import time
import schedule
import requests
import random
import string
import logging
import os
from flask import Flask

# ================= CONFIGURAÇÃO =================
TOKEN = '8255460383:AAG1znCT140k8Kidh7LXFtops4F0n77ckVo'
ADMIN_ID = 5125563829
ADMIN_USERNAME = '@AiltonArmindo'
ADMIN_EMAIL = 'ayltonanna@gmail.com'
BOT_USERNAME = '@BetMasterProBot'
SUPPORT_WHATSAPP = '+258848568229'

# Inicializar bot
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# ================= FUNÇÕES BÁSICAS =================
def init_database():
    """Inicializa banco de dados"""
    conn = sqlite3.connect('betmaster.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        is_vip INTEGER DEFAULT 0,
        daily_codes_used INTEGER DEFAULT 0,
        daily_codes_limit INTEGER DEFAULT 2,
        created_at TEXT,
        last_active TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS codes (
        code_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        code TEXT UNIQUE,
        created_at TEXT
    )
    ''')
    
    conn.commit()
    return conn, cursor

# Inicializar DB
conn, cursor = init_database()

# ================= COMANDOS DO BOT =================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
    
    # Registrar usuário
    cursor.execute('''
        INSERT OR IGNORE INTO users 
        (user_id, username, full_name, created_at, last_active) 
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, full_name, datetime.now(), datetime.now()))
    
    cursor.execute('UPDATE users SET last_active = ? WHERE user_id = ?', 
                  (datetime.now(), user_id))
    conn.commit()
    
    # Criar teclado
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🎯 GERAR CÓDIGO", callback_data="generate"),
        types.InlineKeyboardButton("💎 VER VIP", callback_data="vip_info")
    )
    markup.add(
        types.InlineKeyboardButton("📞 SUPORTE", url="https://t.me/AiltonArmindo"),
        types.InlineKeyboardButton("💰 PAGAMENTOS", callback_data="payments")
    )
    
    welcome_text = f"""
🏆 <b>BET MASTER PRO BOT</b>

👋 Olá <b>{full_name}</b>!
🆔 Seu ID: <code>{user_id}</code>

🎯 <b>COMANDOS DISPONÍVEIS:</b>
/start - Menu principal
/gerar - Gerar código (2 GRÁTIS/dia)
/vip - Planos VIP
/suporte - Falar com suporte

💎 <b>PLANOS VIP:</b>
• Diário: 150MT (10 códigos/dia)
• Semanal: 800MT (15 códigos/dia)
• Mensal: 2500MT (20 códigos/dia)
• Premium: 5000MT (30 códigos/dia)

📞 <b>SUPORTE:</b>
Telegram: @AiltonArmindo
WhatsApp: +258 84 856 8229
Email: ayltonanna@gmail.com

⚠️ <i>Jogue com responsabilidade!</i>
"""
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(commands=['gerar'])
def generate_code(message):
    user_id = message.from_user.id
    
    # Verificar limite diário
    cursor.execute('SELECT daily_codes_used, daily_codes_limit FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    if not result:
        bot.send_message(message.chat.id, "❌ Erro: Usuário não encontrado. Use /start primeiro.")
        return
    
    used, limit = result
    
    if used >= limit:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💎 VER PLANOS VIP", callback_data="vip_info"))
        
        bot.send_message(
            message.chat.id,
            f"❌ <b>LIMITE ATINGIDO!</b>\n\n"
            f"Você já usou {used}/{limit} códigos hoje.\n\n"
            f"💎 <b>Torne-se VIP para:</b>\n"
            f"• 10-30 códigos por dia\n"
            f"• Acesso premium\n"
            f"• Suporte prioritário\n\n"
            f"Use /vip para ver planos!",
            reply_markup=markup,
            parse_mode='HTML'
        )
        return
    
    # Gerar código
    code = f"BM{user_id:06d}{random.randint(1000, 9999)}"
    
    # Salvar no banco
    cursor.execute('''
        INSERT INTO codes (user_id, code, created_at)
        VALUES (?, ?, ?)
    ''', (user_id, code, datetime.now()))
    
    # Atualizar contador
    cursor.execute('''
        UPDATE users 
        SET daily_codes_used = daily_codes_used + 1,
            last_active = ?
        WHERE user_id = ?
    ''', (datetime.now(), user_id))
    
    conn.commit()
    
    # Mensagem de sucesso
    response = f"""
✅ <b>CÓDIGO GERADO COM SUCESSO!</b>

🔢 <b>Seu código:</b> <code>{code}</code>
📅 <b>Data:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}
🎫 <b>Tipo:</b> {'VIP 🎖️' if limit > 2 else 'Grátis ⭐'}
📊 <b>Uso hoje:</b> {used + 1}/{limit}

🏠 <b>CASAS RECOMENDADAS:</b>
• Betway - Use código promocional
• 1xBet - Bônus de boas-vindas
• PremierBet - Cashout rápido
• ElephantBet - Promoções diárias

💡 <b>COMO USAR:</b>
1. Acesse uma casa de apostas
2. Use o código no checkout
3. Confirme sua aposta

⚠️ <i>Válido por 24 horas. Jogue com responsabilidade!</i>
"""
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💎 COMPRAR MAIS CÓDIGOS", callback_data="vip_info"),
        types.InlineKeyboardButton("📞 SUPORTE", url="https://t.me/AiltonArmindo")
    )
    
    bot.send_message(message.chat.id, response, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(commands=['vip'])
def vip_command(message):
    vip_text = """
💎 <b>PLANOS VIP BET MASTER PRO</b>

<b>1. VIP DIÁRIO - 150MT</b>
• 10 códigos por dia
• Suporte por Telegram
• Validade: 24 horas

<b>2. VIP SEMANAL - 800MT</b>
• 15 códigos por dia
• Todos benefícios Diário
• Validade: 7 dias

<b>3. VIP MENSAL - 2.500MT</b>
• 20 códigos por dia
• Todos benefícios Semanal
• Grupo VIP exclusivo
• Validade: 30 dias

<b>4. VIP PREMIUM - 5.000MT</b>
• 30 códigos por dia
• Todos benefícios Mensal
• Mentoria pessoal
• Validade: 90 dias

📲 <b>FORMAS DE PAGAMENTO:</b>
• Emola: 870612404 - Ailton Armindo
• M-Pesa: 848568229 - Ailton Armindo
• PayPal: ayltonanna@gmail.com

⚡ <b>COMO COMPRAR:</b>
1. Escolha seu plano
2. Faça pagamento
3. Envie comprovante para @AiltonArmindo
4. Aguarde ativação (5-15 minutos)

📞 <b>SUPORTE:</b>
WhatsApp: +258 84 856 8229
Telegram: @AiltonArmindo
"""
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💰 DIÁRIO - 150MT", callback_data="buy_daily"),
        types.InlineKeyboardButton("🏆 SEMANAL - 800MT", callback_data="buy_weekly")
    )
    markup.add(
        types.InlineKeyboardButton("👑 MENSAL - 2500MT", callback_data="buy_monthly"),
        types.InlineKeyboardButton("🚀 PREMIUM - 5000MT", callback_data="buy_premium")
    )
    markup.add(
        types.InlineKeyboardButton("📞 FALAR COM VENDEDOR", url="https://t.me/AiltonArmindo")
    )
    
    bot.send_message(message.chat.id, vip_text, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(commands=['suporte'])
def support_command(message):
    support_text = f"""
📞 <b>SUPORTE BET MASTER PRO</b>

💬 <b>CONTATOS OFICIAIS:</b>
• Telegram: @AiltonArmindo
• WhatsApp: +258 84 856 8229
• Email: ayltonanna@gmail.com

🕒 <b>HORÁRIO DE ATENDIMENTO:</b>
• Segunda a Sexta: 08:00 - 22:00
• Sábado e Domingo: 09:00 - 20:00

🔧 <b>ASSUNTOS ATENDIDOS:</b>
• Ativação de VIP
• Problemas com códigos
• Dúvidas sobre pagamento
• Problemas técnicos

⚡ <b>PARA AGILIZAR:</b>
Informe seu ID: <code>{message.from_user.id}</code>
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("💬 TELEGRAM DIRETO", url="https://t.me/AiltonArmindo"),
        types.InlineKeyboardButton("📱 WHATSAPP", url="https://wa.me/258848568229")
    )
    
    bot.send_message(message.chat.id, support_text, reply_markup=markup, parse_mode='HTML')

# ================= CALLBACK HANDLERS =================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    data = call.data
    
    if data == "generate":
        generate_code(call.message)
    
    elif data == "vip_info":
        vip_command(call.message)
    
    elif data == "payments":
        payments_text = f"""
💰 <b>FORMAS DE PAGAMENTO</b>

🇲🇿 <b>PARA MOÇAMBIQUE:</b>
1. <b>EMOLA:</b> 870612404 - Ailton Armindo
2. <b>M-PESA:</b> 848568229 - Ailton Armindo

🌍 <b>INTERNACIONAL:</b>
3. <b>PAYPAL:</b> ayltonanna@gmail.com

📞 <b>CONTATOS:</b>
• Telegram: @AiltonArmindo
• WhatsApp: +258 84 856 8229
• Email: ayltonanna@gmail.com

⚡ <b>PROCEDIMENTO:</b>
1. Faça o pagamento
2. Envie comprovante
3. Informe seu ID: <code>{call.from_user.id}</code>
4. Aguarde ativação

✅ <b>GARANTIA:</b> Ativação em até 15 minutos!
"""
        bot.send_message(call.message.chat.id, payments_text, parse_mode='HTML')
    
    elif data.startswith("buy_"):
        plan = data.replace("buy_", "")
        plans = {
            "daily": {"name": "VIP Diário", "price": "150"},
            "weekly": {"name": "VIP Semanal", "price": "800"},
            "monthly": {"name": "VIP Mensal", "price": "2500"},
            "premium": {"name": "VIP Premium", "price": "5000"}
        }
        
        selected = plans.get(plan, {"name": "VIP", "price": "0"})
        
        buy_text = f"""
🛒 <b>COMPRAR {selected['name'].upper()}</b>

💰 <b>Preço:</b> {selected['price']}MT

📱 <b>PARA PAGAR:</b>
1. Faça transferência de {selected['price']}MT para:
   • Emola: 870612404
   • M-Pesa: 848568229
   • PayPal: ayltonanna@gmail.com

2. Envie comprovante para:
   • Telegram: @AiltonArmindo
   • WhatsApp: +258848568229

3. Informe:
   • Seu ID: <code>{call.from_user.id}</code>
   • Plano escolhido: {selected['name']}

4. Aguarde ativação (5-15 minutos)

🎁 <b>BÔNUS:</b> Ativação garantida em 15 minutos!
"""
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("📲 ENVIAR COMPROVANTE", url="https://t.me/AiltonArmindo"),
            types.InlineKeyboardButton("💬 WHATSAPP", url="https://wa.me/258848568229")
        )
        
        bot.send_message(call.message.chat.id, buy_text, reply_markup=markup, parse_mode='HTML')

# ================= WEB SERVER (PARA RAILWAY/HEROKU) =================
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bet Master Pro Bot</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            h1 { color: #2c3e50; }
            .status { color: #27ae60; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>🤖 Bet Master Pro Bot</h1>
        <p class="status">✅ ONLINE E FUNCIONANDO!</p>
        <p>Telegram: <a href="https://t.me/BetMasterProBot">@BetMasterProBot</a></p>
        <p>Suporte: @AiltonArmindo</p>
    </body>
    </html>
    """

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    """Inicia servidor Flask para keep-alive"""
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# ================= FUNÇÕES DE MANUTENÇÃO =================
def reset_daily_counts():
    """Reseta contadores diários à meia-noite"""
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
            cursor.execute('UPDATE users SET daily_codes_used = 0')
            conn.commit()
            print(f"[{now}] Contadores diários resetados")
        time.sleep(60)

# ================= INICIAR TUDO =================
def run_bot():
    """Função principal do bot"""
    print("🤖 Iniciando Bet Master Pro Bot...")
    print(f"👑 Admin: {ADMIN_USERNAME}")
    print(f"📞 Suporte: {SUPPORT_WHATSAPP}")
    
    try:
        bot.polling(none_stop=True, interval=1, timeout=30)
    except Exception as e:
        print(f"❌ Erro no bot: {e}")
        print("🔄 Reiniciando em 10 segundos...")
        time.sleep(10)
        run_bot()

if __name__ == '__main__':
    # Iniciar threads
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    reset_thread = threading.Thread(target=reset_daily_counts, daemon=True)
    
    flask_thread.start()
    reset_thread.start()
    
    # Iniciar bot
    run_bot()