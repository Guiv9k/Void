import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import datetime

DB_PATH = "database/bot_data.db"

class LojaMenu(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=60)
        self.bot = bot

    # Bros, troquei os nomes dos itens pra ficar no puro suco da putaria
    @discord.ui.select(
        placeholder="Escolhe logo a tua muamba...",
        options=[
            discord.SelectOption(label="🛡️ VPN do Agiota (Escudo)", description="Ninguém consegue te roubar por 24h", value="buy_escudo", emoji="🛡️"),
            discord.SelectOption(label="🧠 Curso de Coach Financeiro", description="[EM BREVE] Aumenta o limite de XP", value="coming_1", emoji="🧠"),
            discord.SelectOption(label="🌑 RG Falso", description="[EM BREVE] Fique invisível no Ranking", value="coming_2", emoji="🌑"),
            discord.SelectOption(label="💎 VIP do Cabaré", description="[EM BREVE] Acesso a comandos VIP", value="coming_3", emoji="💎"),
        ]
    )
    async def shop_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        # bros, se o cara tentar comprar item que não lançou, o bot já barra na hora.
        if "coming" in select.values[0]:
            await interaction.response.send_message("🌀 Calma aí mísera, o fornecedor ainda não entregou essa muamba no porto. Aguarde.", ephemeral=True)
            return

        if select.values[0] == "buy_escudo":
            preco = 1500
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT moedas FROM usuarios WHERE user_id = ?", (str(interaction.user.id),))
            res = cursor.fetchone()

            if not res or res[0] < preco:
                await interaction.response.send_message("❌ Tu é liso, xupeta! Volta quando tiver as `1.500` moedas de verdade.", ephemeral=True)
            else:
                expira = (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat()
                cursor.execute("UPDATE usuarios SET moedas = moedas - ?, escudo_ate = ? WHERE user_id = ?", 
                               (preco, expira, str(interaction.user.id)))
                conn.commit()
                await interaction.response.send_message("🛡️ **VPN do Agiota Ativada!** Tá blindado contra roubo por 24 horas. Aham q lindo me paga um boquete dps de ligar o escudo!", ephemeral=True)
            conn.close()

class Loja(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.garantir_colunas() # Meu nobre, isso aqui impede o bot de dar erro se a coluna escudo_ate não existir no banco

    def garantir_colunas(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute("ALTER TABLE usuarios ADD COLUMN escudo_ate TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass # Se a coluna já existir, ele só ignora e segue a vida
        conn.close()

    @app_commands.command(name="loja", description="Abre o camelô clandestino do servidor.")
    async def loja(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🌌 CAMELÔ DO VÁCUO",
            description=(
                "Bem-vindo, CLT. Aqui o teu dinheiro suado compra o que a lei não permite.\n\n"
                "**MUAMBAS NA PRATELEIRA:**\n"
                "🛡️ **VPN do Agiota (Escudo)** - `1.500 moedas`\n"
                "*Protege a tua conta de ser roubada pelos xupetas por 1 dia inteiro.*\n\n"
                "✨ *Outras porcarias chegarão no próximo carregamento...*"
            ),
            color=0x2b2d31
        )
        embed.set_author(name=f"Vendedor: {self.bot.user.name}", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Abre a carteira e escolhe logo no menu abaixo.")
        
        await interaction.response.send_message(embed=embed, view=LojaMenu(self.bot))

async def setup(bot):
    await bot.add_cog(Loja(bot))