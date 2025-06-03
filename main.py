"""
Discord Fact-Checker Bot
Main entry point for the Discord bot powered by Gemini 1.5
"""

import asyncio
import os
from dotenv import load_dotenv
from bot.discord_bot import FactCheckerBot
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

def main():
    """Main function to initialize and run the Discord bot"""
    # Setup logging
    logger = setup_logger()
    
    # Check for required environment variables
    discord_token = os.getenv('DISCORD_TOKEN')
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    
    if not discord_token:
        logger.error("DISCORD_TOKEN environment variable is required")
        return
    
    if not gemini_api_key:
        logger.error("GEMINI_API_KEY environment variable is required")
        return
    
    # Initialize and run the bot
    bot = FactCheckerBot()
    
    try:
        logger.info("Starting Discord Fact-Checker Bot...")
        bot.run(discord_token)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    main()
