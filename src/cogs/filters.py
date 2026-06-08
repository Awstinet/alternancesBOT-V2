import discord
from discord import app_commands
from discord.ext import commands

from datas.databaseHandler import (
    getAllFilters,
    getUserFiltersID,
    addFilterTo,
    deleterFilterTo,
)


COLOR_INFO = 0x5865F2
COLOR_SUCCESS = 0x57F287
COLOR_ERROR = 0xED4245
COLOR_WARNING = 0xFEE75C


def _embed_mes_filtres(user: discord.User, filters: dict) -> discord.Embed:
    embed = discord.Embed(
        title="Mes filtres",
        description=(
            "Voici les mots-clefs sur lesquels tu es abonné.\n"
            "Utilise les boutons ci-dessous pour en ajouter ou en retirer."
        ),
        color=COLOR_INFO,
    )
    embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)

    if filters:
        embed.add_field(
            name="Filtres actifs",
            value="\n".join(f"• {nom}" for nom in filters.values()),
            inline=False,
        )
    else:
        embed.add_field(
            name="Aucun filtre",
            value="Tu n'as pas encore de filtre. Clique sur **Ajouter** pour commencer.",
            inline=False,
        )

    embed.set_footer(text="Les offres correspondant à tes filtres te seront notifiées automatiquement.")
    return embed


class AddFilterSelect(discord.ui.Select):
    def __init__(self, user_id: int, available: dict):
        """
        available : {filterID: nom} — filtres que l'utilisateur n'a pas encore.
        """
        options = [
            discord.SelectOption(label=nom, value=str(fid))
            for fid, nom in available.items()
        ]
        super().__init__(
            placeholder="Choisis un ou plusieurs filtres…",
            min_values=1,
            max_values=min(len(options), 5),
            options=options,
        )
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "Ce menu ne t'appartient pas.", ephemeral=True
            )
            return

        added = []
        for value in self.values:
            filter_id = int(value)
            filter_name = next(
                (opt.label for opt in self.options if opt.value == value), value
            )
            addFilterTo(self.user_id, filter_id)
            added.append(filter_name)

        embed = discord.Embed(
            title="Filtres ajoutés",
            description="Les filtres suivants ont bien été ajoutés à ton profil :",
            color=COLOR_SUCCESS,
        )
        embed.add_field(
            name="Nouveaux filtres",
            value="\n".join(f"• {n}" for n in added),
            inline=False,
        )

        await interaction.response.edit_message(embed=embed, view=None)


class AddFilterView(discord.ui.View):
    def __init__(self, user_id: int, available: dict):
        super().__init__(timeout=60)
        self.add_item(AddFilterSelect(user_id, available))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


class RemoveFilterSelect(discord.ui.Select):
    def __init__(self, user_id: int, user_filters: dict):
        """
        user_filters : {usersFilters.id: nom} — filtres actuels de l'utilisateur.
        """
        options = [
            discord.SelectOption(label=nom, value=str(uf_id))
            for uf_id, nom in user_filters.items()
        ]
        super().__init__(
            placeholder="Choisis les filtres à retirer…",
            min_values=1,
            max_values=len(options),
            options=options,
        )
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "Ce menu ne t'appartient pas.", ephemeral=True
            )
            return

        removed = []
        for value in self.values:
            uf_id = int(value)
            filter_name = next(
                (opt.label for opt in self.options if opt.value == value), value
            )
            deleterFilterTo(uf_id)
            removed.append(filter_name)

        embed = discord.Embed(
            title="Filtres retirés",
            description="Les filtres suivants ont été supprimés de ton profil :",
            color=COLOR_WARNING,
        )
        embed.add_field(
            name="Filtres supprimés",
            value="\n".join(f"• {n}" for n in removed),
            inline=False,
        )

        await interaction.response.edit_message(embed=embed, view=None)


class RemoveFilterView(discord.ui.View):
    def __init__(self, user_id: int, user_filters: dict):
        super().__init__(timeout=60)
        self.add_item(RemoveFilterSelect(user_id, user_filters))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


class FiltersMainView(discord.ui.View):
    def __init__(self, user: discord.User):
        super().__init__(timeout=120)
        self.user = user

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

    @discord.ui.button(label="Ajouter", style=discord.ButtonStyle.primary)
    async def btn_add(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "Ce menu ne t'appartient pas.", ephemeral=True
            )
            return

        all_filters  = getAllFilters()
        user_filters = getUserFiltersID(interaction.user.id)
        user_filter_names = set(user_filters.values())

        available = {
            fid: nom
            for fid, nom in all_filters.items()
            if nom not in user_filter_names
        }

        if not available:
            await interaction.response.send_message(
                "Tu as déjà tous les filtres disponibles !", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Ajouter des filtres",
            description="Sélectionne les filtres que tu veux ajouter :",
            color=COLOR_INFO,
        )
        await interaction.response.send_message(
            embed=embed,
            view=AddFilterView(interaction.user.id, available),
        )

    @discord.ui.button(label="Retirer", style=discord.ButtonStyle.danger)
    async def btn_remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "Ce menu ne t'appartient pas.", ephemeral=True
            )
            return

        user_filters = getUserFiltersID(interaction.user.id)

        if not user_filters:
            await interaction.response.send_message(
                "Tu n'as aucun filtre à retirer.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Retirer des filtres",
            description="Sélectionne les filtres que tu veux supprimer :",
            color=COLOR_WARNING,
        )
        await interaction.response.send_message(
            embed=embed,
            view=RemoveFilterView(interaction.user.id, user_filters),
        )


class FiltersCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="filtres", description="Gérer tes filtres de recherche d'alternances")
    async def filtres(self, interaction: discord.Interaction):
        user_filters = getUserFiltersID(interaction.user.id)
        embed = _embed_mes_filtres(interaction.user, user_filters)
        await interaction.response.send_message(
            embed=embed,
            view=FiltersMainView(interaction.user),
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(FiltersCog(bot))