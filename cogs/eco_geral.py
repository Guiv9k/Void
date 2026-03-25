import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import random
import time

DB_PATH = "database/bot_data.db"

# --- MINI-JOGO DO DAILY (CAIXAS MISTERIOSAS) ---
class DailyView(discord.ui.View):
    def __init__(self, bot, autor):
        super().__init__(timeout=30)
        self.bot = bot
        self.autor = autor
        self.clicado = False

        # Meus lindos, agora é o puro suco do RNG. Cada caixa recebe um número aleatório de 10 a 300.
        # Pode vir 3 caixas de 10 moedas se o vácuo odiar vocês kkkkkkk.
        self.premios = [
            random.randint(10, 300),
            random.randint(10, 300),
            random.randint(10, 300),
        ]
        random.shuffle(self.premios)

    async def abrir_caixa(
        self, interaction: discord.Interaction, indice: int, num_caixa: int
    ):
        if interaction.user.id != self.autor.id:
            await interaction.response.send_message(
                "❌ Sai daqui xupeta, essa caixa não é tua! Ai dento.", ephemeral=True
            )
            return

        if self.clicado:
            return
        self.clicado = True

        for item in self.children:
            item.disabled = True

        premio_ganho = self.premios[indice]

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "UPDATE usuarios SET moedas = moedas + ? WHERE user_id = ?",
            (premio_ganho, str(self.autor.id)),
        )
        conn.commit()
        conn.close()

        embed = discord.Embed(title="🎁 DAILY RESGATADO", color=0x2B2D31)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        # Meus lindos, os xingamentos agora são baseados em quanto ele tirou de 10 a 300.
        if premio_ganho >= 200:
            embed.color = 0xFFD700
            mensagem = "**CAGADO DEMAIS! FORROU O BOLSO!**"
        elif premio_ganho >= 80:
            embed.color = 0x00FF00
            mensagem = "**TÁ BOM PRA COMPRAR UM PÃO, SEU LISO!**"
        else:
            embed.color = 0xFF0000
            mensagem = "**AI DENTO, SÓ PEGOU MOEDA DE TROCO... XUPETA!**"

        embed.description = f"{mensagem}\n\n> Tu abriu a **Caixa {num_caixa}** e a sorte te deu `{premio_ganho}` moedas.\n\n*Raitumanucu, volta amanhã pra tentar de novo, gatinha.*"

        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    @discord.ui.button(label="Caixa 1", style=discord.ButtonStyle.primary, emoji="📦")
    async def caixa1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.abrir_caixa(interaction, 0, 1)

    @discord.ui.button(label="Caixa 2", style=discord.ButtonStyle.primary, emoji="📦")
    async def caixa2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.abrir_caixa(interaction, 1, 2)

    @discord.ui.button(label="Caixa 3", style=discord.ButtonStyle.primary, emoji="📦")
    async def caixa3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.abrir_caixa(interaction, 2, 3)

    async def on_timeout(self):
        if not self.clicado:
            for item in self.children:
                item.disabled = True
            embed = discord.Embed(
                title="⏳ TEMPO ESGOTADO",
                description="Ficou moscando e o Vácuo engoliu tudo. Ficou sem nada hoje, liso.",
                color=0x2B2D31,
            )
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            await self.message.edit(embed=embed, view=self)


# --- MINI-JOGO DO TRABALHO (DESCRIPTOGRAFIA) ---
class TrabalhoBotao(discord.ui.Button):
    def __init__(self, label, view_obj):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.view_obj = view_obj

    async def callback(self, interaction: discord.Interaction):
        await self.view_obj.processar_trabalho(interaction, self.label)


