import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import random

DB_PATH = "database/bot_data.db"


class RoletaView(discord.ui.View):
    def __init__(self, bot, autor, aposta):
        super().__init__(timeout=30)
        self.bot = bot
        self.autor = autor
        self.aposta = aposta
        self.multiplicador = 1.0
        self.cliques_sobrevividos = 0
        self.bala_na_agulha = random.randint(1, 6)  # O tambor tem 6 espaços
        self.posicao_atual = 1

    async def atualizar_banco(self, valor, ganhar=True):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        if ganhar:
            c.execute(
                "UPDATE usuarios SET moedas = moedas + ? WHERE user_id = ?",
                (valor, str(self.autor.id)),
            )
        else:
            c.execute(
                "UPDATE usuarios SET moedas = moedas - ? WHERE user_id = ?",
                (valor, str(self.autor.id)),
            )
        conn.commit()
        conn.close()

    @discord.ui.button(
        label="Puxar Gatilho", style=discord.ButtonStyle.danger, emoji="🔫"
    )
    async def btn_atirar(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.autor.id:
            await interaction.response.send_message(
                "❌ Sai do meio, xupeta! A arma não é tua.", ephemeral=True
            )
            return

        # Verifica se atirou e foi de base
        if self.posicao_atual == self.bala_na_agulha:
            await self.atualizar_banco(self.aposta, ganhar=False)
            for item in self.children:
                item.disabled = True

            embed = discord.Embed(
                title="💥 BANG! CPF CANCELADO",
                description=f"**Tu estourou os próprios miolos e sujou o chat todo de sangue.**\n\n> A bala tava na câmara {self.posicao_atual}.\n> 💀 O Agiota embolsou tuas `{self.aposta:,}` moedas.",
                color=0xFF0000,
            )
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text="Foi de arrasta pra cima. Liso.")
            await interaction.response.edit_message(embed=embed, view=self)
            self.stop()
        else:
            # Sobreviveu! Aumenta o multiplicador
            self.cliques_sobrevividos += 1
            self.posicao_atual += 1

            # Pup Minha linda, aqui tá o multiplicador de lucro. 0.5 significa 50% de lucro a cada clique.
            # Se a galera começar a ficar muito rica, muda esse 0.5 pra 0.2 ou 0.3!
            self.multiplicador += 0.5

            lucro_atual = int(self.aposta * self.multiplicador)

            embed = discord.Embed(
                title="😰 CLIQUE... VAZIA!",
                description=f"O cu trancou, né? Tu sobreviveu à câmara {self.posicao_atual - 1}.\n\n> 💰 **Lucro Acumulado:** `{lucro_atual:,}` moedas.\n> Vai arregar ou vai puxar de novo, mísera?",
                color=0xFFD700,
            )
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="Arregar e Levar a Grana",
        style=discord.ButtonStyle.success,
        emoji="🏃‍♂️",
    )
    async def btn_parar(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.autor.id:
            await interaction.response.send_message(
                "❌ Vai arrumar sua própria grana, intrometido.", ephemeral=True
            )
            return

        if self.cliques_sobrevividos == 0:
            await interaction.response.send_message(
                "❌ Tem que puxar o gatilho pelo menos uma vez, frango covarde! Ai dento.",
                ephemeral=True,
            )
            return

        for item in self.children:
            item.disabled = True
        lucro_final = int(self.aposta * self.multiplicador)

        await self.atualizar_banco(lucro_final, ganhar=True)

        embed = discord.Embed(
            title="🏃‍♂️ ARREGOU COM O DINHEIRO",
            description=f"Tu tremeu na base, abaixou a arma e meteu o pé.\n\n> 💰 **Lucrou:** `{lucro_final:,}` moedas.\n> A bala estava na câmara {self.bala_na_agulha}.",
            color=0x00FF00,
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(
            text="Aham q lindo me paga um boquete dps de lucrar tudo isso."
        )
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()


class Roleta(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="roleta", description="Aposte sua vida e suas moedas. Risco extremo."
    )
    async def roleta(self, interaction: discord.Interaction, aposta: int):
        if aposta <= 0:
            await interaction.response.send_message(
                "❌ Aposta de centavo não rola, xupeta. Coloca um valor de verdade.",
                ephemeral=True,
            )
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT moedas FROM usuarios WHERE user_id = ?", (str(interaction.user.id),)
        )
        res = cursor.fetchone()
        conn.close()

        if not res or res[0] < aposta:
            await interaction.response.send_message(
                "💀 Tu é liso, parceiro! Não tem moedas suficientes pra essa loucura.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="🔫 ROLETA RUSSA DO VÁCUO",
            description=f"**{interaction.user.mention}** pegou o revólver, rodou o tambor e encostou o cano na cabeça.\n\n> **Aposta Inicial:** `{aposta:,}` moedas.\n> Se puxar o gatilho e sobreviver, o prêmio aumenta.\n\nTem coragem de apertar o botão ou vai chorar pra mãe?",
            color=0x2B2D31,
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        view = RoletaView(self.bot, interaction.user, aposta)
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Roleta(bot))
