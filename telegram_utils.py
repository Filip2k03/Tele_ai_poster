# TeleAI-Poster/telegram_utils.py
import asyncio
from telegram import Bot
from telegram.error import TelegramError, NetworkError
from httpx import HTTPStatusError # Import specific HTTP errors from httpx

async def send_telegram_message(bot_token: str, chat_id: str, message: str) -> bool:
    """
    Sends a message to a specified Telegram chat (group/channel).

    Args:
        bot_token (str): The HTTP API token of your Telegram bot.
        chat_id (str): The ID of the target chat (group/channel).
                       Group/Channel IDs are typically negative (e.g., -123456789).
        message (str): The text message to send.

    Returns:
        bool: True if the message was sent successfully, False otherwise.
    """
    if not bot_token:
        print("Telegram bot token is missing.")
        return False
    if not chat_id:
        print("Telegram chat ID is missing.")
        return False
    if not message:
        print("Message content is empty.")
        return False

    try:
        # Initialize the bot
        bot = Bot(token=bot_token)

        # Send the message
        await bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
        print(f"Message successfully sent to chat_id: {chat_id}")
        return True
    except HTTPStatusError as e: # Catch HTTP status errors, including 401 Unauthorized
        if e.response.status_code == 401:
            print(f"Error: Invalid Telegram Bot Token. Status 401 Unauthorized. Error: {e}")
        else:
            print(f"HTTP Status Error: {e.response.status_code} - {e.response.text}. Error: {e}")
        return False
    except NetworkError as e:
        print(f"Network Error: Could not connect to Telegram API. Check your internet connection or bot token. Error: {e}")
        return False
    except TelegramError as e: # Catch other general Telegram API errors
        print(f"Telegram API Error: {e}. Ensure the bot has permissions in the group/channel and the chat ID is correct.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred while sending Telegram message: {e}")
        return False

# This is a helper function to run the async send_telegram_message in a sync context
# for use with PyQt's event loop.
def send_telegram_message_sync(bot_token: str, chat_id: str, message: str) -> bool:
    """Synchronous wrapper for the async send_telegram_message function."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(send_telegram_message(bot_token, chat_id, message))

if __name__ == '__main__':
    # This block is for testing the telegram_utils independently
    # It requires you to set your .env variables correctly
    import os
    from dotenv import load_dotenv
    load_dotenv()

    test_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    test_group_id = os.getenv("TELEGRAM_GROUP_ID")
    test_message = "Hello from `telegram_utils.py` test script! This is a test message. " \
                   "Current time is {current_time}".format(current_time=asyncio.run(asyncio.sleep(0.1)) or "N/A")

    print(f"Attempting to send test message to group {test_group_id}...")
    success = send_telegram_message_sync(test_bot_token, test_group_id, test_message)
    if success:
        print("Test message sent successfully (if no errors above).")
    else:
        print("Failed to send test message.")