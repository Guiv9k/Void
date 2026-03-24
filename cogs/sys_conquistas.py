import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

DB_PATH = "database/bot_data.db"

class Conquistas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.criar_tabela()

    def criar_tabela(self):
        # Tabela pra guardar os troféus. Minha linda, esse UNIQUE impede de duplicar conquista.
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS conquistas 
                     (user_id TEXT, conquista TEXT, UNIQUE(user_id, conquista))''')
        conn.commit()
        conn.close()

    @app_commands.command(name="conquistas", description="Veja a sua estante de troféus e sincronize os novos.")
    async def conquistas(self, interaction: discord.Interaction, membro: discord.Member = None):
        await interaction.response.defer()
        
        alvo = membro or interaction.user
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # --- VERIFICADOR DE SHAPE (CONQUISTAS) ---
        novos_trofeus = []
        
        # Só verifica as conquistas se o cabra tiver vendo o próprio perfil, pra não bugar o banco pow.
        if alvo.id == interaction.user.id:
            c.execute("SELECT moedas, nivel FROM usuarios WHERE user_id = ?", (str(alvo.id),))
            stats = c.fetchone()
            if stats:
                moedas, nivel = stats
                
                # Regrinhas de conquista. Meus lindos, se quiser adicionar mais dps do treino, é só seguir essa lógica aqui.
                if moedas >= 10000: novos_trofeus.append("👑 Capitalista Safado (10k Moedas)")
                if moedas >= 100000: novos_trofeus.append("🏦 Dono da Porra Toda (100k Moedas)")
                if moedas <= 10: novos_trofeus.append("🗑️ Liso e Frango (Quase 0 Moedas)")
                if nivel >= 5: novos_trofeus.append("🧬 Mutante de Respeito (Nível 5)")
                if nivel >= 15: novos_trofeus.append("🌌 Entidade do Shape Cósmico (Nível 15)")

                # Tenta jogar no banco, se der erro de UNIQUE é pq o xupeta já tem o troféu, aí a gente dá pass. Ai dento, Python é lindo.
                for trofeu in novos_trofeus:
                    try:
                        c.execute("INSERT INTO conquistas (user_id, conquista) VALUES (?, ?)", (str(alvo.id), trofeu))
                    except sqlite3.IntegrityError:
                        pass 
                conn.commit()

        # Busca as conquistas atualizadas
        c.execute("SELECT conquista FROM conquistas WHERE user_id = ?", (str(alvo.id),))
        res = c.fetchall()
        conn.close()

        embed = discord.Embed(title=f"🏆 MURAL DE CONQUISTAS: {alvo.display_name.upper()}", color=0xFFD700)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        if not res:
            embed.description = (
                "> Esta alma ainda não conquistou nada, mísera.\n"
                "> Um completo inútil que não aguenta um supino de 10kg."
            )
            embed.color = 0x2b2d31
        else:
            texto = ""
            for r in res:
                texto += f"> 🎖️ **{r[0]}**\n"
            embed.description = f"**Troféus que esse xupeta desbloqueou:**\n\n{texto}"

        embed.set_footer(text="O Vácuo tá de olho no teu progresso. Vai treinar, meu bem.", icon_url=self.bot.user.display_avatar.url)
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Conquistas(bot))