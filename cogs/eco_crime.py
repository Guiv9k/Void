import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import random
import time

DB_PATH = "database/bot_data.db"


class Crime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldown_crime = {}

    @app_commands.command(
        name="crime",
        description="Cometa um delito contra o sistema. Pode dar bom ou tu vai pro Serasa.",
    )
    @app_commands.choices(
        tipo=[
            app_commands.Choice(name="💳 Fraudar o INSS (Risco Baixo)", value="inss"),
            app_commands.Choice(
                name="🚗 Desmanche de Marea (Risco Médio)", value="desmanche"
            ),
            app_commands.Choice(
                name="🏦 Assaltar o Banco Central (Risco Extremo)", value="banco"
            ),
        ]
    )
    async def crime(
        self, interaction: discord.Interaction, tipo: app_commands.Choice[str]
    ):
        user_id = interaction.user.id
        tempo_atual = time.time()

        # Bros, Cooldown de 2 horas (7200 segundos) pra não virar bagunça
        if user_id in self.cooldown_crime:
            tempo_passado = tempo_atual - self.cooldown_crime[user_id]
            if tempo_passado < 7200:
                horas = int((7200 - tempo_passado) // 3600)
                minutos = int(((7200 - tempo_passado) % 3600) // 60)
                return await interaction.response.send_message(
                    f"⏳ A polícia tá na tua cola, xupeta! Fica escondido por **{horas}h e {minutos}m** antes de tentar outra merda.",
                    ephemeral=True,
                )

        # Inicia a transação com o banco
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT moedas, xp FROM usuarios WHERE user_id = ?", (str(user_id),))
        res = c.fetchone()

        if not res:
            conn.close()
            return await interaction.response.send_message(
                "🌀 O vácuo não te reconhece. Mande uma mensagem no chat primeiro.",
                ephemeral=True,
            )

        saldo_atual = res[0]

        # Se o cara já tiver devendo pro Agiota, ele nem consegue cometer crime
        if saldo_atual < -1000:
            conn.close()
            return await interaction.response.send_message(
                "❌ Teu nome já tá sujo demais no Serasa do Vácuo (Saldo menor que -1000). Vai trabalhar, liso, não tem nem como financiar o crime!",
                ephemeral=True,
            )

        self.cooldown_crime[user_id] = tempo_atual
        sucesso = False

        # --- LÓGICA DE RISCO E RECOMPENSA ---
        if tipo.value == "inss":
            # 70% de chance de dar certo. Lucro mixuruca.
            sucesso = random.random() <= 0.70
            lucro = random.randint(200, 400)
            multa = random.randint(300, 500)
            titulo = "💳 FRAUDE NO INSS"
            msg_win = f"Tu fingiu que não tinha uma perna e sacou a aposentadoria da tua avó.\n> 💰 **Lucro:** `{lucro}` moedas."
            msg_lose = f"O perito do INSS viu tu dançando no TikTok e te denunciou.\n> 💀 **Multa:** `{multa}` moedas pro ralo."

        elif tipo.value == "desmanche":
            # 50% de chance. Lucro bom.
            sucesso = random.random() <= 0.50
            lucro = random.randint(600, 1000)
            multa = random.randint(800, 1200)
            titulo = "🚗 DESMANCHE CLANDESTINO"
            msg_win = f"Tu roubou um Marea Turbo, não explodiu e vendeu as peças na OLX.\n> 💰 **Lucro:** `{lucro}` moedas."
            msg_lose = f"O Marea pegou fogo no meio do roubo e tu teve que pagar a viatura do bombeiro.\n> 💀 **Multa:** `{multa}` moedas pro ralo."

        elif tipo.value == "banco":
            # 20% de chance. Lucro ABSURDO.
            sucesso = random.random() <= 0.20
            lucro = random.randint(3000, 6000)
            multa = random.randint(2500, 4000)
            titulo = "🏦 ASSALTO AO BANCO CENTRAL"
            msg_win = f"TÁ O CARA!!! Tu meteu o louco, cavou um túnel e limpou o cofre sem ninguém ver!\n> 💰 **Lucro Absurdo:** `{lucro}` moedas. O Agiota tá orgulhoso!"
            msg_lose = f"Tu é muito burro. Esqueceu de botar a máscara e a câmera pegou a tua cara de CLT liso.\n> 💀 **Multa Pesada:** `{multa}` moedas. Vai ter que vender até a calça pra pagar."

        # --- APLICA O RESULTADO NO BANCO DE DADOS ---
        if sucesso:
            xp_ganho = random.randint(15, 30)  # Ganha um XPzinho de brinde
            c.execute(
                "UPDATE usuarios SET moedas = moedas + ?, xp = xp + ? WHERE user_id = ?",
                (lucro, xp_ganho, str(user_id)),
            )
            embed = discord.Embed(title=titulo, description=msg_win, color=0x00FF00)
            embed.set_footer(
                text=f"Aham q lindo me paga um boquete dps de lucrar. (+{xp_ganho} XP)"
            )
        else:
            c.execute(
                "UPDATE usuarios SET moedas = moedas - ? WHERE user_id = ?",
                (multa, str(user_id)),
            )
            embed = discord.Embed(title=titulo, description=msg_lose, color=0xFF0000)
            embed.set_footer(text="Nome sujo no Serasa. Raitumanucu.")

        conn.commit()
        conn.close()

        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Crime(bot))
