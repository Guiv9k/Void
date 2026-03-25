import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

DB_PATH = "database/bot_data.db"
PRECO_FACCAO = 10000


class Faccao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.atualizar_banco()

    def atualizar_banco(self):
        # O Raio-X age aqui: cria as colunas de visualização se elas não existirem
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        colunas_visuais = [
            ("slogan", "TEXT DEFAULT 'Fazendo dinheiro sujo no Vácuo.'"),
            ("logo_url", "TEXT"),
        ]
        for nome, tipo in colunas_visuais:
            try:
                c.execute(f"ALTER TABLE faccoes ADD COLUMN {nome} {tipo}")
            except sqlite3.OperationalError:
                pass
        conn.commit()
        conn.close()

    # Grupo de comandos /faccao
    grupo = app_commands.Group(
        name="faccao", description="Sistema de Cartel e Máfia do Vácuo."
    )

    @grupo.command(
        name="criar", description="Custa 10.000 moedas. Monte seu império do crime."
    )
    @app_commands.describe(
        nome="O nome do teu Cartel",
        slogan="A frase de efeito da máfia",
        logo_url="Link de uma imagem pra ser o brasão",
    )
    async def criar_faccao(
        self,
        interaction: discord.Interaction,
        nome: str,
        slogan: str = None,
        logo_url: str = None,
    ):
        user_id = str(interaction.user.id)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("SELECT moedas FROM usuarios WHERE user_id = ?", (user_id,))
        res = c.fetchone()

        if not res or res[0] < PRECO_FACCAO:
            conn.close()
            return await interaction.response.send_message(
                f"❌ Ai dento! Tu precisa de `{PRECO_FACCAO:,}` moedas pra fundar a facção. Vai capinar um lote!",
                ephemeral=True,
            )

        c.execute("SELECT faccao_id FROM membros_faccao WHERE user_id = ?", (user_id,))
        if c.fetchone():
            conn.close()
            return await interaction.response.send_message(
                "❌ Tu já tá numa facção, traidor! Sai da tua antes de criar outra.",
                ephemeral=True,
            )

        slogan_final = slogan if slogan else "Fazendo dinheiro sujo no Vácuo."

        try:
            c.execute(
                "UPDATE usuarios SET moedas = moedas - ? WHERE user_id = ?",
                (PRECO_FACCAO, user_id),
            )
            c.execute(
                "INSERT INTO faccoes (nome, dono_id, slogan, logo_url) VALUES (?, ?, ?, ?)",
                (nome, user_id, slogan_final, logo_url),
            )
            faccao_id = c.lastrowid
            c.execute(
                "INSERT INTO membros_faccao (user_id, faccao_id) VALUES (?, ?)",
                (user_id, faccao_id),
            )
            conn.commit()

            embed = discord.Embed(
                title="🏴 ALVARÁ DO CRIME APROVADO",
                description=f"**{interaction.user.mention}** subornou o Agiota e abriu o próprio Cartel!\n"
                + "━" * 25,
                color=0x2B2D31,
            )
            embed.add_field(name="🗡️ Nome da Facção", value=f"`{nome}`", inline=False)
            embed.add_field(name="🗣️ Lema", value=f"*{slogan_final}*", inline=False)

            if logo_url:
                embed.set_thumbnail(url=logo_url)
            else:
                embed.set_thumbnail(url=interaction.user.display_avatar.url)

            embed.set_footer(text="A chapa vai esquentar no servidor.")
            await interaction.response.send_message(embed=embed)
        except sqlite3.IntegrityError:
            await interaction.response.send_message(
                "❌ Já existe um cartel com esse nome, sem criatividade.",
                ephemeral=True,
            )
        finally:
            conn.close()

    @grupo.command(
        name="entrar",
        description="Vire aviãozinho de uma facção (precisa saber o ID dela).",
    )
    async def entrar_faccao(self, interaction: discord.Interaction, id_faccao: int):
        user_id = str(interaction.user.id)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("SELECT faccao_id FROM membros_faccao WHERE user_id = ?", (user_id,))
        if c.fetchone():
            conn.close()
            return await interaction.response.send_message(
                "❌ Tu já é marmita de outra facção. Sai dela primeiro.", ephemeral=True
            )

        c.execute("SELECT nome FROM faccoes WHERE id = ?", (id_faccao,))
        faccao = c.fetchone()

        if not faccao:
            conn.close()
            return await interaction.response.send_message(
                "❌ Essa facção não existe. Fumou pedra?", ephemeral=True
            )

        c.execute(
            "INSERT INTO membros_faccao (user_id, faccao_id) VALUES (?, ?)",
            (user_id, id_faccao),
        )
        conn.commit()
        conn.close()

        await interaction.response.send_message(
            f"🤝 **{interaction.user.mention}** jurou lealdade e entrou pra facção **{faccao[0]}**!"
        )

    @grupo.command(
        name="painel",
        description="Abre o painel VIP do teu Cartel com o visual completo.",
    )
    async def painel_faccao(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("SELECT faccao_id FROM membros_faccao WHERE user_id = ?", (user_id,))
        res = c.fetchone()

        if not res:
            conn.close()
            return await interaction.response.send_message(
                "❌ Tu é um lobo solitário (ou só um CLT sem amigos). Tu não tem facção.",
                ephemeral=True,
            )

        faccao_id = res[0]
        c.execute(
            "SELECT nome, dono_id, caixa, nivel, slogan, logo_url FROM faccoes WHERE id = ?",
            (faccao_id,),
        )
        faccao = c.fetchone()

        c.execute(
            "SELECT COUNT(*) FROM membros_faccao WHERE faccao_id = ?", (faccao_id,)
        )
        qtd_membros = c.fetchone()[0]
        conn.close()

        # O VISUAL BONITO TÁ AQUI
        embed = discord.Embed(
            title=f"🏴 CARTEL: {faccao[0].upper()}",
            description=f"*{faccao[4]}*\n" + "━" * 25,
            color=0xFF0000,
        )

        if faccao[5]:  # Se tiver logo_url
            try:
                embed.set_thumbnail(url=faccao[5])
            except:
                pass  # Ignora se o link da imagem tiver quebrado

        embed.add_field(name="👑 Chefão", value=f"<@{faccao[1]}>", inline=True)
        embed.add_field(
            name="🧬 Nível de Ameaça", value=f"`Lv. {faccao[3]}`", inline=True
        )
        embed.add_field(name="👥 Capangas", value=f"`{qtd_membros}`", inline=True)

        embed.add_field(
            name="💰 Cofre da Máfia",
            value=f"`{faccao[2]:,}` moedas lavadas",
            inline=False,
        )

        embed.set_footer(
            text=f"ID da Facção: {faccao_id} | Passa o ID pros teus parceiros entrarem.",
            icon_url=self.bot.user.display_avatar.url,
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Faccao(bot))