class TrabalharView(discord.ui.View):
    def __init__(self, bot, autor, palavra_certa, recompensa):
        super().__init__(timeout=20)
        self.bot = bot
        self.autor = autor
        self.palavra_certa = palavra_certa
        self.recompensa = recompensa
        self.clicado = False

    async def processar_trabalho(self, interaction: discord.Interaction, escolha: str):
        if interaction.user.id != self.autor.id:
            await interaction.response.send_message(
                "❌ Vai caçar tua própria CLT, mísera!", ephemeral=True
            )
            return

        if self.clicado:
            return
        self.clicado = True

        for item in self.children:
            item.disabled = True

        embed = discord.Embed(title="💼 FIM DO EXPEDIENTE", color=0x2B2D31)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        if escolha == self.palavra_certa:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                "UPDATE usuarios SET moedas = moedas + ? WHERE user_id = ?",
                (self.recompensa, str(self.autor.id)),
            )
            conn.commit()
            conn.close()

            embed.description = f"**Boa, até que não é tão inútil!**\n\n> Hackeou o bagulho direitinho.\n> 💰 Pagamento: `{self.recompensa}` conto na conta. Aham q lindo me paga um boquete dps do expediente!"
            embed.color = 0x00FF00
        else:
            embed.description = f"**Foi de base, CLT!**\n\n> Tu digitou igual um xupeta e bloqueou o sistema inteiro.\n> 💀 Zero moedas pra ti. A palavra certa era **{self.palavra_certa}**."
            embed.color = 0xFF0000

        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    async def on_timeout(self):
        if not self.clicado:
            for item in self.children:
                item.disabled = True
            embed = discord.Embed(
                title="⏳ TEMPO ESGOTADO",
                description="Dormiu no ponto, liso! Foi demitido por justa causa e perdeu a grana.",
                color=0x2B2D31,
            )
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            await self.message.edit(embed=embed, view=self)


