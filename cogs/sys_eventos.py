import discord
from discord.ext import commands
import sqlite3

DB_PATH = "database/bot_data.db"

class Eventos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Pup Minha linda, eu tentei puxar o canal do sistema. Se o corno do dono desativou, o bot tenta achar o "geral" ou "chat" pra não bugar.
        canal = member.guild.system_channel
        if not canal:
            canal = discord.utils.find(lambda c: c.name in ['geral', 'chat', 'chat-geral'] and isinstance(c, discord.TextChannel), member.guild.channels)
        
        if canal:
            # Meus lindos, já registra a alma nova no banco de dados na marra pra ele não escapar do agiota.
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO usuarios (user_id, moedas, nivel, xp) VALUES (?, ?, ?, ?)", (str(member.id), 0, 1, 0))
            conn.commit()
            conn.close()

            embed = discord.Embed(
                title="🌀 OLHA QUEM CAIU NO VÁCUO",
                description=f"**{member.mention}** chegou no servidor.\n\n> Mais um xupeta liso pra ser roubado. Farma tuas moedas e tenta sobreviver, mísera. Aham q lindo me paga um boquete dps de upar pro nível 2!",
                color=0x00FFFF 
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text="Bem-vindo ao hospício.", icon_url=self.bot.user.display_avatar.url)
            await canal.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # Bros, mesma lógica de buscar o canal de saída aqui.
        canal = member.guild.system_channel
        if not canal:
            canal = discord.utils.find(lambda c: c.name in ['geral', 'chat', 'chat-geral'] and isinstance(c, discord.TextChannel), member.guild.channels)
            
        if canal:
            embed = discord.Embed(
                title="💀 UM XUPETA FOI DE BASE",
                description=f"**{member.display_name}** não aguentou o Kid bengala, chorou e quitou do servidor.\n\n> Ai dento, o vácuo consumiu os restos mortais desse frango.",
                color=0xFF0000
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text="Menos um CLT por aqui.", icon_url=self.bot.user.display_avatar.url)
            await canal.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Eventos(bot))