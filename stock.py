import os
from dotenv import load_dotenv
import asyncio
import logging
import yfinance as yf
from telethon import TelegramClient, events,Button
from telethon.sessions import StringSession

load_dotenv()

logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s',handlers=[logging.FileHandler("xeqt.log"),logging.StreamHandler()])

# Replace these with your actual credentials
API_ID = os.getenv('API_ID')        # Replace with your Telegram API ID
API_HASH = os.getenv('API_HASH')   # Replace with your Telegram API Hash
BOT_TOKEN = os.getenv('BOT_TOKEN') # Replace with your Telegram Bot Token

# Initialize the Telegram client
client = TelegramClient('stock_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# In-memory storage for user preferences
user_preferences = {}

async def fetch_stock_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info

        # Safely extract data with defaults
        long_name = info.get('longName', 'No name available')
        current_price = info.get('currentPrice', 'N/A')
        previous_close = info.get('previousClose', 'N/A')
        day_low = info.get('dayLow', 'N/A')
        day_high = info.get('dayHigh', 'N/A')
        fifty_two_week_low = info.get('fiftyTwoWeekLow', 'N/A')
        fifty_two_week_high = info.get('fiftyTwoWeekHigh', 'N/A')
        market_cap = info.get('marketCap', 'N/A')
        trailing_pe = info.get('trailingPE', 'N/A')
        dividend_yield = info.get('dividendYield', 'N/A')

        # Handle possible type issues by converting to string and formatting
        response = (
            f"🌐 {long_name} ({symbol.upper()})\n"
            f"❗️ Current Price: ₹{current_price}\n"
            f"〽️ Previous Close: ₹{previous_close}\n"
            f"🕛 Day's Range: ₹{day_low} - ₹{day_high}\n"
            f"❇️ 52 Week Range: ₹{fifty_two_week_low} - ₹{fifty_two_week_high}\n"
            f"⏫ Market Cap: ₹{market_cap}\n"
            f"↪️ PE Ratio: {trailing_pe}\n"
            f"↪️ Dividend Yield: {dividend_yield if dividend_yield != 'N/A' else 'N/A'}"
        )

        return response

    except Exception as e:
        return f"⚠️ Error fetching data for {symbol.upper()}: {str(e)}"

async def send_periodic_updates(user_id, symbol, interval):
    while True:
        # Check if the user still wants to receive updates
        prefs = user_preferences.get(user_id, {})
        if not prefs.get('receive_updates', False):
            break

        # Fetch and send stock data
        stock_data = await fetch_stock_data(symbol)
        await client.send_message(user_id, stock_data)

        # Wait for the specified interval before next update
        await asyncio.sleep(interval * 60)  # interval is in minutes

@client.on(events.NewMessage(pattern='/stock\s+(\w+)\s*(\d*)'))
async def stock_handler(event):
    user_id = event.sender_id
    symbol = event.pattern_match.group(1).upper()
    interval_str = event.pattern_match.group(2)
    
    if interval_str:
        interval = int(interval_str)
        # Validate interval
        if interval < 1:
            await event.reply("⛔ Please provide an interval of at least 1 minute.")
            return

        # Store user preferences for periodic updates
        user_preferences[user_id] = {
            'symbol': symbol,
            'interval': interval,
            'receive_updates': True
        }

        # Acknowledge the command
        await event.reply(f"✅ Now you will receive a stock data update for {symbol} in every {interval} minute(s).")

        # Start the periodic update task
        asyncio.create_task(send_periodic_updates(user_id, symbol, interval))
    
    else:
        # Fetch and send stock data once
        stock_data = await fetch_stock_data(symbol)
        await event.reply(stock_data)

        # Remove user preferences to stop updates if any were previously set
        if user_id in user_preferences:
            user_preferences[user_id].pop('receive_updates', None)

@client.on(events.NewMessage(pattern='/stop'))
async def stop_handler(event):
    user_id = event.sender_id
    if user_preferences.get(user_id, {}).get('receive_updates', False):
        user_preferences[user_id]['receive_updates'] = False
        await event.reply("🛑 Stopped receiving stock updates.")
    else:
        await event.reply("⚠️There is No active Updates to Stop")

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    buttons = [
            [Button.url("🔰 Read Me 🔰", "https://telegra.ph/How-to-Use-Me-08-22")],
            [Button.url("➕ Add me to group➕",f"https://t.me/stock342bot?startgroup=true")]
        ]
    await event.respond(
        "Welcome to the Stock Update Bot!🤖\n\n"
        "Which stock do you want to know about\n"
        "You can Use /stock <stock_symbol>\n"
        "For More info Click on Read Me🔽",buttons=buttons)
    
@client.on(events.NewMessage(pattern='/id'))
async def send_user_id(event):
        user_id=event.sender_id
        await event.reply(f"🚫Your User ID is :`{user_id}`")

async def main():
    # Start the client and run until disconnected
    await client.start()
    print("Bot is running...")
    await client.run_until_disconnected()
with client:
    client.loop.run_until_complete(main())