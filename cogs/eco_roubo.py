import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import random
import time
import datetime

DB_PATH = "database/bot_data.db"


# --- MINI-GAME DE DESARMAR O ALARME ---
class RouboView(discord.ui.View):
    def __init__(self, bot, autor, vitima, fio_certo):
        super().__init__(timeout=30)
        self.bot = bot
        self.autor = autor
        self.vitima = vitima
        self.fio_certo = fio_certo
        self.clicado = False

    async def processar_roubo(
        self, interaction: discord.Interaction, cor_escolhida: str
    ):
        if interaction.user.id != self.autor.id:
            await interaction.response.send_message(
                "❌ Sai pra lá xupeta, o roubo não é teu!", ephemeral=True
            )
            return

        if self.clicado:
            return
        self.clicado = True

        for item in self.children:
            item.disabled = True

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT moedas FROM usuarios WHERE user_id = ?", (str(self.vitima.id),)
        )
        saldo_vitima = cursor.fetchone()[0]

        embed = discord.Embed(title="🕵️ RESULTADO DA INVASÃO", color=0x2B2D31)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        if cor_escolhida == self.fio_certo:
            porcentagem = random.uniform(0.10, 0.30)
            valor_roubado = int(saldo_vitima * porcentagem)

            cursor.execute(
                "UPDATE usuarios SET moedas = moedas + ? WHERE user_id = ?",
                (valor_roubado, str(self.autor.id)),
            )
            cursor.execute(
                "UPDATE usuarios SET moedas = moedas - ? WHERE user_id = ?",
                (valor_roubado, str(self.vitima.id)),
            )

            embed.description = f"**O ALARME FOI DESATIVADO!**\n\n> Tu teve a frieza de cortar o fio **{cor_escolhida.upper()}** e limpou o cofre do {self.vitima.mention}.\n> 💰 Lucro: `{valor_roubado:,}` moedas roubadas. Aham q lindo, me paga um boquete dps desse assalto!"
            embed.color = 0x00FF00
        else:
            multa = random.randint(150, 300)
            cursor.execute(
                "UPDATE usuarios SET moedas = moedas - ? WHERE user_id = ?",
                (multa, str(self.autor.id)),
            )

            embed.description = f"**BEEEP! BEEEP! DEU RUIM MÍSERA!**\n\n> Tu cortou o fio **{cor_escolhida.upper()}**, o alarme disparou e o Agiota te pegou no pulo.\n> 💀 Tomou uma multa de `{multa:,}` moedas.\n> O fio certo era o **{self.fio_certo.upper()}**. CLT burro!"
            embed.color = 0xFF0000

        conn.commit()
        conn.close()

        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    @discord.ui.button(
        label="FIO VERMELHO", style=discord.ButtonStyle.danger, emoji="🔴"
    )
    async def btn_vermelho(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.processar_roubo(interaction, "vermelho")

    @discord.ui.button(label="FIO AZUL", style=discord.ButtonStyle.primary, emoji="🔵")
    async def btn_azul(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.processar_roubo(interaction, "azul")

    @discord.ui.button(label="FIO VERDE", style=discord.ButtonStyle.success, emoji="🟢")
    async def btn_verde(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.processar_roubo(interaction, "verde")

    async def on_timeout(self):
        if not self.clicado:
            for item in self.children:
                item.disabled = True
            embed = discord.Embed(
                title="🚨 PRESO POR SER LERDO",
                description="Ficou moscando olhando pros fios igual um xupeta e a polícia te pegou.",
                color=0x2B2D31,
            )
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            await self.message.edit(embed=embed, view=self)


class Roubo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldown_roubo = (
            {}
        )  # Meu nobre, esse dicionário controla as 4 horas de espera

    # Pup Minha linda, aqui eu crio a coluna escudo_ate se ela não existir, igual fiz na Loja, pra não crashar nada.
    def garantir_coluna_escudo(self, cursor):
        try:
            cursor.execute("SELECT escudo_ate FROM usuarios LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN escudo_ate TEXT")

    @app_commands.command(
        name="roubar", description="Tente hackear o cofre de um CLT (Cooldown de 4h)."
    )
    async def roubar(self, interaction: discord.Interaction, vitima: discord.Member):
        if vitima.id == interaction.user.id or vitima.bot:
            await interaction.response.send_message(
                "🌀 Tá esquizofrênico? Tenta roubar alguém de verdade, mísera.",
                ephemeral=True,
            )
            return

        user_id = interaction.user.id
        tempo_atual = time.time()

        # Bros, aqui tá o Cooldown de 4 Horas (14400 segundos)
        if user_id in self.cooldown_roubo:
            tempo_passado = tempo_atual - self.cooldown_roubo[user_id]
            if tempo_passado < 14400:
                horas_restantes = int((14400 - tempo_passado) // 3600)
                minutos_restantes = int(((14400 - tempo_passado) % 3600) // 60)
                await interaction.response.send_message(
                    f"⏳ Ai dento! Tu já tá sendo procurado pela polícia. Esconde a cara por **{horas_restantes}h e {minutos_restantes}m** antes de roubar de novo.",
                    ephemeral=True,
                )
                return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        self.garantir_coluna_escudo(cursor)

        cursor.execute(
            "SELECT moedas FROM usuarios WHERE user_id = ?", (str(interaction.user.id),)
        )
        saldo_autor = cursor.fetchone()
        cursor.execute(
            "SELECT moedas, escudo_ate FROM usuarios WHERE user_id = ?",
            (str(vitima.id),),
        )
        dados_vitima = cursor.fetchone()

        if not saldo_autor or saldo_autor[0] < 200:
            await interaction.response.send_message(
                "💀 Tu é liso demais! Precisa de pelo menos 200 moedas pra bancar as ferramentas de invasão.",
                ephemeral=True,
            )
            conn.close()
            return

        if not dados_vitima or dados_vitima[0] < 50:
            await interaction.response.send_message(
                "🌀 O cofre desse frango tá mais vazio que tua geladeira. Procura alguém mais rico.",
                ephemeral=True,
            )
            conn.close()
            return

        # --- VERIFICAÇÃO DA VPN DO AGIOTA (ESCUDO DA LOJA) ---
        if dados_vitima[1]:
            try:
                data_escudo = datetime.datetime.fromisoformat(dados_vitima[1])
                if datetime.datetime.now() < data_escudo:
                    await interaction.response.send_message(
                        f"🛡️ **DEU RUIM!** O {vitima.display_name} tá usando a **VPN do Agiota**. Tuas ferramentas não conseguiram passar. Tenta dps!",
                        ephemeral=True,
                    )
                    # Dá o cooldown pro cara parar de encher o saco
                    self.cooldown_roubo[user_id] = tempo_atual
                    conn.close()
                    return
            except ValueError:
                pass  # Se a data tiver bugada, ignora e deixa o roubo rolar

        conn.close()

        # Só registra o cooldown se o roubo realmente começar
        self.cooldown_roubo[user_id] = tempo_atual

        fio_certo = random.choice(["vermelho", "azul", "verde"])

        embed_inicio = discord.Embed(
            title="🧨 INVASÃO EM ANDAMENTO",
            description=f"Tu invadiu o sistema de {vitima.mention}, mas encontrou um alarme cabuloso!\n\n> **Tu tem 30 segundos.**\n> Qual fio tu corta pra não ir de base?",
            color=0xFFD700,
        )
        embed_inicio.set_thumbnail(url=self.bot.user.display_avatar.url)

        view = RouboView(self.bot, interaction.user, vitima, fio_certo)

        await interaction.response.send_message(embed=embed_inicio, view=view)
        view.message = await interaction.original_response()


async def setup(bot):
    await bot.add_cog(Roubo(bot))
