import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import time
import random

DB_PATH = "database/bot_data.db"
PRECO_MALDICAO = 1000 # Bros, deixei os 1000 conto. Como tá difícil farmar, quem usar isso aqui é magnata.
TEMPO_MALDICAO = 300 # 5 minutos em segundos

class Maldicao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Dicionário na memória RAM para guardar quem está amaldiçoado: {user_id: tempo_que_acaba}
        self.amaldicoados = {}

    @app_commands.command(name="amaldicoar", description="Pague 1000 conto pro agiota infernizar a vida de alguém por 5 min.")
    async def amaldicoar(self, interaction: discord.Interaction, vitima: discord.Member):
        if vitima.id == interaction.user.id or vitima.bot:
            await interaction.response.send_message("❌ Tá querendo jogar praga em si mesmo ou no bot, xupeta? Ai dento, escolhe um alvo de verdade.", ephemeral=True)
            return

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT moedas FROM usuarios WHERE user_id = ?", (str(interaction.user.id),))
        res = c.fetchone()

        if not res or res[0] < PRECO_MALDICAO:
            conn.close()
            await interaction.response.send_message(f"💀 Tu é liso demais pra isso. Custa `{PRECO_MALDICAO}` moedas pra jogar praga em alguém. Vai trampar, CLT!", ephemeral=True)
            return

        # Desconta o dinheiro do magnata que comprou a maldição
        c.execute("UPDATE usuarios SET moedas = moedas - ? WHERE user_id = ?", (PRECO_MALDICAO, str(interaction.user.id)))
        conn.commit()
        conn.close()

        # Marca a vítima no dicionário de maldições
        tempo_fim = time.time() + TEMPO_MALDICAO
        self.amaldicoados[vitima.id] = tempo_fim

        embed = discord.Embed(
            title="🐸 PRAGA LANÇADA COM SUCESSO",
            description=f"**{interaction.user.mention}** abriu a carteira e pagou `{PRECO_MALDICAO}` moedas pro Vácuo.\n\n> A alma de **{vitima.mention}** tá **AMALDIÇOADA** por 5 minutos.\n> Vai chover shitpost e bullying na cabeça desse CLT.",
            color=0x8B0000 
        )
        embed.set_thumbnail(url=vitima.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return

        vitima_id = message.author.id
        tempo_atual = time.time()

        # Verifica se o cara que mandou mensagem está na lista negra
        if vitima_id in self.amaldicoados:
            if tempo_atual > self.amaldicoados[vitima_id]:
                # O tempo acabou, o cara tá livre do agiota
                del self.amaldicoados[vitima_id]
            else:
                # Bros, o cara tá amaldiçoado! O Void vai alugar um triplex na mente dele (50% de chance).
                if random.random() < 0.5:
                    xingamentos = [
                        "Cala a boca, amaldiçoado. Ninguém quer ler as tuas merdas não, mísera.",
                        "Tu não cansa de ser um xupeta passando vergonha não? Raitumanucu.",
                        "Aham q lindo me paga um boquete dps de sair dessa maldição.",
                        "Tua alma foi vendida por 1000 conto na biqueira e tu ainda ousa falar no chat?",
                        "Lá vem o liso amaldiçoado digitar de novo... ai dento.",
                        "Vai upar teu shape e tuas moedas antes de falar comigo, seu frango."
                    ]
                    await message.reply(random.choice(xingamentos))

async def setup(bot):
    await bot.add_cog(Maldicao(bot))