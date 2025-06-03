"""
Discord Bot Implementation
Handles Discord interactions and message monitoring
"""

import discord
from discord.ext import commands
import asyncio
import re
from typing import Optional

from bot.fact_checker import FactChecker
from bot.commands import setup_commands
from bot.feedback import FeedbackView
from utils.rate_limiter import RateLimiter
from utils.logger import get_logger
from config.settings import BOT_CONFIG

class FactCheckerBot(commands.Bot):
    """Main Discord bot class for fact-checking functionality"""

    def __init__(self):
        # Configure bot intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        super().__init__(
            command_prefix=BOT_CONFIG['command_prefix'],
            intents=intents,
            help_command=None  # Disable default help to use custom one
        )

        self.logger = get_logger(__name__)
        self.fact_checker = FactChecker()
        self.rate_limiter = RateLimiter(
            max_requests=BOT_CONFIG['rate_limit']['max_requests'],
            time_window=BOT_CONFIG['rate_limit']['time_window']
        )

        # Keywords that might indicate misinformation
        self.trigger_keywords = BOT_CONFIG['trigger_keywords']

        # Setup commands
        setup_commands(self)

    async def on_ready(self):
        """Called when the bot is ready and connected to Discord"""
        self.logger.info(f'{self.user} has connected to Discord!')
        self.logger.info(f'Bot is in {len(self.guilds)} guilds')

        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for misinformation | !factcheck"
            )
        )

    async def on_message(self, message):
        """Process incoming messages for potential fact-checking"""
        # Ignore messages from the bot itself
        if message.author == self.user:
            return

        # Ignore messages from other bots unless specifically configured
        if message.author.bot and not BOT_CONFIG['respond_to_bots']:
            return

        # Check if bot is mentioned in a reply
        if message.reference and self.user in message.mentions:
            await self._handle_reply_with_mention(message)
            return

        # Process commands first
        await self.process_commands(message)

        # Check if automatic fact-checking is enabled
        if not BOT_CONFIG['auto_fact_check']:
            return

        # Check rate limiting
        if not self.rate_limiter.check_rate_limit(str(message.author.id)):
            return

        # Check if message contains potential misinformation triggers
        if self._should_fact_check(message.content):
            await self._auto_fact_check(message)

    def _should_fact_check(self, content: str) -> bool:
        """Determine if a message should be automatically fact-checked"""
        content_lower = content.lower()

        # Check for trigger keywords
        for keyword in self.trigger_keywords:
            if keyword.lower() in content_lower:
                return True

        # Check for common misinformation patterns
        patterns = [
            r'\b(studies? show|research proves|scientists say)\b',
            r'\b(breaking|urgent|exclusive)\b.*\b(news|report)\b',
            r'\b(they don\'t want you to know|hidden truth|cover[- ]?up)\b',
            r'\b(miracle cure|secret remedy|doctors hate)\b',
            r'\b(\d+% of (people|doctors|scientists))\b',
        ]

        for pattern in patterns:
            if re.search(pattern, content_lower):
                return True

        return False

    async def _auto_fact_check(self, message):
        """Automatically fact-check a message"""
        try:
            # Show typing indicator
            async with message.channel.typing():
                # Perform fact-check
                result = await self.fact_checker.check_claim(message.content)

                if result:
                    embed = self._create_truthiness_embed(
                        claim=message.content[:100] + "..." if len(message.content) > 100 else message.content,
                        result=result,
                        auto_check=True
                    )

                    await message.reply(embed=embed, mention_author=False)

        except Exception as e:
            self.logger.error(f"Error in auto fact-check: {e}")
            # Don't send error messages for auto fact-checks to avoid spam

    def _create_truthiness_embed(self, claim: str, result: dict, auto_check: bool = False) -> discord.Embed:
        """Create an embed for fact-check results"""
        # Determine embed color based on accuracy
        accuracy = result.get('accuracy', 'unknown').lower()
        if accuracy in ['true', 'mostly true']:
            color = discord.Color.green()
        elif accuracy in ['false', 'mostly false']:
            color = discord.Color.red()
        elif accuracy in ['mixed', 'partially true']:
            color = discord.Color.orange()
        else:
            color = discord.Color.blue()

        title = "🔍 Truthiness Analysis" + (" (Auto)" if auto_check else "")
        embed = discord.Embed(title=title, color=color)

        # Add claim field
        embed.add_field(
            name="📝 Claim",
            value=f"```{claim}```",
            inline=False
        )

        # Add accuracy assessment
        embed.add_field(
            name="🎯 Assessment",
            value=f"**{result.get('accuracy', 'Unknown')}**",
            inline=True
        )

        # Add confidence score if available
        if 'confidence' in result:
            embed.add_field(
                name="📊 Truth Percentage",
                value=f"{result['confidence']}%",
                inline=True
            )

        # Add AI model info
        embed.add_field(
            name="🤖 AI Model",
            value="Gemini 1.5 Flash",
            inline=True
        )

        # Add explanation
        if 'explanation' in result:
            explanation = result['explanation']
            if len(explanation) > 1024:
                explanation = explanation[:1021] + "..."
            embed.add_field(
                name="💭 Explanation",
                value=explanation,
                inline=False
            )

        # Add sources if available
        if 'sources' in result and result['sources']:
            sources_text = "\n".join([f"• {source}" for source in result['sources'][:3]])
            if len(result['sources']) > 3:
                sources_text += f"\n... and {len(result['sources']) - 3} more"
            embed.add_field(
                name="📚 Sources",
                value=sources_text,
                inline=False
            )

        # Add footer
        embed.set_footer(
            text="Powered by Gemini 1.5 | Results may not be 100% accurate",
            icon_url="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/google/google-original.svg"
        )

        return embed

    def _create_expose_embed(self, claim: str, result: dict) -> discord.Embed:
        """Create an embed for expose analysis results"""
        # Determine embed color based on expose result
        expose_type = result.get('expose_type', 'unknown').lower()
        if expose_type == 'debunked':
            color = discord.Color.red()
            title = "🔥 Claim Exposed & Debunked"
        elif expose_type == 'supported':
            color = discord.Color.green()
            title = "✅ Claim Validated & Supported"
        else:
            color = discord.Color.blue()
            title = "🔍 Expose Analysis"

        embed = discord.Embed(title=title, color=color)

        # Add claim field
        embed.add_field(
            name="📝 Claim",
            value=f"```{claim}```",
            inline=False
        )

        # Add expose result
        embed.add_field(
            name="🎯 Result",
            value=f"**{result.get('expose_type', 'Unknown').title()}**",
            inline=True
        )

        # Add confidence score if available
        if 'confidence' in result:
            embed.add_field(
                name="📊 Confidence",
                value=f"{result['confidence']}%",
                inline=True
            )

        # Add AI model info
        embed.add_field(
            name="🤖 AI Model",
            value="Gemini 1.5 Flash",
            inline=True
        )

        # Add analysis
        if 'analysis' in result:
            analysis = result['analysis']
            if len(analysis) > 1024:
                analysis = analysis[:1021] + "..."
            embed.add_field(
                name="🔍 Analysis",
                value=analysis,
                inline=False
            )

        # Add evidence if available
        if 'evidence' in result and result['evidence']:
            evidence_text = "\n".join([f"• {evidence}" for evidence in result['evidence'][:3]])
            if len(result['evidence']) > 3:
                evidence_text += f"\n... and {len(result['evidence']) - 3} more"
            embed.add_field(
                name="📚 Evidence",
                value=evidence_text,
                inline=False
            )

        # Add footer
        embed.set_footer(
            text="Powered by Gemini 1.5 | Analysis may not be 100% accurate",
            icon_url="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/google/google-original.svg"
        )

        return embed

    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Missing required argument. Use `!help` for command usage.")

        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ Command is on cooldown. Try again in {error.retry_after:.1f} seconds.")

        else:
            self.logger.error(f"Command error: {error}")
            await ctx.send("❌ An error occurred while processing your command.")

    async def _handle_reply_with_mention(self, message):
        """Handles a message that is a reply and mentions the bot"""
        try:
            # Get the original message being replied to
            replied_message = await message.channel.fetch_message(message.reference.message_id)

            # Combine the original message and the reply content for fact-checking
            combined_content = f"{replied_message.content}\n{message.content}"

            # Perform fact-check
            result = await self.fact_checker.check_claim(combined_content)

            if result:
                embed = self._create_truthiness_embed(
                    claim=combined_content[:100] + "..." if len(combined_content) > 100 else combined_content,
                    result=result,
                    auto_check=False  # It's a reply, so not an automatic check
                )

                # Send the embed with feedback buttons
                view = FeedbackView(self, result['accuracy'])
                await message.reply(embed=embed, mention_author=False, view=view)

        except discord.NotFound:
            await message.reply("❌ Original message not found.", mention_author=False)
        except Exception as e:
            self.logger.error(f"Error handling reply with mention: {e}")
            await message.reply("❌ An error occurred while processing your request.", mention_author=False)