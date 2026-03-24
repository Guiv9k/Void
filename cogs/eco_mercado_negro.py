import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

DB_PATH = "database/bot_data.db"

class MercadoNegroDropdown(discord.ui.Select):
    def __init__(self):
        opcoes = [
            discord.SelectOption(
                label="RG Falso (Limpa Nome)", 
                description="Zera tua dívida no Serasa do Vácuo. Custa: 1.500 moedas.", 
                emoji="🪪", 
                value="rg_falso"
            ),
            discord.SelectOption(
                label="Pé de Cabra [EM BREVE]", 
                description="Vai aumentar a chance de sucesso no assalto (Próxima Att).", 
                emoji="⛏️", 
                value="pe_de_cabra"
            ),
            discord.SelectOption(
                label="Suborno Policial [EM BREVE]", 
                description="Zera o tempo de espera pra fazer outro crime (Próxima Att).", 
                emoji="👮‍♂️", 
                value="suborno"
            )
        ]
        super().__init__(placeholder="Escolhe a muamba, anda logo...", min_values=1, max_values=1, options=opcoes)

    async def callback(self, interaction: discord.Interaction):
        escolha = self.values[0]

        if escolha in ["pe_de_cabra", "suborno"]:
            return await interaction.response.send_message("❌ Tá cego, xupeta? Essa porra tá sem estoque. Volta na próxima atualização do bot.", ephemeral=True)

        user_id = str(interaction.user.id)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("SELECT moedas FROM usuarios WHERE user_id = ?", (user_id,))
        res = c.fetchone()

        if not res:
            conn.close()
            return await interaction.response.send_message("🌀 Tu nem existe no sistema. Vai mandar mensagem no chat primeiro.", ephemeral=True)

        saldo_atual = res[0]
        preco_rg = 1500

        if escolha == "rg_falso":
            # O cara precisa ter PELO MENOS a grana do RG, ou seja, se ele tá devendo 3000, 
            # como ele vai comprar? Ele vai ter que arrumar alguem pra transferir pra ele!
            # Mas, pra facilitar o shitpost, vou deixar o cara comprar o RG com XP ou se ele tiver as moedas na mão.
            # Vamos fazer diferente: O RG custa 1500, mas só faz sentido se o cara TIVER as 1500 moedas pra pagar o atravessador.
            if saldo_atual < preco_rg:
                conn.close()
                return await interaction.response.send_message(f"💀 Tu é liso e burro. Como tu vai comprar um RG Falso de `{preco_rg}` moedas se tu só tem `{saldo_atual}`? Pede dinheiro pra tua webnamorada!", ephemeral=True)

            # Só compensa usar se o cara estiver devendo (pra limpar a dívida) ou perto de negativar.
            # Se o cara tem 10000 moedas, e gasta 1500 pra ficar com 0, ele é demente KKKKK
            
            # Cobra os 1500 do atravessador e ZERA as dívidas negativas!
            # Se o cara tinha 1500, ele fica com 0. Se ele for usar isso pra limpar nome, ele ia precisar ter juntado os 1500.
            # Pera, o Void é Agiota! A gente perdoa a dívida negativa e bota a conta dele em ZERO.
            
            c.execute("UPDATE usuarios SET moedas = 0 WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()

            embed = discord.Embed(
                title="🪪 IDENTIDADE FORJADA",
                description="> **NOME:** Zé Ninguém da Silva\n> **CPF:** 000.000.000-00\n\nTu pagou o falsificador, ele queimou teus documentos antigos e hackeou o Serasa do Vácuo.\n\n💰 **Tua dívida de assaltos foi apagada.** Teu saldo atual agora é cravado em `0` moedas.",
                color=0x00FF00
            )
            embed.set_thumbnail(url="https://i.imgur.com/q3LXXHh.png") # Uma imagem genérica de hacker/anon
            embed.set_footer(text="Vê se não suja o nome de novo, CLT de merda.")
            
            await interaction.response.send_message(embed=embed)


class MercadoNegroView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MercadoNegroDropdown())

class MercadoNegro(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="biqueira", description="Acesse a loja clandestina. Itens ilegais e falsificações.")
    async def biqueira(self, interaction: discord.Interaction):
        # Cor mega escura pra dar o tema "Negro" que tu pediu
        embed = discord.Embed(
            title="🌑 BIQUEIRA DO VÁCUO",
            description="Tu entrou num beco escuro e fedendo a mijo. Tem um maluco de capuz vendendo umas paradas suspeitas.\n\n> ⚠️ **Aviso:** Se a polícia do server pegar, tu vai de arrasta pra cima.\n> Escolhe logo o que tu quer e vaza.",
            color=0x080808
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Sem devolução. Se quebrar, problema é teu.")

        view = MercadoNegroView()
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(MercadoNegro(bot))