import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import random
import asyncio

DB_PATH = "database/bot_data.db"


class Brazzino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.apostas_ativas = {}
        self.rodada_aberta = False

    @app_commands.command(
        name="brazzino",
        description="Inicia uma rodada de apostas coletivas no servidor!",
    )
    async def brazzino(self, interaction: discord.Interaction):
        if self.rodada_aberta:
            await interaction.response.send_message(
                "⚠️ Calma aí, monstro! Já tem um Brazzino rodando. Segura a emoção aí, mísera!",
                ephemeral=True,
            )
            return

        self.rodada_aberta = True
        self.apostas_ativas = {}

        embed = discord.Embed(
            title="🎰 BRAZZINO 777: O CASSINO DOS MAROMBAS",
            description=(
                "📢 **A BOCA TÁ ABERTA, PORRA!**\n\n"
                "Vocês têm **60 segundos** pra jogar o dinheiro na mesa.\n"
                "Use `/apostar_brazzino` antes que eu feche essa bodega.\n\n"
                "💰 **Prêmio:** 5x o valor apostado se tiver a moral de acertar o número de 1 a 10!"
            ),
            color=0xFFD700,
        )
        embed.set_thumbnail(url="https://i.imgur.com/vHpxLid.png")
        embed.set_footer(text="Bora, xupetas, façam suas apostas...")

        await interaction.response.send_message(embed=embed)

        # Deixa os xupeta apostarem por 60 segundos. meus lindos, não mexe nesse sleep dps, deixa 60 msm.
        await asyncio.sleep(60)

        if not self.apostas_ativas:
            self.rodada_aberta = False
            await interaction.channel.send(
                "🌑 Ai dento! Bando de xupeta medroso, ninguém apostou. Fechei a banca, vão treinar!"
            )
            return

        # Sorteio animado só pra dar emoção na rapaziada.
        sorteio_msg = await interaction.channel.send("🎲 **Girando essa bagaça...**")
        await asyncio.sleep(2)

        numero_sorteado = random.randint(1, 10)
        await sorteio_msg.edit(
            content=f"🎰 E a parada parou no: **{numero_sorteado}**! Raitumanucu, quem acertou?"
        )

        ganhadores = []
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Checa quem acertou a mísera do número.
        for u_id, dados in self.apostas_ativas.items():
            valor, num_escolhido = dados
            if num_escolhido == numero_sorteado:
                premio = valor * 5
                cursor.execute(
                    "UPDATE usuarios SET moedas = moedas + ? WHERE user_id = ?",
                    (premio, str(u_id)),
                )
                ganhadores.append(f"<@{u_id}> (Forrou `{premio}` moedas)")

        conn.commit()
        conn.close()

        if ganhadores:
            resultado = "\n".join(ganhadores)
            embed_win = discord.Embed(
                title="🏆 OS MONSTROS QUE FORRARAM",
                description=resultado,
                color=0x00FF00,
            )
            await interaction.channel.send(embed=embed_win)
        else:
            await interaction.channel.send(
                "💀 Ai dento! Todo mundo perdeu tudo, bando de xupeta! O Vácuo agradece o patrocínio. Vão chorar no supino!"
            )

        self.rodada_aberta = False

    @app_commands.command(
        name="apostar_brazzino",
        description="Coloque suas moedas na rodada atual do Brazzino.",
    )
    @app_commands.describe(
        valor="Quanto quer apostar?", numero="Escolha um número de 1 a 10"
    )
    async def apostar_brazzino(
        self, interaction: discord.Interaction, valor: int, numero: int
    ):
        if not self.rodada_aberta:
            await interaction.response.send_message(
                "❌ Tá cego, parceiro? A banca tá fechada agora. Fica esperto pra próxima.",
                ephemeral=True,
            )
            return
        if valor <= 0 or not (1 <= numero <= 10):
            await interaction.response.send_message(
                "❌ Tá apostando fofo, mísera? Bota um valor de verdade e escolhe um número de 1 a 10!",
                ephemeral=True,
            )
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT moedas FROM usuarios WHERE user_id = ?", (str(interaction.user.id),)
        )
        res = cursor.fetchone()

        if not res or res[0] < valor:
            await interaction.response.send_message(
                "❌ Tu tá liso, parceiro! Vai arrumar uns bicos ou fazer um roubo antes de vir no cassino.",
                ephemeral=True,
            )
            conn.close()
            return

        # Já deduz o valor da aposta na hora pro maluco não dar calote.
        cursor.execute(
            "UPDATE usuarios SET moedas = moedas - ? WHERE user_id = ?",
            (valor, str(interaction.user.id)),
        )
        conn.commit()
        conn.close()

        self.apostas_ativas[interaction.user.id] = [valor, numero]
        await interaction.response.send_message(
            f"✅ Tá lá, meu nobre! Apostou `{valor}` conto no número `{numero}`. Se perder não vem chorar, aham q lindo me paga um boquete dps do treino!",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(Brazzino(bot))
