# TeleAI-Poster/main.py
import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTextEdit, QLineEdit, QLabel,
                             QComboBox, QMessageBox, QTabWidget, QFormLayout,
                             QScrollArea, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from dotenv import load_dotenv

# Local imports
from config import (DEFAULT_AI_PROMPT, WINDOW_WIDTH, WINDOW_HEIGHT,
                    TELEGRAM_MAX_MESSAGE_LENGTH, DEFAULT_AI_MODEL)
from telegram_utils import send_telegram_message_sync
from ai_utils import generate_ai_content

# Load environment variables at the very beginning of the application startup.
# This ensures that environment variables from the .env file are available
# throughout the application, including in imported modules like ai_utils.
load_dotenv()

# --- Worker Threads for Asynchronous Operations ---
# These classes run time-consuming operations (like API calls) in separate threads
# to prevent the GUI from freezing, ensuring a smooth user experience.

class AiWorker(QThread):
    """
    A QThread subclass for performing AI content generation asynchronously.
    Emits a signal with the generated content or an error message upon completion.
    """
    finished = pyqtSignal(str) # Signal to emit the result (generated text or error)

    def __init__(self, prompt: str, api_key: str, model: str):
        """
        Initializes the AI worker thread.
        Args:
            prompt (str): The text prompt for AI generation.
            api_key (str): The API key for the AI service (e.g., Gemini).
            model (str): The specific AI model to use (e.g., "gemini-pro").
        """
        super().__init__()
        self.prompt = prompt
        self.api_key = api_key
        self.model = model

    def run(self):
        """
        The main execution method for the thread.
        Calls the AI utility function and emits the result.
        """
        # Call the AI generation function from ai_utils.py
        result = generate_ai_content(self.prompt, self.api_key, self.model)
        self.finished.emit(result)

class TelegramWorker(QThread):
    """
    A QThread subclass for sending Telegram messages asynchronously.
    Emits a signal with the success status (bool) and a descriptive message (str).
    """
    finished = pyqtSignal(bool, str) # Signal to emit success status and a message

    def __init__(self, bot_token: str, chat_id: str, message: str):
        """
        Initializes the Telegram worker thread.
        Args:
            bot_token (str): The Telegram bot's API token.
            chat_id (str): The target Telegram chat ID (group/channel).
            message (str): The message content to send.
        """
        super().__init__()
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.message = message

    def run(self):
        """
        The main execution method for the thread.
        Calls the Telegram utility function and emits the result.
        """
        # Call the synchronous Telegram message sending function
        success = send_telegram_message_sync(self.bot_token, self.chat_id, self.message)
        if success:
            self.finished.emit(True, "Content posted to Telegram successfully!")
        else:
            # If send_telegram_message_sync returns False, it means an error occurred
            # The specific error message is printed to console by telegram_utils.py
            self.finished.emit(False, "Failed to post content to Telegram. Check console for details.")

