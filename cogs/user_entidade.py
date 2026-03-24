import discord
from discord.ext import commands
from discord import app_commands
import random
import sqlite3
from datetime import datetime

DB_PATH = "database/bot_data.db"

class Entidade(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.msg_count = 0 
        self.criar_tabelas() 

    def criar_tabelas(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS quotes 
                          (user_id TEXT, frase TEXT, data TEXT)''')
        conn.commit()
        conn.close()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        
        # --- SISTEMA DE RESPOSTA AUTOMÁTICA ---
        conteudo = message.content.lower()
        if "bot lixo" in conteudo:
            await message.reply("Lixo é teu PC movido a lenha, mísera! Raitumanucu.")
            return
        if "void" in conteudo and "?" in conteudo:
            respostas_void = ["Ai dento, me deixa em paz.", "Tá me chamando por quê, xupeta?", "Aham q lindo me paga um boquete dps de me marcar."]
            await message.reply(random.choice(respostas_void))
            return
        
        self.msg_count += 1
        
        # --- SISTEMA DE CONVERSA DO TOXICO ---
        if self.msg_count >= 50:
            self.msg_count = 0
            frases_mood = [
                "👁️ O chat tá mais morto que a vida amorosa de vocês. Pqp.",
                "🌀 Caraca bando de desocupado, 50 mensagens falando abobrinha.",
                "💀 Vão arrumar uma CLT ao invés de ficar floodando o chat, bando de liso.",
                "🌑 Só tem xupeta nesse servidor, ai dento."
            ]
            await message.channel.send(random.choice(frases_mood))

        # --- DETECÇÃO DE INSÔNIA (MADRUGADA) ---
        hora = datetime.now().hour
        if 2 <= hora <= 5:
            if random.random() < 0.10: 
                await message.reply(f"⚠️ **ALERTA DE DESOCUPADO:** {message.author.mention}, vai dormir xupeta! Madrugada é pra quem trampa, liso do caralho.")

    # --- SISTEMA DE PÉROLAS (Antigo) ---
    @app_commands.command(name="perola", description="Eterniza uma pérola (merda) que alguém falou no servidor.")
    @app_commands.describe(membro="Quem soltou a pérola?", frase="A merda que o xupeta falou")
    async def perola(self, interaction: discord.Interaction, membro: discord.Member, frase: str):
        if len(frase) > 500:
            await interaction.response.send_message("❌ Ai dento! Tu quer eternizar a Bíblia? Manda uma frase mais curta, mísera.", ephemeral=True)
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        data_hoje = datetime.now().strftime("%d/%m/%Y")
        cursor.execute("INSERT INTO quotes VALUES (?, ?, ?)", (str(membro.id), frase, data_hoje))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(color=0x2b2d31)
        embed.description = f"**❝ {frase} ❞**\n\n— {membro.mention}, no dia {data_hoje}"
        embed.set_author(name="📜 Pérola Eternizada com Sucesso!")
        embed.set_thumbnail(url=membro.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="flashback", description="Traz uma pérola alheia do passado.")
    async def flashback(self, interaction: discord.Interaction):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM quotes ORDER BY RANDOM() LIMIT 1")
        res = cursor.fetchone()
        conn.close()

        if res:
            user_id, frase, data = res
            membro = interaction.guild.get_member(int(user_id))
            
            nome_display = membro.mention if membro else "<@Desconhecido>"
            foto_url = membro.display_avatar.url if membro else self.bot.user.display_avatar.url

            embed = discord.Embed(color=0xFFD700)
            embed.description = f"**❝ {frase} ❞**\n\n— {nome_display}"
            embed.set_author(name=f"🌀 Flashback do dia {data}")
            embed.set_thumbnail(url=foto_url)
            embed.set_footer(text="A internet nunca esquece. E o Vácuo também não.")
            
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("🌑 O vácuo ainda não tem pérolas salvas. Usem o `/perola` primeiro, bando de liso.")

async def setup(bot):
    await bot.add_cog(Entidade(bot))