# TeleAI-Poster/main.py (Updated for Deployment)
import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                             QPushButton, QTextEdit, QLineEdit, QLabel,
                             QComboBox, QMessageBox, QTabWidget, QFormLayout,
                             QScrollArea)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# Local imports
from config import (DEFAULT_AI_PROMPT, WINDOW_WIDTH, WINDOW_HEIGHT,
                    TELEGRAM_MAX_MESSAGE_LENGTH, DEFAULT_AI_MODEL)
from telegram_utils import send_telegram_message_sync
from ai_utils import generate_ai_content

# --- This function finds a safe, user-specific place to store config files ---
def get_config_path():
    """Gets the path to the configuration file in a user-specific directory."""
    app_name = "TeleAIPoster"
    # For Windows, this is typically C:/Users/<user>/AppData/Roaming/TeleAIPoster
    # For macOS, ~/Library/Application Support/TeleAIPoster
    # For Linux, ~/.config/TeleAIPoster
    if sys.platform == "win32":
        path = os.path.join(os.environ['APPDATA'], app_name)
    elif sys.platform == "darwin":
        path = os.path.join(os.path.expanduser('~/Library/Application Support'), app_name)
    else:
        path = os.path.join(os.path.expanduser('~/.config'), app_name)
    
    os.makedirs(path, exist_ok=True) # Ensure the directory exists
    return os.path.join(path, "config.json")

# Define the configuration file path
CONFIG_FILE = get_config_path()


# --- Worker Threads for Asynchronous Operations ---
# (These are unchanged from your original code)

class AiWorker(QThread):
    """
    A QThread subclass for performing AI content generation asynchronously.
    """
    finished = pyqtSignal(str) 

    def __init__(self, prompt: str, api_key: str, model: str):
        super().__init__()
        self.prompt = prompt
        self.api_key = api_key
        self.model = model

    def run(self):
        result = generate_ai_content(self.prompt, self.api_key, self.model)
        self.finished.emit(result)

class TelegramWorker(QThread):
    """
    A QThread subclass for sending Telegram messages asynchronously.
    """
    finished = pyqtSignal(bool, str) 

    def __init__(self, bot_token: str, chat_id: str, message: str):
        super().__init__()
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.message = message

    def run(self):
        success = send_telegram_message_sync(self.bot_token, self.chat_id, self.message)
        if success:
            self.finished.emit(True, "Content posted to Telegram successfully!")
        else:
            self.finished.emit(False, "Failed to post content. Check console for details.")


