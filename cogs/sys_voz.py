import discord
from discord.ext import commands, tasks
from discord import app_commands
import sqlite3
import time
import random

DB_PATH = "database/bot_data.db"

# 📑 SISTEMA DE PAGINAÇÃO (BOTÕES DO RANKING)
class VozPaginacao(discord.ui.View):
    def __init__(self, data, guilda, bot_avatar_url):
        super().__init__(timeout=120)
        self.data = data
        self.guilda = guilda
        self.bot_avatar_url = bot_avatar_url
        self.pagina_atual = 0
        self.itens_por_pagina = 5
        self.total_paginas = max(1, (len(data) - 1) // self.itens_por_pagina + 1)
        self.atualizar_botoes()

    def atualizar_botoes(self):
        self.btn_anterior.disabled = self.pagina_atual == 0
        self.btn_proximo.disabled = self.pagina_atual == self.total_paginas - 1

    def formatar_tempo(self, minutos_totais):
        horas = minutos_totais // 60
        minutos = minutos_totais % 60
        return f"{horas}h {minutos}m" if horas > 0 else f"{minutos}m"

    def criar_embed(self):
        inicio = self.pagina_atual * self.itens_por_pagina
        fim = inicio + self.itens_por_pagina
        itens_pagina = self.data[inicio:fim]

        embed = discord.Embed(
            title="🎙️ RANKING DOS SEM VIDA",
            description="A elite de desocupados que mora na call e não vê a luz do sol.\n** **",
            color=0x00FFFF,
        )
        embed.set_thumbnail(url=self.bot_avatar_url)

        texto_ranking = ""
        for i, user_data in enumerate(itens_pagina):
            user_id, tempo_minutos = int(user_data[0]), user_data[1]
            rank = inicio + i + 1
            membro = self.guilda.get_member(user_id)
            nome = membro.display_name if membro else f"Fugitivo ({user_id})"
            icone = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, "🎧")
            texto_ranking += f"> **{icone} #{rank}** | 👤 **{nome}**\n> ⏳ Tempo: `{self.formatar_tempo(tempo_minutos)}`\n> ───────────────\n"

        embed.add_field(name="Classificação Geral", value=texto_ranking or "O silêncio domina o vácuo.", inline=False)
        embed.set_footer(text=f"Página {self.pagina_atual + 1} de {self.total_paginas}", icon_url=self.bot_avatar_url)
        return embed

    @discord.ui.button(label="◀ Voltar", style=discord.ButtonStyle.secondary)
    async def btn_anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.pagina_atual -= 1
        self.atualizar_botoes()
        await interaction.response.edit_message(embed=self.criar_embed(), view=self)

    @discord.ui.button(label="Avançar ▶", style=discord.ButtonStyle.primary)
    async def btn_proximo(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.pagina_atual += 1
        self.atualizar_botoes()
        await interaction.response.edit_message(embed=self.criar_embed(), view=self)


# 🎙️ CLASSE PRINCIPAL (O MOTOR DE VOZ)
class Voz(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.preparar_banco()
        # 🔥 Inicia o cronômetro automático
        self.atualizar_tempo_real.start()

    def preparar_banco(self):
        conn = sqlite3.connect(DB_PATH)
        try:
            conn.execute("ALTER TABLE usuarios ADD COLUMN tempo_voz INTEGER DEFAULT 0")
            conn.commit()
        except sqlite3.OperationalError:
            pass
        conn.close()

    def cog_unload(self):
        self.atualizar_tempo_real.cancel()

    # 💓 LOOP DE 1 MINUTO: Dá XP e Tempo pra quem está em call
    @tasks.loop(minutes=1.0)
    async def atualizar_tempo_real(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        for guild in self.bot.guilds:
            for channel in guild.voice_channels:
                for member in channel.members:
                    if member.bot or member.voice.self_deaf:
                        continue

                    # Garante que o usuário existe
                    cursor.execute("INSERT OR IGNORE INTO usuarios (user_id, xp, nivel, moedas) VALUES (?, 0, 1, 0)", (str(member.id),))
                    
                    # Puxa dados pro Buff de 15% e Level Up de 1000 XP
                    cursor.execute("SELECT xp, nivel, conjuge FROM usuarios WHERE user_id = ?", (str(member.id),))
                    res = cursor.fetchone()
                    
                    if res:
                        xp_atual, nivel_atual, conjuge = res
                        xp_ganho = 5 # Base
                        
                        # 15% bônus pro gado
                        if conjuge and conjuge != "Solteirão Liso":
                            xp_ganho = int(xp_ganho * 1.15)

                        novo_xp = xp_atual + xp_ganho
                        novo_nivel = nivel_atual
                        
                        # 1000 XP FIXO
                        while novo_xp >= 1000:
                            novo_xp -= 1000
                            novo_nivel += 1

                        cursor.execute(
                            "UPDATE usuarios SET xp = ?, nivel = ?, tempo_voz = tempo_voz + 1 WHERE user_id = ?",
                            (novo_xp, novo_nivel, str(member.id))
                        )
        conn.commit()
        conn.close()

    @app_commands.command(name="ranking_call", description="Ranking dos desocupados em call.")
    async def ranking_call(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT user_id, tempo_voz FROM usuarios WHERE tempo_voz > 0 ORDER BY tempo_voz DESC")
        todos = c.fetchall()
        conn.close()

        if not todos:
            return await interaction.followup.send("🌀 Ninguém registrou tempo ainda. Vão conversar!", ephemeral=True)

        view = VozPaginacao(todos, interaction.guild, self.bot.user.display_avatar.url)
        await interaction.followup.send(embed=view.criar_embed(), view=view)

async def setup(bot):
    await bot.add_cog(Voz(bot))