# Discord Fact-Checker Bot

A powerful Discord bot that combats misinformation by automatically fact-checking messages using Google's Gemini 1.5 AI model. The bot monitors conversations for potential misinformation and provides real-time fact-checking responses with sources and confidence ratings.

## ✨ Features

- **🤖 Automatic Fact-Checking**: Monitors messages for misinformation patterns and keywords
- **📋 Manual Commands**: Users can request fact-checks on specific claims
- **🎯 AI-Powered Analysis**: Uses Gemini 1.5 for comprehensive fact-checking
- **📊 Confidence Scoring**: Provides confidence levels for fact-check results
- **📚 Source Attribution**: Includes reliable sources when available
- **⚡ Rate Limiting**: Prevents API abuse and manages usage quotas
- **🔧 Configurable**: Extensive configuration options via environment variables
- **📝 Comprehensive Logging**: Detailed logging for monitoring and debugging

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Discord Bot Token
- Google Gemini API Key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/discord-fact-checker.git
   cd discord-fact-checker
   ```

2. **Install dependencies**
   ```bash
   pip install discord.py google-generativeai python-dotenv asyncio
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your credentials
   ```

4. **Run the bot**
   ```bash
   python main.py
   ```

## 🔧 Configuration

### Required Environment Variables

Create a `.env` file with the following required variables:

```bash
DISCORD_TOKEN=your_discord_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
