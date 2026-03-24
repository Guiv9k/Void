import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import random

DB_PATH = "database/bot_data.db"

class Recompensas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    grupo = app_commands.Group(name="encomenda", description="Mercado de matadores de aluguel.")

    @grupo.command(name="colocar", description="Bote a cabeça de um xupeta a prêmio.")
    async def colocar_recompensa(self, interaction: discord.Interaction, alvo: discord.Member, valor: int):
        if alvo.id == interaction.user.id or alvo.bot:
            return await interaction.response.send_message("❌ Tu quer botar tua própria cabeça a prêmio? Deixa de ser doente.", ephemeral=True)
            
        if valor < 1000:
            return await interaction.response.send_message("❌ O Agiota não suja a mão por menos de 1.000 moedas.", ephemeral=True)

        user_id = str(interaction.user.id)
        alvo_id = str(alvo.id)
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("SELECT moedas FROM usuarios WHERE user_id = ?", (user_id,))
        res = c.fetchone()
        
        if not res or res[0] < valor:
            conn.close()
            return await interaction.response.send_message(f"💀 Tu não tem `{valor}` moedas pra pagar o contrato, liso.", ephemeral=True)

        # Cobra o dinheiro e joga no mural
        c.execute("UPDATE usuarios SET moedas = moedas - ? WHERE user_id = ?", (valor, user_id))
        
        # Se o cara já tiver uma recompensa, soma o valor novo!
        c.execute('''INSERT INTO recompensas (alvo_id, contratante_id, valor) 
                     VALUES (?, ?, ?) 
                     ON CONFLICT(alvo_id) 
                     DO UPDATE SET valor = valor + ?, contratante_id = ?''', 
                  (alvo_id, user_id, valor, valor, user_id))
        
        conn.commit()
        conn.close()

        # Gui, avisa o teu nobre que isso aqui vai dar briga de verdade no servidor!
        embed = discord.Embed(
            title="🎯 CONTRATO DE MORTE ASSINADO",
            description=f"**{interaction.user.mention}** pagou o Agiota pra colocar a cabeça de **{alvo.mention}** a prêmio!\n\n> 💰 **Recompensa:** `{valor:,}` moedas.\n> Quem abater esse verme primeiro leva a grana.",
            color=0x8B0000
        )
        embed.set_thumbnail(url=alvo.display_avatar.url)
        await interaction.response.send_message(content=alvo.mention, embed=embed)

    @grupo.command(name="cacar", description="Tente abater um procurado e levar a grana do mural.")
    async def cacar_alvo(self, interaction: discord.Interaction, alvo: discord.Member):
        if alvo.id == interaction.user.id:
            return await interaction.response.send_message("❌ Vai se matar?", ephemeral=True)

        user_id = str(interaction.user.id)
        alvo_id = str(alvo.id)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Verifica se o alvo tá procurado
        c.execute("SELECT valor FROM recompensas WHERE alvo_id = ?", (alvo_id,))
        res_recompensa = c.fetchone()
        
        if not res_recompensa:
            conn.close()
            return await interaction.response.send_message("🌀 Esse cara não tem recompensa na cabeça. Tá matando de graça por quê?", ephemeral=True)

        valor_premio = res_recompensa[0]
        
        # Mecânica de Risco: 50% de chance de matar, 50% de tomar um tiro de volta
        sucesso = random.choice([True, False])
        
        if sucesso:
            # Matou o alvo e pegou a grana
            c.execute("UPDATE usuarios SET moedas = moedas + ? WHERE user_id = ?", (valor_premio, user_id))
            c.execute("DELETE FROM recompensas WHERE alvo_id = ?", (alvo_id,))
            
            # Tira um pouco do XP do alvo como punição por ter sido morto
            c.execute("UPDATE usuarios SET xp = MAX(0, xp - 200) WHERE user_id = ?", (alvo_id,))
            
            embed = discord.Embed(
                title="🔫 ABATE CONFIRMADO",
                description=f"**{interaction.user.mention}** meteu bala no **{alvo.mention}** e cobrou a recompensa!\n\n> 💰 **Faturou:** `{valor_premio:,}` moedas.\n> O nome do alvo saiu do Serasa dos Mercenários.",
                color=0x00FF00
            )
        else:
            # Tomou um tiro do alvo e perdeu dinheiro pro hospital
            prejuizo = int(valor_premio * 0.10) # Perde 10% do valor do prêmio como taxa médica
            c.execute("UPDATE usuarios SET moedas = moedas - ? WHERE user_id = ?", (prejuizo, user_id))
            
            embed = discord.Embed(
                title="🚑 FOI DE BERÇO",
                description=f"**{interaction.user.mention}** tentou matar o **{alvo.mention}**, mas tomou uma paulada na nuca e foi parar no hospital.\n\n> 💀 **Prejuízo Médico:** `{prejuizo:,}` moedas.\n> O alvo continua vivo e com a cabeça a prêmio.",
                color=0xFF0000
            )

        conn.commit()
        conn.close()
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Recompensas(bot))