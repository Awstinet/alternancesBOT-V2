import discord
from discord import app_commands
from discord.ext import commands
import datetime

from datas.databaseHandler import (
    addUserApplication,
    deleteUserApplication,
    getUserApplications,
    changeStatus,
)
from config import config

COLOR_INFO = 0x5865F2
COLOR_SUCCESS = 0x57F287
COLOR_ERROR = 0xED4245
COLOR_WARNING = 0xFEE75C
COLOR_NEUTRAL = 0x99AAB5

STATUS_LABELS = {
    "applied": ("Candidature envoyée", COLOR_INFO),
    "revived": ("Relancé", COLOR_WARNING),
    "interview": ("Entretien", 0xEB459E),
    "accepted": ("Accepté", COLOR_SUCCESS),
    "refused": ("Refusé", COLOR_ERROR),
}

def _status_display(status: str) -> str:
    label, _ = STATUS_LABELS.get(status, ("Inconnu", COLOR_NEUTRAL))
    return label


def _embed_candidatures(user: discord.User, applications) -> discord.Embed:
    embed = discord.Embed(
        title="Mes candidatures",
        description="Voici toutes tes candidatures en cours.",
        color=COLOR_INFO,
    )
    embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)

    if applications is None or len(applications) == 0:
        embed.add_field(
            name="Aucune candidature",
            value="Tu n'as pas encore ajouté de candidature. Clique sur **Ajouter** !",
            inline=False,
        )
    else:
        for row in applications:
            app_id, _, company, post, date_apply, date_revival, status = row
            status_str = _status_display(status)
            embed.add_field(
                name=f"{company} — {post}",
                value=(
                    f"**Statut :** {status_str}\n"
                    f"**Postulé le :** {date_apply}\n"
                    f"**Relance le :** {date_revival}\n"
                    f"*ID : `{app_id}`*"
                ),
                inline=True,
            )

    embed.set_footer(text="Les relances sont automatiquement notifiées dans le salon dédié.")
    return embed


class ApplicationModal(discord.ui.Modal, title="Ajouter une candidature"):
    company = discord.ui.TextInput(
        label="Entreprise",
        placeholder="Ex : Google, Airbus, BNP Paribas...",
        max_length=100,
    )
    post = discord.ui.TextInput(
        label="Poste / intitulé de l'offre",
        placeholder="Ex : Développeur Python, Data Analyst...",
        max_length=150,
    )

    async def on_submit(self, interaction: discord.Interaction):
        addUserApplication(
            userID=interaction.user.id,
            company=self.company.value,
            post=self.post.value,
        )

        today = datetime.date.today()
        revival = today + datetime.timedelta(config.DAYS_BEFORE_REVIVAL)

        embed = discord.Embed(
            title="Candidature ajoutée",
            description="Ta candidature a bien été enregistrée !",
            color=COLOR_SUCCESS,
        )
        embed.add_field(name="Entreprise", value=self.company.value, inline=True)
        embed.add_field(name="Poste", value=self.post.value, inline=True)
        embed.add_field(name="Date de candidature", value=today.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="Date de relance", value=revival.strftime("%d/%m/%Y"), inline=True)
        embed.set_footer(text="Une notification automatique te sera envoyée à la date de relance.")

        await interaction.response.send_message(embed=embed)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message(
            f"Une erreur s'est produite : `{error}`", ephemeral=True
        )
        

class StatusSelect(discord.ui.Select):
    def __init__(self, user_id: int, applications):
        options = [
            discord.SelectOption(
                label=f"{row[2]} — {row[3]}"[:100],
                description=f"Statut actuel : {_status_display(row[6])} | Postulé le {row[4]}"[:100],
                value=str(row[0]),
            )
            for row in applications
        ]
        super().__init__(
            placeholder="Quelle candidature modifier ?",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Ce menu ne t'appartient pas.", ephemeral=True)
            return

        app_id = int(self.values[0])
        app_label = next(opt.label for opt in self.options if opt.value == self.values[0])

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Changer le statut",
                description=f"Sélectionne le nouveau statut pour **{app_label}** :",
                color=COLOR_INFO,
            ),
            view=NewStatusView(self.user_id, app_id, app_label),
        )