# --- CLASSE PRINCIPAL ---
class Economia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldown_chat = {}
        self.cooldown_daily = {}
        self.cooldown_trabalho = {}

    # --- 1. XP AUTOMÁTICO NO CHAT ---
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return

        user_id = message.author.id
        tempo_atual = time.time()

        if (user_id in self.cooldown_chat and tempo_atual - self.cooldown_chat[user_id] < 60):
            return
        self.cooldown_chat[user_id] = tempo_atual

        # Seus valores originais de ganho
        xp_ganho = random.randint(5, 12)
        moedas_ganhas = random.randint(1, 4)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 🔥 A PEÇA QUE FALTAVA: Criar o liso se ele não estiver no banco
        cursor.execute("INSERT OR IGNORE INTO usuarios (user_id, xp, nivel, moedas) VALUES (?, 0, 1, 0)", (str(user_id),))

        # Puxa os dados (XP, Nível e Conjuge pro seu bônus de 15%)
        cursor.execute("SELECT xp, nivel, conjuge FROM usuarios WHERE user_id = ?", (str(user_id),))
        res = cursor.fetchone()

        if res:
            xp_atual, nivel_atual, conjuge = res
            
            # 🔥 REGRA DO PATRÃO: 15% de XP a mais (1.15) se for casado
            if conjuge and conjuge != "Solteirão Liso":
                xp_ganho = int(xp_ganho * 1.15)

            novo_xp = xp_atual + xp_ganho
            novo_nivel = nivel_atual
            upou = False

            # 🔥 REGRA DO PATRÃO: 1000 XP FIXO
            while novo_xp >= 1000:
                novo_xp -= 1000
                novo_nivel += 1
                upou = True

            cursor.execute(
                "UPDATE usuarios SET xp = ?, nivel = ?, moedas = moedas + ? WHERE user_id = ?",
                (novo_xp, novo_nivel, moedas_ganhas, str(user_id)),
            )
            conn.commit()

            if upou:
                await message.channel.send(
                    f"📈 **MILAGRE!** {message.author.mention} upou pro **Nível {novo_nivel}**! Literalmente deixou de ser um liso."
                )
        
        conn.close()

    # --- 2. COMANDO DE TRABALHO ---
    @app_commands.command(
        name="trabalhar",
        description="Presta um serviço de hacker e ganha umas moedas (Cooldown de 4h).",
    )
    async def trabalhar(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        tempo_atual = time.time()

        # Bros, botei 4 HORAS (14400 segundos) de cooldown pra esses xupetas pararem de farmar fácil.
        if user_id in self.cooldown_trabalho:
            tempo_passado = tempo_atual - self.cooldown_trabalho[user_id]
            if tempo_passado < 14400:
                horas_restantes = int((14400 - tempo_passado) // 3600)
                minutos_restantes = int(((14400 - tempo_passado) % 3600) // 60)
                await interaction.response.send_message(
                    f"⏳ Ai dento! A carga horária acabou. Volta daqui a **{horas_restantes}h e {minutos_restantes}m**, CLT!",
                    ephemeral=True,
                )
                return

        self.cooldown_trabalho[user_id] = tempo_atual

        recompensa = random.randint(80, 150)

        palavras = [
            "VACUO",
            "XUPETA",
            "MISERA",
            "SHITPOST",
            "MACACO",
            "AGIOTA",
            "CALVO",
            "DEBOCHE",
            "HACKER",
            "SISTEMA",
        ]
        palavra_certa = random.choice(palavras)

        lista_letras = list(palavra_certa)
        random.shuffle(lista_letras)
        palavra_embaralhada = "".join(lista_letras)

        while palavra_embaralhada == palavra_certa:
            random.shuffle(lista_letras)
            palavra_embaralhada = "".join(lista_letras)

        outras = [p for p in palavras if p != palavra_certa]
        errada1 = random.choice(outras)
        outras.remove(errada1)
        errada2 = random.choice(outras)

        opcoes = [palavra_certa, errada1, errada2]
        random.shuffle(opcoes)

        embed_inicio = discord.Embed(
            title="💻 BORA TRABALHAR, CLT",
            description=f"O agiota tá cobrando. Descobre qual é a palavra real pra hackear o sistema!\n\n> 🔐 Código Embaralhado: **`{palavra_embaralhada}`**\n> ⏳ Tempo: 20 segundos.",
            color=0xFFD700,
        )
        embed_inicio.set_thumbnail(url=self.bot.user.display_avatar.url)

        view = TrabalharView(self.bot, interaction.user, palavra_certa, recompensa)
        for op in opcoes:
            view.add_item(TrabalhoBotao(label=op, view_obj=view))

        await interaction.response.send_message(embed=embed_inicio, view=view)
        view.message = await interaction.original_response()

    # --- 3. BÓNUS DIÁRIO INTERATIVO ---
    @app_commands.command(
        name="daily", description="Pega tua esmola diária pra não passar fome."
    )
    async def daily(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        tempo_atual = time.time()

        if user_id in self.cooldown_daily:
            tempo_passado = tempo_atual - self.cooldown_daily[user_id]
            tempo_restante = 86400 - tempo_passado
            if tempo_restante > 0:
                horas = int(tempo_restante // 3600)
                minutos = int((tempo_restante % 3600) // 60)
                await interaction.response.send_message(
                    f"⏳ Ai dento! Quer farmar infinito, mísera? A esmola só libera daqui a **{horas}h e {minutos}m**. Vai caçar o que fazer!",
                    ephemeral=True,
                )
                return

        self.cooldown_daily[user_id] = tempo_atual

        embed_inicio = discord.Embed(
            title="📦 A CAIXA SURPRESA",
            description="Tem 3 caixas aqui, e é roleta russa pura. O Vácuo colocou um valor aleatório de 10 a 300 moedas em CADA UMA.\n\n> Qual tu vai abrir, meu bem?",
            color=0x2B2D31,
        )
        embed_inicio.set_thumbnail(url=self.bot.user.display_avatar.url)

        view = DailyView(self.bot, interaction.user)

        await interaction.response.send_message(embed=embed_inicio, view=view)
        view.message = await interaction.original_response()


async def setup(bot):
    await bot.add_cog(Economia(bot))
