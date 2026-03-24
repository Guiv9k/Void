import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import time

DB_PATH = "database/bot_data.db"

# --- SISTEMA DE PAGINAÇÃO (BOTÕES) ---
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
        if horas > 0:
            return f"{horas}h {minutos}m"
        return f"{minutos}m"

    def criar_embed(self):
        inicio = self.pagina_atual * self.itens_por_pagina
        fim = inicio + self.itens_por_pagina
        itens_pagina = self.data[inicio:fim]

        embed = discord.Embed(
            title="🎙️ RANKING DOS SEM VIDA",
            description="A elite de desocupados que mora na call do servidor e não vê a luz do sol.\n** **",
            color=0x00FFFF 
        )
        embed.set_thumbnail(url=self.bot_avatar_url)

        texto_ranking = ""
        for i, user_data in enumerate(itens_pagina):
            user_id = int(user_data[0])
            tempo_minutos = user_data[1]
            rank = inicio + i + 1

            membro = self.guilda.get_member(user_id)
            nome = membro.display_name if membro else f"Fugitivo ({user_id})"

            icone = "🎧"
            if rank == 1: icone = "🥇"
            elif rank == 2: icone = "🥈"
            elif rank == 3: icone = "🥉"

            tempo_formatado = self.formatar_tempo(tempo_minutos)

            texto_ranking += f"> **{icone} #{rank}** | 👤 **{nome}**\n> ⏳ Tempo em Call: `{tempo_formatado}`\n> ───────────────\n"

        embed.add_field(name="Classificação Geral", value=texto_ranking if texto_ranking else "O silêncio domina o servidor. Ninguém entrou em call.", inline=False)
        embed.set_footer(text=f"Página {self.pagina_atual + 1} de {self.total_paginas} • O Vácuo escuta suas fofocas.", icon_url=self.bot_avatar_url)
        return embed

    @discord.ui.button(label="◀ Voltar", style=discord.ButtonStyle.secondary, custom_id="prev")
    async def btn_anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.pagina_atual -= 1
        self.atualizar_botoes()
        await interaction.response.edit_message(embed=self.criar_embed(), view=self)

    @discord.ui.button(label="Avançar ▶", style=discord.ButtonStyle.primary, custom_id="next")
    async def btn_proximo(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.pagina_atual += 1
        self.atualizar_botoes()
        await interaction.response.edit_message(embed=self.criar_embed(), view=self)


# --- O SISTEMA PRINCIPAL ---
class Voz(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tempos_call = {} 
        self.preparar_banco()

    def preparar_banco(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute("ALTER TABLE usuarios ADD COLUMN tempo_voz INTEGER DEFAULT 0")
            conn.commit()
        except sqlite3.OperationalError:
            pass 
        conn.close()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot: return

        # Entrou na call
        if before.channel is None and after.channel is not None:
            self.tempos_call[member.id] = time.time()

        # Saiu da call
        elif before.channel is not None and after.channel is None:
            if member.id in self.tempos_call:
                tempo_entrou = self.tempos_call.pop(member.id)
                tempo_ficou_segundos = time.time() - tempo_entrou
                minutos_ficados = int(tempo_ficou_segundos // 60)

                if minutos_ficados > 0:
                    # xp padrão: 5 por minuto
                    xp_ganho = minutos_ficados * 5

                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    
                    # Pup Minha linda, aqui eu aplico o bônus de gado. Se a pessoa tiver conjuge, ganha +15%
                    c.execute("SELECT conjuge FROM usuarios WHERE user_id = ?", (str(member.id),))
                    res = c.fetchone()
                    if res and res[0] is not None:
                        # Multiplica por 1.15 pra dar os 15% de bônus
                        xp_ganho = int(xp_ganho * 1.15) 

                    c.execute("UPDATE usuarios SET xp = xp + ?, tempo_voz = tempo_voz + ? WHERE user_id = ?", 
                              (xp_ganho, minutos_ficados, str(member.id)))
                    conn.commit()
                    conn.close()

    @app_commands.command(name="ranking_call", description="Expõe a cara dos viciados que moram na call do servidor.")
    async def ranking_call(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT user_id, tempo_voz FROM usuarios WHERE tempo_voz > 0 ORDER BY tempo_voz DESC")
        todos_usuarios = c.fetchall()
        conn.close()

        if not todos_usuarios:
            await interaction.followup.send("🌀 Ninguém registrou tempo em call ainda. Vão conversar, bando de antissocial!", ephemeral=True)
            return

        view = VozPaginacao(todos_usuarios, interaction.guild, self.bot.user.display_avatar.url)
        await interaction.followup.send(embed=view.criar_embed(), view=view)

async def setup(bot):
    await bot.add_cog(Voz(bot))