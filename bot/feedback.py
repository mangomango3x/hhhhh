"""
Feedback System
Handles user feedback on fact-check responses
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from typing import Dict, Any
from utils.logger import get_logger

class FeedbackView(discord.ui.View):
    """View for feedback buttons on fact-check responses"""

    def __init__(self, bot, result_type: str):
        super().__init__(timeout=300)  # 5 minute timeout
        self.bot = bot
        self.result_type = result_type
        self.logger = get_logger(__name__)

    @discord.ui.button(label="👍 Helpful", style=discord.ButtonStyle.green)
    async def helpful_feedback(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle helpful feedback"""
        try:
            await interaction.response.send_message("✅ Thank you for your feedback! This helps improve our fact-checking.", ephemeral=True)
            self.logger.info(f"Helpful feedback received from {interaction.user.id} for {self.result_type}")
        except Exception as e:
            self.logger.error(f"Error handling helpful feedback: {e}")
            await interaction.response.send_message("❌ Error processing feedback.", ephemeral=True)

    @discord.ui.button(label="👎 Not Helpful", style=discord.ButtonStyle.red)
    async def not_helpful_feedback(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle not helpful feedback"""
        try:
            await interaction.response.send_message("📝 Thank you for your feedback! We'll work to improve our analysis.", ephemeral=True)
            self.logger.info(f"Not helpful feedback received from {interaction.user.id} for {self.result_type}")
        except Exception as e:
            self.logger.error(f"Error handling not helpful feedback: {e}")
            await interaction.response.send_message("❌ Error processing feedback.", ephemeral=True)

    async def on_timeout(self):
        """Called when the view times out"""
        # Disable all buttons when timeout occurs
        for item in self.children:
            item.disabled = True