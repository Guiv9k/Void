import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import re

DB_PATH = "database/bot_data.db"

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.preparar_banco()

    def preparar_banco(self):
        # Pup Minha linda, tirei o CREATE TABLE do on_message e botei aqui pra ele não ficar 
        # forçando o banco de dados a cada mensagem que vocês mandam. Otimização pura!
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS stats (user_id TEXT, palavra TEXT, data TEXT)")
        conn.commit()
        conn.close()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        
        # Bros, botei umas palavras chatas aqui pra ele ignorar. 
        # Assim o ranking mostra as gírias de vcs e não palavras como "você", "para", "como".
        palavras_ignoradas = {"para", "como", "mais", "isso", "esse", "aqui", "muito", "você", "quem", "quando", "onde", "qual", "pelo", "pela", "tava", "fazer", "acho", "tudo", "nada", "esta", "está"}

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Limpa o texto e salva as palavras
        palavras = re.findall(r'\w+', message.content.lower())
        for p in palavras:
            if len(p) > 3 and p not in palavras_ignoradas: 
                cursor.execute("INSERT INTO stats VALUES (?, ?, ?)", 
                               (str(message.author.id), p, str(message.created_at.date())))
        
        conn.commit()
        conn.close()

    @app_commands.command(name="analise", description="O Vácuo puxa a capivara e faz o exame toxicológico do chat.")
    async def analise(self, interaction: discord.Interaction):
        await interaction.response.defer()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Bros, A MÁGICA TÁ AQUI! 
        # Em vez de puxar tudo pra RAM e contar no Python, eu mando o SQLite contar e me dar só o Top 5. O bot fica liso liso!
        cursor.execute("SELECT palavra, COUNT(palavra) as qtd FROM stats GROUP BY palavra ORDER BY qtd DESC LIMIT 5")
        comuns = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM stats")
        total_palavras = cursor.fetchone()[0]
        
        if not comuns or total_palavras == 0:
            await interaction.followup.send("🌑 O vácuo tá limpo. Ninguém falou merda suficiente ainda.", ephemeral=True)
            conn.close()
            return

        palavras_texto = "\n".join([f"> 🗣️ **{p.upper()}**: falada `{c}` vezes" for p, c in comuns])

        # DNA do Shitpost baseado em volume de mensagens
        caos = (total_palavras % 100)
        # Se o caos for menor que 50, a gente inverte pra dar a sensação de que o servidor é maluco mesmo
        if caos < 50: caos += 40 
        intelecto = 100 - caos

        embed = discord.Embed(
            title="🧪 EXAME TOXICOLÓGICO DO CHAT", 
            description="O Vácuo analisou a mente podre de vocês e o resultado é preocupante.\n" + "━"*25,
            color=0x2F3136
        )
        embed.add_field(name="💩 As merdas mais ecoadas aqui:", value=palavras_texto, inline=False)
        embed.add_field(name="📊 Laudo Psiquiátrico", value=f"> 🌪️ **Nível de Shitpost/Caos:** `{caos}%`\n> 🧠 **QI Sobrevivente:** `{intelecto}%`", inline=False)
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else self.bot.user.display_avatar.url)
        embed.set_footer(text="A Entidade recomenda terapia coletiva pra vocês.")
        
        await interaction.followup.send(embed=embed)
        conn.close()

async def setup(bot):
    await bot.add_cog(Stats(bot))