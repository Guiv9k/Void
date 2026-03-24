import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import datetime

DB_PATH = "database/bot_data.db"

class Perfil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Função mágica que cria a barrinha de progresso do XP
    def gerar_barra_xp(self, xp, xp_max):
        porcentagem = min(int((xp / xp_max) * 100), 100)
        blocos_cheios = porcentagem // 10
        blocos_vazios = 10 - blocos_cheios
        barra = ("▰" * blocos_cheios) + ("▱" * blocos_vazios)
        return f"{barra} {porcentagem}% ({xp:,} / {xp_max:,} XP)"

    @app_commands.command(name="perfil", description="Puxa a capivara completa de alguém no banco do Agiota.")
    async def perfil(self, interaction: discord.Interaction, membro: discord.Member = None):
        await interaction.response.defer()
        
        alvo = membro or interaction.user
        alvo_id = str(alvo.id)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # 1. Puxa XP, Nível e Moedas
        c.execute("SELECT moedas, nivel, xp FROM usuarios WHERE user_id = ?", (alvo_id,))
        stats = c.fetchone()
        
        if not stats:
            moedas, nivel, xp = 0, 1, 0
        else:
            moedas, nivel, xp = stats

        # 2. Puxa as Reputações e conta o Total de Prestígio
        # Bros, eu mantive a busca por reputação, mas se não tiver a tabela, o bot não quebra
        dict_reps = {"genio": 0, "caos": 0, "traidor": 0, "bondade": 0}
        total_rep = 0
        try:
            c.execute("SELECT categoria, quantidade FROM reputacao WHERE user_id = ?", (alvo_id,))
            reps = c.fetchall()
            for rep in reps:
                dict_reps[rep[0]] = rep[1]
                total_rep += rep[1]
        except sqlite3.OperationalError:
            pass 

        # 3. Conta as Conquistas
        total_conquistas = 0
        try:
            c.execute("SELECT COUNT(*) FROM conquistas WHERE user_id = ?", (alvo_id,))
            res_conq = c.fetchone()
            total_conquistas = res_conq[0] if res_conq else 0
        except sqlite3.OperationalError:
            pass

        # 4. Verifica o Vínculo (Casamento) se a tabela existir
        # Minha linda, aqui eu botei 'Solteirão' pra zoar quem não casou ainda no comando social
        vinculo = "Solteirão Liso"
        try:
            c.execute("SELECT parceiro_id FROM casamentos WHERE user_id = ?", (alvo_id,))
            casamento = c.fetchone()
            if casamento:
                vinculo = f"<@{casamento[0]}>"
        except sqlite3.OperationalError:
            pass 

        conn.close()

        # Calcula o XP Máximo para o próximo nível
        # MEU NOBRE AQUI TAVA O ERRO! Lá na economia a gente botou (nivel+1)*500. 
        # Se deixar 300 aqui o painel de XP ia bugar. Já arrumei pra 500!
        xp_max = (nivel + 1) * 500
        barra_xp = self.gerar_barra_xp(xp, xp_max)

        # Laudo Psicológico e Cores Dinâmicas com os xingamentos do Void
        if dict_reps["caos"] > dict_reps["genio"] and dict_reps["caos"] > dict_reps["bondade"]:
            psicologico = "Shitposter Tóxico."
            cor_embed = 0xFF0000 
        elif dict_reps["genio"] > 0 and dict_reps["genio"] >= dict_reps["caos"]:
            psicologico = "Nerdola."
            cor_embed = 0x00FFFF 
        elif dict_reps["traidor"] > 0:
            psicologico = "Talarico / Agiota."
            cor_embed = 0x808080 
        elif dict_reps["bondade"] > 0:
            psicologico = "Xupeta Bonzinho."
            cor_embed = 0x00FF00 
        else:
            psicologico = "CLT Genérico"
            cor_embed = 0x2b2d31 

        # --- A JUNÇÃO DOS DOIS MUNDOS  ---
        embed = discord.Embed(
            title=f"🪪 CAPIVARA CRIMINAL: {alvo.display_name}",
            description="*Ficha puxada direto do Serasa do Vácuo.*\n" + "━"*25,
            color=cor_embed
        )
        embed.set_thumbnail(url=alvo.display_avatar.url)

        # Linha 1: Status Base
        embed.add_field(name="💰 Conta do Agiota", value=f"`{moedas:,}` moedas", inline=True)
        embed.add_field(name="⭐ Moral no Server", value=f"`{total_rep}` REP", inline=True)
        embed.add_field(name="🏆 Estante", value=f"`{total_conquistas}` troféus", inline=True)

        # Linha 2: Lore do Jogador
        embed.add_field(name="💍 Casamento", value=vinculo, inline=True)
        embed.add_field(name="🧠 Laudo Void", value=psicologico, inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True) # Campo invisível pra alinhar bonitinho

        # Linha 3: Reputação Detalhada
        detalhes_rep = f"> 🧠 `{dict_reps['genio']}` Nerd | 🌪️ `{dict_reps['caos']}` Shitpost\n> 🔪 `{dict_reps['traidor']}` Talarico | 🤝 `{dict_reps['bondade']}` Xupeta"
        embed.add_field(name="🎭 Status na Sociedade", value=detalhes_rep, inline=False)

        # Linha 4: A Clássica Barra de Progresso
        embed.add_field(name=f"🧬 Nível {nivel}", value=f"`{barra_xp}`", inline=False)

        # Rodapé Oficial
        embed.set_footer(text=f"ID do Liso: {alvo.id} • CPF negativado", icon_url=self.bot.user.display_avatar.url)
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Perfil(bot))