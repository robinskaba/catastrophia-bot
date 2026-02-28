from discord import (
    Color,
    Embed,
    Interaction,
    Object,
    app_commands,
)
from discord.ext import commands
from discord.app_commands import Choice

from src.core.services.stats_service import StatsService
from src.core.services.user_service import UserService


async def _answer_unknown_user(
    interaction: Interaction, username: str, followup: bool = False
):
    embed = Embed(title=f"{username}", description="No user found.", color=Color.red())
    response = interaction.followup if followup else interaction.response
    await response.send_message(embed=embed, ephemeral=True)


class RobloxCog(commands.Cog):
    """Cog with commands to manage the Discord server."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.user_service = UserService()
        self.stats_service = StatsService()

    @app_commands.command(
        name="player", description="Lists information about a player."
    )
    async def show_player_info(self, interaction: Interaction, username: str):
        await interaction.response.defer(
            ephemeral=True
        )  # defering since might take longer

        user = self.user_service.get_user(username)
        user = self.user_service.get_detailed_user(user.id) if user else None
        if not user:
            await _answer_unknown_user(interaction, username, followup=True)
            return

        embed = Embed(title=user.name, color=Color.random())
        embed.set_thumbnail(url=self.user_service.get_user_thumbnail_url(user))

        # Roblox information
        embed.add_field(
            name="Roblox",
            value=f"ID: {user.id}\nAccount age: {user.account_age_in_days} days\nPremium: {user.premium}\nLocale: {user.locale}\n\n",
            inline=False,
        )

        # Catastrophia information
        spent_rbx = self.user_service.get_robux_spent(user)
        spent_rbx = f"{spent_rbx:,}".replace(",", " ")  # formatting
        playtime = self.stats_service.get_player_playtime(user.name)
        embed.add_field(
            name="Catastrophia",
            value=f"**Spent: {spent_rbx}** RBX\nPlaytime: {playtime // 60} hours\n",
            inline=False,
        )

        # Restrictions
        restrictions = self.user_service.get_user_restrictions(user)
        restrictions = restrictions if restrictions else []
        is_banned = restrictions[0].is_ongoing if len(restrictions) > 0 else False

        message = "```text\n"
        if len(restrictions) == 0:
            message += "no bans yet.."
        else:
            for restriction in restrictions:
                date_str = restriction.time.strftime("%d.%m.%y %H:%M")
                dur_text = (
                    f"({restriction.duration // 3600} h)"
                    if restriction.duration
                    else ""
                )
                reason = restriction.reason if restriction.active else "unbanned"
                message += f"[{date_str}] {dur_text}\n> {reason}\n"
        message += "```"

        status_msg = f"is banned" if is_banned else "is not banned"
        embed.add_field(
            name="Restrictions",
            value=f"{user.name} **{status_msg}**\n{message}",
            inline=False,
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name="roblox-ban", description="Bans a Roblox user from Catastrophia"
    )
    @app_commands.choices(
        ban_alts=[
            Choice(name="Yes", value=1),
            Choice(name="Do not ban alts", value=0),
        ],
        show_response=[
            Choice(name="Yes", value=1),
            Choice(name="No", value=0),
        ],
    )
    async def ban_roblox_user(
        self,
        interaction: Interaction,
        username: str,
        reason: str = "",
        duration_in_days: int | None = None,
        ban_alts: int = 1,
        show_response: int = 0,
    ):
        user = self.user_service.get_user(username)
        if not user:
            await _answer_unknown_user(interaction, username)
            return

        success = self.user_service.add_user_restriction(
            user, reason, duration_in_days, ban_alts
        )

        duration_str = (
            f"for {duration_in_days} days" if duration_in_days else "permanently"
        )
        message = (
            f"was banned {duration_str}."
            if success
            else "wasn't banned due to an error (probably too many requests)!"
        )

        embed = Embed(
            title=f"Banning {user.name}",
            description=f"{user.name} {message}",
            color=Color.red(),
        )
        await interaction.response.send_message(
            embed=embed, ephemeral=not show_response
        )

    @app_commands.command(
        name="roblox-unban", description="Unbans a Roblox user from Catastrophia"
    )
    @app_commands.choices(
        show_response=[
            Choice(name="Yes", value=1),
            Choice(name="No", value=0),
        ],
    )
    async def unban_roblox_user(
        self, interaction: Interaction, username: str, show_response: int = 0
    ) -> bool:
        user = self.user_service.get_user(username)
        if not user:
            await _answer_unknown_user(interaction, username)
            return

        success = self.user_service.remove_user_restriction(user)
        message = (
            "was unbanned."
            if success
            else "wasn't unbanned due to an error (probably too many requests)!"
        )

        embed = Embed(
            title=f"Unbanning {user.name}",
            description=f"{user.name} {message}",
            color=Color.green(),
        )
        await interaction.response.send_message(
            embed=embed, ephemeral=not show_response
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RobloxCog(bot), guilds=[Object(id=bot.guild_id)])