# --- Main Application Window ---
class TelegramAIPoster(QWidget):
    """
    The main GUI window for the TeleAI-Poster application.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle('TeleAI-Poster: AI Agent for Telegram')
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.initUI()
        # Load saved settings from config.json into the UI on startup
        self.load_settings()

    def initUI(self):
        """
        Sets up the layout and widgets for the application's user interface.
        """
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # --- Main Tab ---
        self.main_tab = QWidget()
        self.tabs.addTab(self.main_tab, "Main")
        main_tab_layout = QVBoxLayout()
        self.main_tab.setLayout(main_tab_layout)

        main_tab_layout.addWidget(QLabel("<h2>AI Prompt:</h2>"))
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText(DEFAULT_AI_PROMPT)
        self.prompt_input.setFixedHeight(120)
        self.prompt_input.setText(DEFAULT_AI_PROMPT)
        main_tab_layout.addWidget(self.prompt_input)

        self.generate_button = QPushButton("✨ Generate AI Content")
        self.generate_button.setStyleSheet(
            "background-color: #6A1B9A; color: white; font-weight: bold; padding: 10px; border-radius: 5px;"
        )
        self.generate_button.clicked.connect(self.generate_content)
        main_tab_layout.addWidget(self.generate_button)

        main_tab_layout.addWidget(QLabel("<h2>Generated Content Preview:</h2>"))
        self.content_preview = QTextEdit()
        self.content_preview.setPlaceholderText("AI generated content will appear here...")
        main_tab_layout.addWidget(self.content_preview)

        main_tab_layout.addWidget(QLabel("<h2>Post Target:</h2>"))
        self.target_display_label = QLabel("Configured Group/Channel: <span style='font-weight:bold;'>Not Set</span>")
        self.target_display_label.setTextFormat(Qt.RichText)
        main_tab_layout.addWidget(self.target_display_label)

        self.post_button = QPushButton("🚀 One-Click Post to Telegram")
        self.post_button.setStyleSheet(
            "background-color: #2196F3; color: white; font-weight: bold; padding: 15px; border-radius: 8px;"
        )
        self.post_button.clicked.connect(self.post_content)
        main_tab_layout.addWidget(self.post_button)

        self.status_label = QLabel("Ready.")
        self.status_label.setStyleSheet("color: gray; margin-top: 10px;")
        main_tab_layout.addWidget(self.status_label)

        # --- Settings Tab ---
        self.settings_tab = QWidget()
        self.tabs.addTab(self.settings_tab, "Settings")
        settings_layout = QVBoxLayout()
        self.settings_tab.setLayout(settings_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        settings_layout.addWidget(scroll_area)

        settings_content_widget = QWidget()
        scroll_area.setWidget(settings_content_widget)
        settings_form_layout = QFormLayout(settings_content_widget)

        settings_form_layout.addRow(QLabel("<h3>API Keys & Configuration:</h3>"))
        self.ai_api_key_input = QLineEdit()
        self.ai_api_key_input.setPlaceholderText("Enter your Google Gemini API Key")
        self.ai_api_key_input.setEchoMode(QLineEdit.Password)
        settings_form_layout.addRow("Gemini API Key:", self.ai_api_key_input)

        self.telegram_bot_token_input = QLineEdit()
        self.telegram_bot_token_input.setPlaceholderText("Enter your Telegram Bot Token")
        self.telegram_bot_token_input.setEchoMode(QLineEdit.Password)
        settings_form_layout.addRow("Telegram Bot Token:", self.telegram_bot_token_input)

        self.group_id_input = QLineEdit()
        self.group_id_input.setPlaceholderText("Enter Telegram Group/Channel ID (e.g., -123456789)")
        settings_form_layout.addRow("Telegram Group ID:", self.group_id_input)

        settings_form_layout.addRow(QLabel("<h3>AI Model Settings:</h3>"))
        self.ai_model_combo = QComboBox()
        self.ai_model_combo.addItems(["gemini-pro", "gemini-1.5-flash-latest", "gemini-1.5-pro-latest"])
        settings_form_layout.addRow("AI Model:", self.ai_model_combo)

        self.save_settings_button = QPushButton("💾 Save Settings")
        self.save_settings_button.clicked.connect(self.save_settings)
        self.save_settings_button.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; border-radius: 5px;"
        )
        settings_form_layout.addRow(self.save_settings_button)
        settings_layout.addStretch(1)

    def load_settings(self):
        """
        Loads API keys and group ID from the config.json file into the UI.
        If the file doesn't exist, the fields will remain empty for the user to fill.
        """
        try:
            with open(CONFIG_FILE, 'r') as f:
                settings = json.load(f)
                self.ai_api_key_input.setText(settings.get("GEMINI_API_KEY", ""))
                self.telegram_bot_token_input.setText(settings.get("TELEGRAM_BOT_TOKEN", ""))
                self.group_id_input.setText(settings.get("TELEGRAM_GROUP_ID", ""))
                self.ai_model_combo.setCurrentText(settings.get("AI_MODEL", DEFAULT_AI_MODEL))
            self.status_label.setText("Loaded saved settings.")
        except FileNotFoundError:
            self.status_label.setText("Welcome! Please enter your API keys in the Settings tab.")
        except json.JSONDecodeError:
             self.status_label.setText("Could not read settings file. Please re-save your settings.")

        self.update_target_display()

    def save_settings(self):
        """
        Saves the current settings from the UI into the config.json file.
        This makes them persistent across application restarts.
        """
        settings = {
            "GEMINI_API_KEY": self.ai_api_key_input.text(),
            "TELEGRAM_BOT_TOKEN": self.telegram_bot_token_input.text(),
            "TELEGRAM_GROUP_ID": self.group_id_input.text(),
            "AI_MODEL": self.ai_model_combo.currentText()
        }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(settings, f, indent=4)
            QMessageBox.information(self, "Settings Saved",
                                    f"Your settings have been saved locally to:\n{CONFIG_FILE}")
            self.update_target_display()
        except Exception as e:
            QMessageBox.critical(self, "Error Saving Settings", f"Could not save settings file: {e}")

    def update_target_display(self):
        """
        Updates the label on the 'Main' tab to show the current Group ID.
        """
        group_id = self.group_id_input.text().strip()
        if group_id:
            self.target_display_label.setText(
                f"Configured Group/Channel: <span style='font-weight:bold; color:#007bff;'>{group_id}</span>"
            )
        else:
            self.target_display_label.setText(
                "Configured Group/Channel: <span style='font-weight:bold; color:red;'>Not Set</span>"
            )

    def generate_content(self):
        """
        Initiates AI content generation.
        """
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Input Error", "Please enter a prompt for the AI.")
            return

        ai_api_key = self.ai_api_key_input.text().strip()
        if not ai_api_key:
            QMessageBox.warning(self, "API Key Missing", "Please enter your Gemini API Key in the Settings tab.")
            self.tabs.setCurrentIndex(1)
            return

        selected_model = self.ai_model_combo.currentText()
        self.status_label.setText("Generating AI content... Please wait.")
        self.generate_button.setEnabled(False)
        self.post_button.setEnabled(False)

        self.ai_thread = AiWorker(prompt, ai_api_key, selected_model)
        self.ai_thread.finished.connect(self.on_ai_content_generated)
        self.ai_thread.start()

    def on_ai_content_generated(self, result: str):
        """
        Callback for when the AiWorker thread finishes.
        """
        self.content_preview.setText(result)
        self.status_label.setText("AI content generated. Review and post!")
        self.generate_button.setEnabled(True)
        self.post_button.setEnabled(True)
        if "Error:" in result:
             QMessageBox.critical(self, "AI Generation Error", result)

    def post_content(self):
        """
        Initiates the Telegram message posting process.
        """
        content = self.content_preview.toPlainText().strip()
        group_id = self.group_id_input.text().strip()
        bot_token = self.telegram_bot_token_input.text().strip()

        if not all([content, group_id, bot_token]):
            QMessageBox.warning(self, "Configuration Error", "Please ensure content and all settings are filled out.")
            self.tabs.setCurrentIndex(1)
            return
        
        if len(content) > TELEGRAM_MAX_MESSAGE_LENGTH:
            QMessageBox.warning(self, "Content Too Long", f"Content exceeds Telegram's limit of {TELEGRAM_MAX_MESSAGE_LENGTH} characters and will be truncated.")
            content = content[:TELEGRAM_MAX_MESSAGE_LENGTH]

        self.status_label.setText("Posting to Telegram... Please wait.")
        self.generate_button.setEnabled(False)
        self.post_button.setEnabled(False)

        self.telegram_thread = TelegramWorker(bot_token, group_id, content)
        self.telegram_thread.finished.connect(self.on_telegram_post_finished)
        self.telegram_thread.start()

    def on_telegram_post_finished(self, success: bool, message: str):
        """
        Callback for when the TelegramWorker thread finishes.
        """
        if success:
            QMessageBox.information(self, "Success", message)
            self.status_label.setText("Content posted successfully!")
            self.content_preview.clear()
        else:
            QMessageBox.critical(self, "Posting Error", message)
            self.status_label.setText(f"Error posting: {message}")

        self.generate_button.setEnabled(True)
        self.post_button.setEnabled(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TelegramAIPoster()
    ex.show()
    sys.exit(app.exec_())
