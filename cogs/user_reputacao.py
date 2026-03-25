import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import time

DB_PATH = "database/bot_data.db"


class Reputacao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}
        self.criar_tabelas()

    def criar_tabelas(self):
        # Pup Minha linda, essa linha cria a tabela caso ela não exista. O UNIQUE não deixa o cara ter duas linhas da mesma categoria.
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS reputacao 
                     (user_id TEXT, categoria TEXT, quantidade INTEGER, UNIQUE(user_id, categoria))"""
        )
        conn.commit()
        conn.close()

    @app_commands.command(
        name="rep",
        description="Julgue um xupeta do servidor dando um ponto de reputação pra ele.",
    )
    @app_commands.describe(
        membro="Quem você vai julgar?", categoria="Qual a fama dessa pessoa?"
    )
    @app_commands.choices(
        categoria=[
            # Bros, mudei os nomes pra combinar com o nosso shitpost, mas mantive os values iguais pro comando /perfil não bugar!
            app_commands.Choice(name="🧠 Nerdola (Gênio)", value="genio"),
            app_commands.Choice(name="🌪️ Shitposter Tóxico (Caos)", value="caos"),
            app_commands.Choice(name="🔪 Talarico (Traidor)", value="traidor"),
            app_commands.Choice(name="🤝 Xupeta Bonzinho (Gente Boa)", value="bondade"),
        ]
    )
    async def dar_rep(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        categoria: app_commands.Choice[str],
    ):
        if membro.id == interaction.user.id or membro.bot:
            await interaction.response.send_message(
                "❌ Querendo mamar a si mesmo ou dar rep pro bot? Ai dento, xupeta! Escolhe um alvo de verdade.",
                ephemeral=True,
            )
            return

        # Cooldown de 2 horas para não farmarem reputação infinita
        user_id = interaction.user.id
        tempo_atual = time.time()

        if user_id in self.cooldowns and tempo_atual - self.cooldowns[user_id] < 7200:
            tempo_passado = tempo_atual - self.cooldowns[user_id]
            tempo_restante = 7200 - tempo_passado
            horas = int(tempo_restante // 3600)
            minutos = int((tempo_restante % 3600) // 60)

            # Bros, arrumei a formatação do tempo pra ficar bonitinho em horas e minutos.
            if horas > 0:
                await interaction.response.send_message(
                    f"⏳ Segura a emoção, fiscal de cuheio! Tu só pode julgar alguém de novo em **{horas}h e {minutos}m**.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    f"⏳ Tá emocionado? Tu só pode julgar alguém de novo em **{minutos} minutos**.",
                    ephemeral=True,
                )
            return

        self.cooldowns[user_id] = tempo_atual

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Tenta inserir, se já existir, ele apenas soma +1 (Puro suco do SQLite)
        c.execute(
            """INSERT INTO reputacao (user_id, categoria, quantidade) 
                     VALUES (?, ?, 1) 
                     ON CONFLICT(user_id, categoria) 
                     DO UPDATE SET quantidade = quantidade + 1""",
            (str(membro.id), categoria.value),
        )
        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="⚖️ TRIBUNAL DO AGIOTA",
            description=f"**{interaction.user.mention}** explanou o **{membro.mention}** na roda e marcou o CPF dele como:\n\n> **{categoria.name.upper()}**",
            color=0xFFD700,
        )
        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_footer(
            text="Aham q lindo, me paga um boquete dps desse julgamento.",
            icon_url=self.bot.user.display_avatar.url,
        )
        await interaction.response.send_message(content=membro.mention, embed=embed)


async def setup(bot):
    await bot.add_cog(Reputacao(bot))