# --- Main Application Window ---
class TelegramAIPoster(QWidget):
    """
    The main GUI window for the TeleAI-Poster application.
    Manages user input, AI generation, and Telegram posting.
    """
    def __init__(self):
        """
        Initializes the main application window and its UI components.
        """
        super().__init__()
        self.setWindowTitle('TeleAI-Poster: AI Agent for Telegram')
        # Set initial window size
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.initUI()
        # Load settings from .env file into UI fields on startup
        self.load_settings()

    def initUI(self):
        """
        Sets up the layout and widgets for the application's user interface.
        Organizes content into tabs for main functionality and settings.
        """
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Tab Widget for Main Content and Settings
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # --- Main Tab (AI Generation and Posting) ---
        self.main_tab = QWidget()
        self.tabs.addTab(self.main_tab, "Main")
        main_tab_layout = QVBoxLayout()
        self.main_tab.setLayout(main_tab_layout)

        # AI Prompt Input Area
        main_tab_layout.addWidget(QLabel("<h2>AI Prompt:</h2>"))
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText(DEFAULT_AI_PROMPT)
        self.prompt_input.setFixedHeight(120)
        self.prompt_input.setText(DEFAULT_AI_PROMPT) # Set default text from config
        main_tab_layout.addWidget(self.prompt_input)

        # Generate Content Button
        self.generate_button = QPushButton("✨ Generate AI Content")
        self.generate_button.setStyleSheet(
            "background-color: #6A1B9A; color: white; font-weight: bold; "
            "padding: 10px; border-radius: 5px;"
        )
        self.generate_button.clicked.connect(self.generate_content)
        main_tab_layout.addWidget(self.generate_button)

        # Generated Content Preview Area
        main_tab_layout.addWidget(QLabel("<h2>Generated Content Preview:</h2>"))
        self.content_preview = QTextEdit()
        self.content_preview.setPlaceholderText("AI generated content will appear here...")
        self.content_preview.setReadOnly(False) # Allow user to edit before posting
        main_tab_layout.addWidget(self.content_preview)

        # Display for the currently configured Telegram target
        main_tab_layout.addWidget(QLabel("<h2>Post Target:</h2>"))
        self.target_display_label = QLabel("Configured Group/Channel: <span style='font-weight:bold;'>Not Set</span>")
        self.target_display_label.setTextFormat(Qt.RichText) # Enable HTML-like text
        main_tab_layout.addWidget(self.target_display_label)

        # One-Click Post Button
        self.post_button = QPushButton("🚀 One-Click Post to Telegram")
        self.post_button.setStyleSheet(
            "background-color: #2196F3; color: white; font-weight: bold; "
            "padding: 15px; border-radius: 8px;"
        )
        self.post_button.clicked.connect(self.post_content)
        main_tab_layout.addWidget(self.post_button)

        # Status Bar / Message Label to show ongoing operations or results
        self.status_label = QLabel("Ready.")
        self.status_label.setStyleSheet("color: gray; margin-top: 10px;")
        main_tab_layout.addWidget(self.status_label)

        # --- Settings Tab ---
        self.settings_tab = QWidget()
        self.tabs.addTab(self.settings_tab, "Settings")
        settings_layout = QVBoxLayout()
        self.settings_tab.setLayout(settings_layout)

        # Use a QScrollArea for settings to handle many fields gracefully
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        settings_layout.addWidget(scroll_area)

        settings_content_widget = QWidget()
        scroll_area.setWidget(settings_content_widget)
        settings_form_layout = QFormLayout(settings_content_widget)

        # API Keys Input Section
        settings_form_layout.addRow(QLabel("<h3>API Keys:</h3>"))
        self.ai_api_key_input = QLineEdit()
        self.ai_api_key_input.setPlaceholderText("Enter your Google Gemini API Key (starts with AIza...)")
        self.ai_api_key_input.setEchoMode(QLineEdit.Password) # Hide characters for sensitive input
        settings_form_layout.addRow("Gemini API Key:", self.ai_api_key_input) # Updated label for Gemini

        self.telegram_bot_token_input = QLineEdit()
        self.telegram_bot_token_input.setPlaceholderText("Enter your Telegram Bot Token")
        self.telegram_bot_token_input.setEchoMode(QLineEdit.Password)
        settings_form_layout.addRow("Telegram Bot Token:", self.telegram_bot_token_input)

        # Telegram Group ID Input Section
        settings_form_layout.addRow(QLabel("<h3>Telegram Configuration:</h3>"))
        self.group_id_input = QLineEdit()
        self.group_id_input.setPlaceholderText("Enter Telegram Group/Channel ID (e.g., -123456789)")
        settings_form_layout.addRow("Telegram Group ID:", self.group_id_input)

        # AI Model Selection (Optional)
        settings_form_layout.addRow(QLabel("<h3>AI Model Settings:</h3>"))
        self.ai_model_combo = QComboBox()
        # List of available Gemini models. Update this list as new models become available.
        self.ai_model_combo.addItems(["gemini-pro", "gemini-1.5-flash-latest", "gemini-1.5-pro-latest"])
        self.ai_model_combo.setCurrentText(DEFAULT_AI_MODEL) # Set default from config.py
        settings_form_layout.addRow("AI Model:", self.ai_model_combo)

        # Save Settings Button
        self.save_settings_button = QPushButton("💾 Save Settings")
        self.save_settings_button.clicked.connect(self.save_settings)
        self.save_settings_button.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; "
            "padding: 10px; border-radius: 5px;"
        )
        settings_form_layout.addRow(self.save_settings_button)

        # Add some stretch at the end to push content to the top
        settings_layout.addStretch(1)

    def load_settings(self):
        """
        Loads API keys and group ID from environment variables (.env file)
        into the respective UI input fields on application startup.
        """
        self.ai_api_key_input.setText(os.getenv("GEMINI_API_KEY", "")) # Changed to GEMINI_API_KEY
        self.telegram_bot_token_input.setText(os.getenv("TELEGRAM_BOT_TOKEN", ""))
        self.group_id_input.setText(os.getenv("TELEGRAM_GROUP_ID", ""))
        self.update_target_display() # Update the display label based on loaded settings

    def save_settings(self):
        """
        This method is called when the "Save Settings" button is clicked.
        It primarily updates the UI's internal state and the target display label.
        Note: This does NOT save changes back to the .env file. Users must manually
        update their .env file for changes to persist across application restarts.
        """
        self.update_target_display()
        QMessageBox.information(self, "Settings Saved",
                                "Settings updated in UI. For persistence, manually update your .env file.")

    def update_target_display(self):
        """
        Updates the label on the 'Main' tab to show the currently configured
        Telegram group/channel ID.
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
        Initiates the AI content generation process.
        Retrieves the prompt and API key from UI, then starts an AiWorker thread.
        """
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Input Error", "Please enter a prompt for the AI.")
            return

        ai_api_key = self.ai_api_key_input.text().strip()
        if not ai_api_key:
            QMessageBox.warning(self, "API Key Missing",
                                "Please enter your Google Gemini API Key in the Settings tab.")
            self.tabs.setCurrentIndex(1) # Switch to settings tab
            return

        selected_model = self.ai_model_combo.currentText()

        self.status_label.setText("Generating AI content... Please wait.")
        # Disable buttons to prevent multiple concurrent operations
        self.generate_button.setEnabled(False)
        self.post_button.setEnabled(False)

        # Start AI generation in a separate thread to keep GUI responsive
        self.ai_thread = AiWorker(prompt, ai_api_key, selected_model)
        self.ai_thread.finished.connect(self.on_ai_content_generated)
        self.ai_thread.start()

    def on_ai_content_generated(self, result: str):
        """
        Callback function executed when the AiWorker thread finishes.
        Updates the content preview and re-enables buttons.
        Args:
            result (str): The generated text content or an error message.
        """
        self.content_preview.setText(result)
        self.status_label.setText("AI content generated. Review and post!")
        # Re-enable buttons
        self.generate_button.setEnabled(True)
        self.post_button.setEnabled(True)
        # Check if the result contains an error message from ai_utils
        if "Error:" in result:
             QMessageBox.critical(self, "AI Generation Error", result)

    def post_content(self):
        """
        Initiates the Telegram message posting process.
        Retrieves content, group ID, and bot token from UI, then starts a TelegramWorker thread.
        """
        content = self.content_preview.toPlainText().strip()
        group_id = self.group_id_input.text().strip()
        bot_token = self.telegram_bot_token_input.text().strip()

        if not content:
            QMessageBox.warning(self, "Input Error", "No content to post. Please generate or type content.")
            return

        if not group_id:
            QMessageBox.warning(self, "Configuration Error",
                                "Please enter the Telegram Group ID in the Settings tab.")
            self.tabs.setCurrentIndex(1) # Switch to settings tab
            return

        if not bot_token:
            QMessageBox.warning(self, "Configuration Error",
                                "Please enter your Telegram Bot Token in the Settings tab.")
            self.tabs.setCurrentIndex(1) # Switch to settings tab
            return

        # Check for Telegram message length limit
        if len(content) > TELEGRAM_MAX_MESSAGE_LENGTH:
            reply = QMessageBox.warning(self, "Content Too Long",
                                        f"The content ({len(content)} characters) exceeds Telegram's "
                                        f"message limit ({TELEGRAM_MAX_MESSAGE_LENGTH} characters). "
                                        "It will be truncated. Do you want to proceed?",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                self.status_label.setText("Posting cancelled due to message length.")
                return
            content = content[:TELEGRAM_MAX_MESSAGE_LENGTH] # Truncate content

        self.status_label.setText("Posting to Telegram... Please wait.")
        # Disable buttons during posting
        self.generate_button.setEnabled(False)
        self.post_button.setEnabled(False)

        # Start Telegram posting in a separate thread
        self.telegram_thread = TelegramWorker(bot_token, group_id, content)
        self.telegram_thread.finished.connect(self.on_telegram_post_finished)
        self.telegram_thread.start()

    def on_telegram_post_finished(self, success: bool, message: str):
        """
        Callback function executed when the TelegramWorker thread finishes.
        Displays success/error message and re-enables buttons.
        Args:
            success (bool): True if the message was sent successfully, False otherwise.
            message (str): A descriptive message about the posting result.
        """
        if success:
            QMessageBox.information(self, "Success", message)
            self.status_label.setText("Content posted successfully!")
            self.content_preview.clear() # Clear content after successful post
        else:
            QMessageBox.critical(self, "Posting Error", message)
            self.status_label.setText(f"Error posting: {message}")

        # Re-enable buttons
        self.generate_button.setEnabled(True)
        self.post_button.setEnabled(True)


if __name__ == '__main__':
    # Create the QApplication instance (necessary for any PyQt5 application)
    app = QApplication(sys.argv)
    # Create an instance of our main window
    ex = TelegramAIPoster()
    # Show the window
    ex.show()
    # Start the application's event loop
    sys.exit(app.exec_())
