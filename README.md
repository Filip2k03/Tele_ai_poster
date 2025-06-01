# TeleAI-Poster

TeleAI-Poster is a desktop application that uses AI to generate engaging social media posts and instantly publishes them to your Telegram group or channel. It features a user-friendly PyQt5 GUI, Google Gemini AI integration, and seamless Telegram posting.

## Features

- ✨ Generate concise, engaging content using Google Gemini AI
- 🚀 One-click posting to your Telegram group or channel
- 🔒 Secure API key management via `.env` file
- 🖥️ Easy-to-use PyQt5 interface with settings tab
- 🛠️ Customizable AI prompt and model selection

## Screenshots

![TeleAI-Poster Screenshot](screenshot.png) <!-- Add your screenshot here if available -->

## Getting Started

### Prerequisites

- Python 3.10+
- Telegram Bot (create via [@BotFather](https://t.me/BotFather))
- Google Gemini API Key ([get one here](https://aistudio.google.com/app/apikey))

### Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/yourusername/teleai-poster.git
   cd teleai-poster
   ```

2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**

   Copy `.env.example` to `.env` and fill in your credentials, or edit `.env` directly:
   ```env
   TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
   TELEGRAM_GROUP_ID="-1234567890"
   GEMINI_API_KEY="your-gemini-api-key"
   ```

### Usage

Run the application:

```sh
python main.py
```

- Enter your API keys and Telegram group/channel ID in the **Settings** tab.
- Write or edit your AI prompt.
- Click **Generate AI Content** to get a post suggestion.
- Review/edit the generated content.
- Click **One-Click Post to Telegram** to publish.

### Packaging (Optional)

To build a standalone executable (using PyInstaller):

```sh
pyinstaller main.spec
```

## File Structure

- [`main.py`](main.py): Main PyQt5 GUI application
- [`ai_utils.py`](ai_utils.py): Google Gemini AI integration
- [`telegram_utils.py`](telegram_utils.py): Telegram bot utilities
- [`config.py`](config.py): App configuration
- [`.env`](.env): API keys and secrets (not committed to GitHub)

## License

MIT License

---

**Note:** Never share your API keys publicly.