class NewStatusSelect(discord.ui.Select):
    def __init__(self, user_id: int, app_id: int, app_label: str):
        options = [
            discord.SelectOption(label=label, value=key)
            for key, (label, _) in STATUS_LABELS.items()
        ]
        super().__init__(
            placeholder="Nouveau statut",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.user_id  = user_id
        self.app_id   = app_id
        self.app_label = app_label

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Ce menu ne t'appartient pas.", ephemeral=True)
            return

        new_status = self.values[0]
        changeStatus(self.app_id, new_status)

        label, color = STATUS_LABELS.get(new_status, ("Inconnu", COLOR_NEUTRAL))
        embed = discord.Embed(
            title="Statut mis à jour",
            description=f"**{self.app_label}** → {label}",
            color=color,
        )
        await interaction.response.edit_message(embed=embed, view=None)


class NewStatusView(discord.ui.View):
    def __init__(self, user_id: int, app_id: int, app_label: str):
        super().__init__(timeout=60)
        self.add_item(NewStatusSelect(user_id, app_id, app_label))


class DeleteApplicationSelect(discord.ui.Select):
    def __init__(self, user_id: int, applications):
        options = [
            discord.SelectOption(
                label=f"{row[2]} — {row[3]}"[:100],
                description=f"Postulé le {row[4]}"[:100],
                value=str(row[0]),
            )
            for row in applications
        ]
        super().__init__(
            placeholder="Quelle candidature supprimer ?",
            min_values=1,
            max_values=len(options),
            options=options,
        )
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Ce menu ne t'appartient pas.", ephemeral=True)
            return

        deleted = []
        for value in self.values:
            label = next(opt.label for opt in self.options if opt.value == value)
            deleteUserApplication(int(value))
            deleted.append(label)

        embed = discord.Embed(
            title="Candidature(s) supprimée(s)",
            description="\n".join(f"• {l}" for l in deleted),
            color=COLOR_WARNING,
        )
        await interaction.response.edit_message(embed=embed, view=None)


class DeleteApplicationView(discord.ui.View):
    def __init__(self, user_id: int, applications):
        super().__init__(timeout=60)
        self.add_item(DeleteApplicationSelect(user_id, applications))


class ApplicationsMainView(discord.ui.View):
    def __init__(self, user: discord.User):
        super().__init__(timeout=120)
        self.user = user

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

    @discord.ui.button(label="Ajouter", style=discord.ButtonStyle.primary)
    async def btn_add(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("Ce menu ne t'appartient pas.", ephemeral=True)
            return
        await interaction.response.send_modal(ApplicationModal())

    @discord.ui.button(label="Modifier statut", style=discord.ButtonStyle.secondary)
    async def btn_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("Ce menu ne t'appartient pas.", ephemeral=True)
            return

        df = getUserApplications(interaction.user.id)
        applications = df.values.tolist() if df is not None and len(df) > 0 else []

        if not applications:
            await interaction.response.send_message(
                "Tu n'as aucune candidature à modifier.", ephemeral=True
            )
            return

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Modifier le statut",
                description="Sélectionne la candidature à modifier :",
                color=COLOR_INFO,
            ),
            view=_StatusSelectView(interaction.user.id, applications),
        )

    @discord.ui.button(label="Supprimer", style=discord.ButtonStyle.danger)
    async def btn_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("Ce menu ne t'appartient pas.", ephemeral=True)
            return

        df = getUserApplications(interaction.user.id)
        applications = df.values.tolist() if df is not None and len(df) > 0 else []

        if not applications:
            await interaction.response.send_message(
                "Tu n'as aucune candidature à supprimer.", ephemeral=True
            )
            return

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Supprimer des candidatures",
                description="Sélectionne les candidatures à supprimer :",
                color=COLOR_WARNING,
            ),
            view=DeleteApplicationView(interaction.user.id, applications),
        )


class _StatusSelectView(discord.ui.View):
    """Vue intermédiaire pour le select de choix de candidature à modifier."""
    def __init__(self, user_id: int, applications):
        super().__init__(timeout=60)
        self.add_item(StatusSelect(user_id, applications))


class ApplicationsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="candidatures",
        description="Voir et gérer toutes tes candidatures",
    )
    async def candidatures(self, interaction: discord.Interaction):
        df = getUserApplications(interaction.user.id)
        applications = df.values.tolist() if df is not None and len(df) > 0 else []
        embed = _embed_candidatures(interaction.user, applications)

        await interaction.response.send_message(
            embed=embed,
            view=ApplicationsMainView(interaction.user),
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ApplicationsCog(bot))