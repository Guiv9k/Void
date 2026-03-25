import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

DB_PATH = "database/bot_data.db"
MEU_ID = 953432769659301910  # Meu ID, não mexam aqui pelo amor de deus


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="setmoedas", description="[ADMIN] Altera as moedas de um usuário."
    )
    @app_commands.describe(
        membro="Quem vai receber?", valor="Nova quantidade de moedas"
    )
    async def setmoedas(
        self, interaction: discord.Interaction, membro: discord.Member, valor: int
    ):
        await interaction.response.defer(ephemeral=True)

        # Ai dento, se algum frango tentar usar isso aqui sem ser eu, o bot barra.
        # Meu nobre, se for testar com a tua conta dps, coloca teu ID lá em cima provisório.
        if interaction.user.id != MEU_ID:
            await interaction.followup.send(
                "⛔ **ERRO:** Raitumanucu, quem tu acha que é pra mexer no meu cofre? Só o chefe manda aqui, mísera!",
                ephemeral=True,
            )
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE usuarios SET moedas = ? WHERE user_id = ?", (valor, str(membro.id))
        )

        # Meus lindos, presta atenção aqui: se o cara não existir no banco de dados, a gente já insere ele na marra.
        if cursor.rowcount == 0:
            cursor.execute(
                "INSERT INTO usuarios (user_id, moedas) VALUES (?, ?)",
                (str(membro.id), valor),
            )

        conn.commit()
        conn.close()

        await interaction.followup.send(
            f"✅ Feito, meu bem. O saldo de **{membro.display_name}** foi pra `{valor}` moedas. Manda ele ir treinar agora.",
            ephemeral=True,
        )

    @app_commands.command(
        name="setnivel", description="[ADMIN] Altera o nível de um usuário."
    )
    async def setnivel(
        self, interaction: discord.Interaction, membro: discord.Member, nivel: int
    ):
        await interaction.response.defer(ephemeral=True)

        if interaction.user.id != MEU_ID:
            await interaction.followup.send(
                "⛔ Ai dento! Tu não tem moral pra alterar nível de ninguém não, mísera.",
                ephemeral=True,
            )
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE usuarios SET nivel = ?, xp = 0 WHERE user_id = ?",
            (nivel, str(membro.id)),
        )
        conn.commit()
        conn.close()

        await interaction.followup.send(
            f"🔮 Tá lá, meu bem! O nível de **{membro.display_name}** foi injetado pra `{nivel}` na marra!",
            ephemeral=True,
        )

    @app_commands.command(
        name="resetar_usuario",
        description="[ADMIN] Apaga todos os registros de uma alma.",
    )
    async def resetar_usuario(
        self, interaction: discord.Interaction, membro: discord.Member
    ):
        await interaction.response.defer(ephemeral=True)

        if interaction.user.id != MEU_ID:
            await interaction.followup.send(
                "⛔ Tá achando que é o dono do server, mísera? Sai daqui.",
                ephemeral=True,
            )
            return

        # Raitumanucu, esse comando aqui deleta TUDO do cara. Usem com cuidado pow.
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM usuarios WHERE user_id = ?", (str(membro.id),))
        conn.commit()
        conn.close()

        await interaction.followup.send(
            f"♻️ **{membro.display_name}** foi de base. Apagado com sucesso, meu bem.",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(Admin(bot))
