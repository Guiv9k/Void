import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import io
import requests
import asyncio
from PIL import Image, ImageDraw, ImageFont

DB_PATH = "database/bot_data.db"
NOME_ARQUIVO_FUNDO = "fundo_xp.png"

# --- SISTEMA DE PAGINAÇÃO (BOTÕES) PARA O RANKING GERAL ---
class RankingPaginacao(discord.ui.View):
    def __init__(self, data, guilda, bot_avatar_url):
        super().__init__(timeout=120) 
        self.data = data
        self.guilda = guilda
        self.bot_avatar_url = bot_avatar_url
        self.pagina_atual = 0
        self.itens_por_pagina = 10
        self.total_paginas = max(1, (len(data) - 1) // self.itens_por_pagina + 1)
        self.atualizar_botoes()

    def atualizar_botoes(self):
        # Meu nobre, essa lógica desativa o botão de voltar se o cara já tiver na página 1 pra não bugar
        self.btn_anterior.disabled = self.pagina_atual == 0
        self.btn_proximo.disabled = self.pagina_atual == self.total_paginas - 1

    def criar_embed(self):
        inicio = self.pagina_atual * self.itens_por_pagina
        fim = inicio + self.itens_por_pagina
        itens_pagina = self.data[inicio:fim]

        embed = discord.Embed(
            title="📜 REGISTRO DE DESOCUPADOS",
            description="A lista completa dos CLTs que passam o dia farmando em vez de trabalhar.",
            color=0x00FFFF 
        )
        embed.set_thumbnail(url=self.bot_avatar_url)

        texto = ""
        for i, user_data in enumerate(itens_pagina):
            user_id = int(user_data[0])
            xp = user_data[1]
            nivel = user_data[2]
            rank = inicio + i + 1

            membro = self.guilda.get_member(user_id)
            nome = membro.display_name if membro else f"Fugitivo ({user_id})"

            icone_rank = "💀"
            if rank == 1: icone_rank = "🥇"
            elif rank == 2: icone_rank = "🥈"
            elif rank == 3: icone_rank = "🥉"

            texto += f"> **{icone_rank} #{rank}** | 👤 **{nome}**\n> 🧬 Nível: `{nivel}` | ✨ XP: `{xp:,}`\n\n"

        embed.add_field(name="Classificação Geral", value=texto if texto else "Nenhuma alma encontrada.", inline=False)
        embed.set_footer(text=f"Página {self.pagina_atual + 1} de {self.total_paginas} • Vai caçar o que fazer, mísera.")
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


# --- COMANDOS DO RANKING ---
class Ranking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def gerar_card_ranking(self, guilda, top_5_data, bot_avatar_url):
        # Pup Minha linda, esse bloco 'try' é salva-vidas. Se ele não achar a tua imagem 'fundo_xp.png', 
        # ele pinta um fundo preto meio azulado na marra ao invés de crashar o bot.
        try:
            background = Image.open(NOME_ARQUIVO_FUNDO).convert("RGBA")
            background = background.resize((1920, 1080))
        except:
            background = Image.new('RGBA', (1920, 1080), (10, 10, 15, 255))

        overlay = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        try:
            f_titulo = ImageFont.truetype("georgiab.ttf", 90)
            f_nick = ImageFont.truetype("arialbd.ttf", 40)
            f_stats = ImageFont.truetype("arial.ttf", 30)
        except:
            f_titulo = f_nick = f_stats = ImageFont.load_default()

        texto_titulo = "OS MAIORES LISOS"
        left, top, right, bottom = draw.textbbox((0, 0), texto_titulo, font=f_titulo)
        tw = right - left
        th = bottom - top
        
        x_titulo = (1920 - tw) // 2
        y_titulo = 60
        
        draw.text((x_titulo + 5, y_titulo + 5), texto_titulo, font=f_titulo, fill=(0, 255, 255, 100)) 
        draw.text((x_titulo, y_titulo), texto_titulo, font=f_titulo, fill=(255, 255, 255, 255))
        
        y_barrinha = y_titulo + th + 25
        largura_barrinha = tw + 40
        x_barrinha = (1920 - largura_barrinha) // 2
        draw.line([(x_barrinha, y_barrinha), (x_barrinha + largura_barrinha, y_barrinha)], fill=(0, 255, 255, 150), width=5)

        y_inicio_lista = 280
        for i, user_data in enumerate(top_5_data):
            user_id = int(user_data[0])
            xp = user_data[1]
            nivel = user_data[2]
            rank = i + 1
            
            membro = guilda.get_member(user_id)
            user_nick = membro.display_name.upper() if membro else f"XUPETA {user_id}"
            user_avatar_url = membro.display_avatar.url if membro else bot_avatar_url

            y_linha = y_inicio_lista + (i * 150)
            draw.rounded_rectangle((100, y_linha, 1820, y_linha + 130), radius=30, fill=(0, 0, 0, 170), outline=(0, 255, 255, 100), width=3)
            
            draw.text((150, y_linha + 45), f"#{rank}", font=f_nick, fill=(0, 255, 255, 255))
            
            try:
                response = requests.get(user_avatar_url)
                avatar_img = Image.open(io.BytesIO(response.content)).convert("RGBA")
                avatar_img = avatar_img.resize((100, 100))
                
                mask = Image.new('L', (100, 100), 0)
                draw_mask = ImageDraw.Draw(mask)
                draw_mask.ellipse((0, 0, 100, 100), fill=255)
                
                overlay.paste(avatar_img, (280, y_linha + 15), mask)
                draw.ellipse((280, y_linha + 15, 280 + 100, y_linha + 15 + 100), outline=(0, 255, 255, 200), width=3)
            except:
                draw.ellipse((280, y_linha + 15, 280 + 100, y_linha + 15 + 100), fill=(50, 50, 50))

            draw.text((420 + 2, y_linha + 25 + 2), user_nick, font=f_nick, fill=(0, 0, 0, 255))
            draw.text((420, y_linha + 25), user_nick, font=f_nick, fill=(255, 255, 255, 255))
            
            x_status = 1250
            draw.text((x_status, y_linha + 25), f"NÍVEL: {nivel}", font=f_stats, fill=(255, 255, 255, 255))
            draw.text((x_status, y_linha + 70), f"XP TOTAL: {xp:,}", font=f_stats, fill=(0, 255, 255, 255))

        final = Image.alpha_composite(background, overlay)
        buf = io.BytesIO()
        final.save(buf, format="PNG")
        buf.seek(0)
        return buf

    @app_commands.command(name="xp_ranking", description="O vácuo expõe a cara dos 5 maiores desocupados do servidor em uma imagem.")
    async def xp_ranking(self, interaction: discord.Interaction):
        await interaction.response.defer()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT user_id, xp, nivel FROM usuarios ORDER BY nivel DESC, xp DESC LIMIT 5")
        top_5 = c.fetchall()
        conn.close()

        if not top_5:
            await interaction.followup.send("🌀 O vácuo ainda não consumiu ninguém. Bando de CLT ocupado.", ephemeral=True)
            return

        # Bros, isso aqui evita do bot travar o Discord inteiro enquanto desenha a imagem.
        img_buffer = await asyncio.to_thread(self.gerar_card_ranking, interaction.guild, top_5, self.bot.user.display_avatar.url)
        
        await interaction.followup.send(content="📸 Tá aí a foto dos maiores frangos do servidor:", file=discord.File(fp=img_buffer, filename="ranking.png"))

    @app_commands.command(name="ranking_all", description="Lista completa pra você ver o quão liso você está no ranking geral.")
    async def ranking_all(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT user_id, xp, nivel FROM usuarios ORDER BY nivel DESC, xp DESC")
        todos_usuarios = c.fetchall()
        conn.close()

        if not todos_usuarios:
            await interaction.followup.send("🌀 O vácuo está vazio. Ninguém pisou aqui ainda.", ephemeral=True)
            return

        view = RankingPaginacao(todos_usuarios, interaction.guild, self.bot.user.display_avatar.url)
        await interaction.followup.send(embed=view.criar_embed(), view=view)

async def setup(bot):
    await bot.add_cog(Ranking(bot))