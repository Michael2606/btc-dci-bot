import logging
import os
import asyncio
import pandas as pd
import numpy as np
import httpx
from ta.momentum import RSIIndicator
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN:
    raise RuntimeError("❌ TOKEN inválido ou ausente. Configure a variável TOKEN no Render.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot RSI funcionando!")

async def fetch_price():
    url = "https://api.binance.com/api/v3/klines?symbol=BTCBRL&interval=1h&limit=100"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        data = r.json()
    closes = [float(candle[4]) for candle in data]
    return closes

async def check_rsi(context: ContextTypes.DEFAULT_TYPE):
    logger.info("📊 Checando RSI...")
    closes = await fetch_price()
    df = pd.DataFrame(closes, columns=["close"])
    rsi = RSIIndicator(df["close"], window=14).rsi()
    last_rsi = rsi.iloc[-1]
    logger.info(f"RSI atual: {last_rsi:.2f}")
    if last_rsi < 30:
        await context.bot.send_message(chat_id=CHAT_ID, text=f"📉 RSI: {last_rsi:.2f} — *Hora de comprar BTC*", parse_mode="Markdown")
    elif last_rsi > 70:
        await context.bot.send_message(chat_id=CHAT_ID, text=f"📈 RSI: {last_rsi:.2f} — *Mercado sobrecomprado*", parse_mode="Markdown")

async def main():
    logger.info("⚙️ Iniciando bot...")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.job_queue.run_repeating(check_rsi, interval=3600, first=10)
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
