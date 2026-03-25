import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import datetime
import os

DB_PATH = "database/bot_data.db"
IMG_FOLDER = "imagens_casamento"
PRECO_CASAMENTO = 5000
PRECO_DIVORCIO = 1000


class PedidoCasamento(discord.ui.View):
    def __init__(self, autor, alvo, cog_social):
        super().__init__(timeout=60)
        self.autor = autor
        self.alvo = alvo
        self.cog_social = cog_social

    @discord.ui.button(label="Sim, sou gado! 💍", style=discord.ButtonStyle.success)
    async def aceitar(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.alvo.id:
            return await interaction.response.send_message(
                "❌ Sai do meio, xupeta! O pedido não é pra tu.", ephemeral=True
            )

        data_hoje = datetime.datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Oficializa e cobra o valor absurdo
        c.execute(
            "UPDATE usuarios SET moedas = moedas - ?, conjuge = ?, data_casamento = ? WHERE user_id = ?",
            (PRECO_CASAMENTO, str(self.alvo.id), data_hoje, str(self.autor.id)),
        )
        c.execute(
            "UPDATE usuarios SET conjuge = ?, data_casamento = ? WHERE user_id = ?",
            (str(self.autor.id), data_hoje, str(self.alvo.id)),
        )
        conn.commit()
        conn.close()

        linha = "━" * 25
        embed = discord.Embed(
            title="✨ CONTRATO DE GADO ASSINADO ✨",
            description=(
                f"**Que nojo. Os dois xupetas agora tão juntos.**\n\n"
                f"💍 **Gados:** {self.autor.mention} & {self.alvo.mention}\n"
                f"💳 **Taxa do Cartório:** `{PRECO_CASAMENTO}` moedas (Bem feito)\n"
                f"🗓️ **Data do Erro:** `{data_hoje}`\n"
                f"{linha}"
            ),
            color=0xFF69B4,
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(
            text="Até que o chifre os separe.",
            icon_url=self.cog_social.bot.user.display_avatar.url,
        )

        await self.cog_social.enviar_com_imagem_local(
            interaction, embed, "casamento.png"
        )
        self.stop()

    @discord.ui.button(label="Mandar Pastar 💔", style=discord.ButtonStyle.danger)
    async def recusar(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.alvo.id:
            return
        await interaction.response.edit_message(
            content=f"💔 **{self.alvo.display_name}** mandou o cara pastar. O Vácuo amou essa humilhação.",
            embed=None,
            view=None,
        )
        self.stop()


class Social(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.garantir_colunas()

    def garantir_colunas(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute("ALTER TABLE usuarios ADD COLUMN data_casamento TEXT")
            conn.commit()
        except:
            pass
        conn.close()

    async def enviar_com_imagem_local(
        self,
        interaction: discord.Interaction,
        embed: discord.Embed,
        nome_imagem: str,
        followup=False,
    ):
        path_png = os.path.join(IMG_FOLDER, nome_imagem.replace(".jpg", ".png"))
        path_jpg = os.path.join(IMG_FOLDER, nome_imagem.replace(".png", ".jpg"))
        arquivo_final = (
            path_png
            if os.path.exists(path_png)
            else (path_jpg if os.path.exists(path_jpg) else None)
        )

        if arquivo_final:
            file = discord.File(arquivo_final, filename=f"image_{nome_imagem}")
            embed.set_image(url=f"attachment://image_{nome_imagem}")
            if followup:
                await interaction.followup.send(file=file, embed=embed)
            elif interaction.response.is_done():
                await interaction.followup.send(file=file, embed=embed)
            else:
                await interaction.response.send_message(file=file, embed=embed)
        else:
            if followup:
                await interaction.followup.send(embed=embed)
            elif interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="casamento", description="Exibe a certidão de gado oficial."
    )
    async def ver_casamento(
        self, interaction: discord.Interaction, usuario: discord.Member = None
    ):
        target = usuario or interaction.user
        await interaction.response.defer()

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT conjuge, data_casamento FROM usuarios WHERE user_id = ?",
            (str(target.id),),
        )
        res = c.fetchone()
        conn.close()

        if not res or res[0] is None or res[0] == "None":
            return await interaction.followup.send(
                f"🌀 O CPF de <@{target.id}> tá limpo. Esse é Solteirão Liso ainda.",
                ephemeral=True,
            )

        conjuge_id = res[0]
        data_string = res[1] or "No tempo que a internet era a lenha"
        dias_texto = "Infinitos"
        if res[1]:
            try:
                data_casamento = datetime.datetime.strptime(res[1], "%Y-%m-%d")
                diferenca = datetime.datetime.now() - data_casamento
                dias_texto = f"{diferenca.days} dias de sofrimento"
            except:
                pass

        linha = "━" * 15
        embed = discord.Embed(
            title="📜 REGISTRO DE GADO",
            description=f"*Certidão registrada no Cartório do Agiota.*\n{linha}",
            color=0xFF69B4,
            timestamp=datetime.datetime.now(),
        )
        embed.set_author(
            name=f"Vínculo do Xupeta: {target.display_name}",
            icon_url=target.display_avatar.url,
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        embed.add_field(
            name="💘 Sofre junto com:",
            value=f"> **Membro:** <@{conjuge_id}>\n> **ID:** `{conjuge_id}`",
            inline=False,
        )
        embed.add_field(
            name="⏳ Tempo Suportando",
            value=f"> **Assinado em:** `{data_string}`\n> **Duração:** `{dias_texto}`",
            inline=True,
        )
        embed.add_field(
            name="🧿 Benefícios",
            value="> `+15% XP` na Call com a Webnamorada\n> `Chifre`",
            inline=True,
        )

        embed.set_footer(
            text=f"ID do Gado: #VAC-{str(target.id)[-5:]}",
            icon_url=self.bot.user.display_avatar.url,
        )
        await self.enviar_com_imagem_local(
            interaction, embed, "perfil_casado.png", followup=True
        )

    @app_commands.command(
        name="casar", description="Se amarre a um xupeta por incríveis 5.000 moedas."
    )
    async def casar(self, interaction: discord.Interaction, conjuge: discord.Member):
        if conjuge.id == interaction.user.id or conjuge.bot:
            return await interaction.response.send_message(
                "❌ Casar com o próprio ego ou com robô não dá XP, mísera.",
                ephemeral=True,
            )

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT moedas, conjuge FROM usuarios WHERE user_id = ?",
            (str(interaction.user.id),),
        )
        res = c.fetchone()

        # Bros, eu chequei se o ALVO não tá casado tbm, pra não dar bigamia no servidor KKKK
        c.execute("SELECT conjuge FROM usuarios WHERE user_id = ?", (str(conjuge.id),))
        res_alvo = c.fetchone()
        conn.close()

        moedas_atuais = res[0] if res and res[0] is not None else 0
        ja_casado = res[1] if res and res[1] is not None else None
        alvo_casado = res_alvo[0] if res_alvo and res_alvo[0] is not None else None

        if moedas_atuais < PRECO_CASAMENTO:
            return await interaction.response.send_message(
                f"❌ Casar custa `{PRECO_CASAMENTO}` pra pagar o padre. Tu só tem `{moedas_atuais}`. Vai trabalhar CLT!",
                ephemeral=True,
            )

        if ja_casado:
            return await interaction.response.send_message(
                "❌ Tu já é casado, talarico! Paga a pensão do divórcio primeiro.",
                ephemeral=True,
            )

        if alvo_casado:
            return await interaction.response.send_message(
                "❌ Ai dento! A pessoa já tá casada. Sai de perto que dá morte.",
                ephemeral=True,
            )

        embed = discord.Embed(
            title="💍 PEDIDO DE GADO",
            description=f"**{interaction.user.mention}** tá cego de amor e quer se unir a **{conjuge.mention}**.\n\n💰 **Taxa do Padre:** `{PRECO_CASAMENTO}` moedas saem da conta do emocionado.",
            color=0x00FFFF,
        )
        embed.set_footer(text="Vai aceitar essa humilhação?")

        view = PedidoCasamento(interaction.user, conjuge, self)
        await interaction.response.send_message(
            content=f"{conjuge.mention}", embed=embed, view=view
        )

    @app_commands.command(name="beijar", description="Dê um beijo em alguém.")
    async def beijar(self, interaction: discord.Interaction, usuario: discord.Member):
        if usuario.id == interaction.user.id or usuario.bot:
            return await interaction.response.send_message(
                "❌ Beijar o próprio braço é foda.", ephemeral=True
            )
        embed = discord.Embed(
            description=f"💋 Ui ui ui! **{interaction.user.display_name}** tascou um beijão de língua no(a) **{usuario.display_name}**!",
            color=0xFF69B4,
        )
        await self.enviar_com_imagem_local(interaction, embed, "beijo.png")

    @app_commands.command(name="abracar", description="Dê um abraço em alguém.")
    async def abracar(self, interaction: discord.Interaction, usuario: discord.Member):
        embed = discord.Embed(
            description=f"🫂 **{interaction.user.display_name}** deu um abraço de urso carente em **{usuario.display_name}**!",
            color=0x00FFFF,
        )
        await self.enviar_com_imagem_local(interaction, embed, "abraco.png")

    @app_commands.command(name="tapa", description="Mete a mão na orelha de alguém.")
    async def tapa(self, interaction: discord.Interaction, usuario: discord.Member):
        if usuario.id == self.bot.user.id:
            return await interaction.response.send_message(
                "❌ Tenta bater em mim pra tu ver se teu HD não queima amanhã.",
                ephemeral=True,
            )
        embed = discord.Embed(
            description=f"🖐️ POU! **{interaction.user.display_name}** meteu a mão na orelha do(a) **{usuario.display_name}**!",
            color=0xFF0000,
        )
        await self.enviar_com_imagem_local(interaction, embed, "tapa.png")

    @app_commands.command(
        name="divorciar",
        description="Paga 1.000 pro advogado do Vácuo e se livra do encosto.",
    )
    async def divorciar(self, interaction: discord.Interaction):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT conjuge, moedas FROM usuarios WHERE user_id = ?",
            (str(interaction.user.id),),
        )
        res = c.fetchone()

        if not res or res[0] is None:
            conn.close()
            return await interaction.response.send_message(
                "Tu nem casado é, liso.", ephemeral=True
            )

        moedas = res[1] if res[1] is not None else 0
        if moedas < PRECO_DIVORCIO:
            conn.close()
            return await interaction.response.send_message(
                f"❌ O advogado cobra `{PRECO_DIVORCIO}` pra assinar os papéis. Tu não tem grana nem pra separar.",
                ephemeral=True,
            )

        ex_id = res[0]
        c.execute(
            "UPDATE usuarios SET conjuge = NULL, data_casamento = NULL, moedas = moedas - ? WHERE user_id = ?",
            (PRECO_DIVORCIO, str(interaction.user.id)),
        )
        c.execute(
            "UPDATE usuarios SET conjuge = NULL, data_casamento = NULL WHERE user_id = ?",
            (str(ex_id),),
        )
        conn.commit()
        conn.close()

        await interaction.response.send_message(
            f"💔 **{interaction.user.mention}** pagou o advogado e chutou <@{ex_id}> pra rua. A pista tá livre, xupetas!"
        )

    @app_commands.command(
        name="lore",
        description="Puxa o fofoqueiro mór: quem tá por cima e quem tá quebrado.",
    )
    async def lore(self, interaction: discord.Interaction):
        await interaction.response.defer()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT user_id, moedas FROM usuarios ORDER BY moedas DESC LIMIT 1")
        rico = c.fetchone()
        c.execute(
            "SELECT user_id, moedas FROM usuarios WHERE moedas < 50 ORDER BY moedas ASC LIMIT 1"
        )
        pobre = c.fetchone()
        conn.close()

        embed = discord.Embed(title="👁️ FOFOCAS DO AGIOTA", color=0x2B2D31)
        if rico:
            embed.add_field(
                name="💰 Magnata do Server",
                value=f"<@{rico[0]}> nadando no dinheiro.",
                inline=False,
            )
        if pobre:
            embed.add_field(
                name="💀 Mais Liso que Sabonete",
                value=f"<@{pobre[0]}> tá morrendo de fome.",
                inline=False,
            )

        if not rico and not pobre:
            embed.description = (
                "Não tem lore porque o banco do Agiota faliu (ninguém no DB)."
            )

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Social(bot))
