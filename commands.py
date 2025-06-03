"""
Discord Bot Commands
Handles user-initiated fact-checking commands
"""

import discord
from discord.ext import commands
import asyncio
from typing import Optional

from bot.fact_checker import FactChecker
from bot.feedback import FeedbackView
from utils.rate_limiter import RateLimiter
from utils.logger import get_logger
from config.settings import BOT_CONFIG

def setup_commands(bot):
    """Setup all bot commands"""

    @bot.command(name='truthiness', aliases=['truth', 'verify'])
    @commands.cooldown(1, 30, commands.BucketType.user)  # 1 use per 30 seconds per user
    async def truthiness_command(ctx, *, claim: str = None):
        """
        Analyze the truthiness of a specific claim
        Usage: !truthiness <claim>
        """
        if not claim:
            embed = discord.Embed(
                title="❓ How to use truthiness",
                description="Please provide a claim to analyze.\n\n**Usage:** `!truthiness <your claim here>`\n\n**Example:** `!truthiness Drinking 8 glasses of water daily is necessary for health`",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return

        # Check if claim is too long
        if len(claim) > 1000:
            await ctx.send("❌ Claim is too long. Please keep it under 1000 characters.")
            return

        # Check if claim is too short
        if len(claim.strip()) < 10:
            await ctx.send("❌ Claim is too short. Please provide a more detailed statement to fact-check.")
            return

        try:
            # Show typing indicator
            async with ctx.typing():
                # Perform truthiness analysis
                result = await bot.fact_checker.check_claim(claim)

                if result:
                    embed = bot._create_truthiness_embed(
                        claim=claim,
                        result=result,
                        auto_check=False
                    )
                    view = FeedbackView(bot, result.get('accuracy', 'Unknown'))
                    await ctx.send(embed=embed, view=view)
                else:
                    embed = discord.Embed(
                        title="❌ Truthiness Analysis Failed",
                        description="I couldn't analyze this claim. This might be because:\n• The claim is too vague or subjective\n• There's an issue with the analysis service\n• The claim contains unsupported content",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)

        except Exception as e:
            bot.logger.error(f"Error in truthiness command: {e}")
            await ctx.send("❌ An error occurred while analyzing truthiness. Please try again later.")

    @bot.command(name='quickcheck', aliases=['qc'])
    @commands.cooldown(2, 60, commands.BucketType.user)  # 2 uses per minute per user
    async def quick_check_command(ctx, *, claim: str = None):
        """
        Quick fact-check with basic response
        Usage: !quickcheck <claim>
        """
        if not claim:
            await ctx.send("❓ Please provide a claim to quickly fact-check. Usage: `!quickcheck <claim>`")
            return

        if len(claim) > 500:
            await ctx.send("❌ Claim too long for quick check. Use `!factcheck` for longer claims.")
            return

        try:
            async with ctx.typing():
                result = await bot.fact_checker.check_claim(claim)

                if result:
                    accuracy = result.get('accuracy', 'Unknown')
                    confidence = result.get('confidence', 0)

                    # Create a simple response
                    if accuracy.lower() in ['true', 'mostly true']:
                        emoji = "✅"
                        color = discord.Color.green()
                    elif accuracy.lower() in ['false', 'mostly false']:
                        emoji = "❌"
                        color = discord.Color.red()
                    elif accuracy.lower() in ['mixed', 'partially true']:
                        emoji = "⚠️"
                        color = discord.Color.orange()
                    else:
                        emoji = "❓"
                        color = discord.Color.blue()

                    embed = discord.Embed(
                        title=f"{emoji} Quick Check Result",
                        description=f"**Assessment:** {accuracy}\n**Confidence:** {confidence}%",
                        color=color
                    )

                    if len(result.get('explanation', '')) > 0:
                        explanation = result['explanation'][:200] + "..." if len(result['explanation']) > 200 else result['explanation']
                        embed.add_field(name="Brief Explanation", value=explanation, inline=False)

                    await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ Could not perform quick fact-check on this claim.")

        except Exception as e:
            bot.logger.error(f"Error in quick-check command: {e}")
            await ctx.send("❌ Quick check failed. Please try again.")

    @bot.command(name='expose', aliases=['debunk', 'disprove'])
    @commands.cooldown(1, 45, commands.BucketType.user)  # 1 use per 45 seconds per user
    async def expose_command(ctx, *, claim: str = None):
        """
        Try to debunk/disprove a statement, or support it if debunking fails
        Usage: !expose <claim>
        """
        if not claim:
            embed = discord.Embed(
                title="❓ How to use expose",
                description="Please provide a claim to expose or validate.\n\n**Usage:** `!expose <your claim here>`\n\n**Example:** `!expose The moon landing was fake`",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return

        # Check if claim is too long
        if len(claim) > 1000:
            await ctx.send("❌ Claim is too long. Please keep it under 1000 characters.")
            return

        # Check if claim is too short
        if len(claim.strip()) < 10:
            await ctx.send("❌ Claim is too short. Please provide a more detailed statement to analyze.")
            return

        try:
            # Show typing indicator
            async with ctx.typing():
                # Perform expose analysis
                result = await bot.fact_checker.expose_claim(claim)

                if result:
                    embed = bot._create_expose_embed(
                        claim=claim,
                        result=result
                    )
                    view = FeedbackView(bot, result.get('expose_type', 'Unknown'))
                    await ctx.send(embed=embed, view=view)
                else:
                    embed = discord.Embed(
                        title="❌ Expose Analysis Failed",
                        description="I couldn't analyze this claim for debunking. This might be because:\n• The claim is too vague or subjective\n• There's an issue with the analysis service\n• The claim contains unsupported content",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)

        except Exception as e:
            bot.logger.error(f"Error in expose command: {e}")
            await ctx.send("❌ An error occurred while analyzing the claim. Please try again later.")

    @bot.command(name='settings', aliases=['config'])
    @commands.has_permissions(manage_guild=True)
    async def settings_command(ctx):
        """
        Show current bot settings (Admin only)
        """
        from config.settings import BOT_CONFIG

        embed = discord.Embed(
            title="⚙️ Bot Settings",
            description="Current configuration for this server",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Auto Fact-Check",
            value="✅ Enabled" if BOT_CONFIG['auto_fact_check'] else "❌ Disabled",
            inline=True
        )

        embed.add_field(
            name="Command Prefix",
            value=f"`{BOT_CONFIG['command_prefix']}`",
            inline=True
        )

        embed.add_field(
            name="Rate Limit",
            value=f"{BOT_CONFIG['rate_limit']['max_requests']} requests per {BOT_CONFIG['rate_limit']['time_window']}s",
            inline=True
        )

        embed.add_field(
            name="Trigger Keywords",
            value=f"{len(BOT_CONFIG['trigger_keywords'])} keywords configured",
            inline=True
        )

        embed.add_field(
            name="Respond to Bots",
            value="✅ Yes" if BOT_CONFIG['respond_to_bots'] else "❌ No",
            inline=True
        )

        await ctx.send(embed=embed)

    @bot.command(name='help')
    async def help_command(ctx, command_name: str = None):
        """
        Show help information
        """
        if command_name:
            # Show help for specific command
            command = bot.get_command(command_name)
            if command:
                embed = discord.Embed(
                    title=f"Help: {command.name}",
                    description=command.help or "No description available",
                    color=discord.Color.blue()
                )
                if command.aliases:
                    embed.add_field(
                        name="Aliases",
                        value=", ".join([f"`{alias}`" for alias in command.aliases]),
                        inline=False
                    )
            else:
                embed = discord.Embed(
                    title="❌ Command Not Found",
                    description=f"No command named `{command_name}` found.",
                    color=discord.Color.red()
                )
        else:
            # Show general help
            embed = discord.Embed(
                title="🔍 Discord Fact-Checker Bot",
                description="I help combat misinformation by fact-checking claims using AI.",
                color=discord.Color.blue()
            )

            embed.add_field(
                name="📋 Main Commands",
                value="""
`!truthiness <claim>` - Comprehensive truthiness analysis
`!quickcheck <claim>` - Quick fact-check
`!expose <claim>` - Debunk or validate claims
`!settings` - View bot settings (Admin)
`!help` - Show this help message
                """,
                inline=False
            )

            embed.add_field(
                name="🤖 Auto Fact-Checking",
                value="I automatically check messages that contain potential misinformation keywords or patterns.",
                inline=False
            )

            embed.add_field(
                name="⚡ Rate Limits",
                value="Commands have cooldowns to prevent spam and manage API usage.",
                inline=False
            )

            embed.add_field(
                name="🔗 Example",
                value="`!truthiness Vaccines contain microchips`",
                inline=False
            )

            embed.set_footer(text="Powered by Gemini 1.5 | Results may not be 100% accurate")

        await ctx.send(embed=embed)

    @bot.command(name='ping')
    async def ping_command(ctx):
        """Check bot latency"""
        latency = round(bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Bot latency: {latency}ms",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @bot.command(name='stats')
    async def stats_command(ctx):
        """Show bot statistics"""
        embed = discord.Embed(
            title="📊 Bot Statistics",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Servers",
            value=str(len(bot.guilds)),
            inline=True
        )

        embed.add_field(
            name="Users",
            value=str(len(bot.users)),
            inline=True
        )

        embed.add_field(
            name="Latency",
            value=f"{round(bot.latency * 1000)}ms",
            inline=True
        )

        await ctx.send(embed=embed)

    # Error handlers for commands
    @truthiness_command.error
    async def truthiness_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏰ Cooldown Active",
                description=f"Please wait {error.retry_after:.1f} seconds before using this command again.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)

    @expose_command.error
    async def expose_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏰ Cooldown Active",
                description=f"Please wait {error.retry_after:.1f} seconds before using expose again.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)

    @quick_check_command.error
    async def quick_check_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏰ Cooldown Active",
                description=f"Please wait {error.retry_after:.1f} seconds before using quick check again.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)

    @settings_command.error
    async def settings_error(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You need 'Manage Server' permission to view bot settings.")