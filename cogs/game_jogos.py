import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import random
import asyncio

DB_PATH = "database/bot_data.db"


# --- MINI-GAME DOS BOTÕES COLORIDOS (TIROTEIO) ---
class DueloGameView(discord.ui.View):
    def __init__(self, p1, p2, aposta, cor_certa):
        super().__init__(timeout=15)
        self.p1 = p1
        self.p2 = p2
        self.aposta = aposta
        self.cor_certa = cor_certa
        self.clicado = False

        # Cria os botões e embaralha a ordem deles pra foder a mente dos xupetas
        botoes = [
            discord.ui.Button(
                label="VERMELHO", style=discord.ButtonStyle.danger, custom_id="vermelho"
            ),
            discord.ui.Button(
                label="AZUL", style=discord.ButtonStyle.primary, custom_id="azul"
            ),
            discord.ui.Button(
                label="VERDE", style=discord.ButtonStyle.success, custom_id="verde"
            ),
            discord.ui.Button(
                label="CINZA", style=discord.ButtonStyle.secondary, custom_id="cinza"
            ),
        ]
        random.shuffle(botoes)

        for btn in botoes:
            btn.callback = self.criar_callback(btn.custom_id)
            self.add_item(btn)

    def criar_callback(self, cor_clicada):
        async def callback(interaction: discord.Interaction):
            # Só os duelistas podem clicar, se um aleatório clicar toma esporro
            if interaction.user not in [self.p1, self.p2]:
                await interaction.response.send_message(
                    "❌ Sai do meio da bala bala perdida, mísera!", ephemeral=True
                )
                return
            if self.clicado:
                return
            self.clicado = True

            # Desativa os botões na hora
            for item in self.children:
                item.disabled = True

            # Checa se o cara clicou certo ou foi burro
            if cor_clicada == self.cor_certa:
                vencedor = interaction.user
                perdedor = self.p1 if interaction.user == self.p2 else self.p2
                motivo = f"**{vencedor.mention}** teve reflexos de águia e cravou o dedo no botão **{cor_clicada.upper()}** primeiro!"
            else:
                perdedor = interaction.user
                vencedor = self.p1 if interaction.user == self.p2 else self.p2
                motivo = f"💀 **{perdedor.mention}** é um CLT lerdo, clicou no **{cor_clicada.upper()}** por engano e tomou um pipoco na testa!"

            # Atualiza o banco do agiota
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                "UPDATE usuarios SET moedas = moedas + ? WHERE user_id = ?",
                (self.aposta, str(vencedor.id)),
            )
            c.execute(
                "UPDATE usuarios SET moedas = moedas - ? WHERE user_id = ?",
                (self.aposta, str(perdedor.id)),
            )
            conn.commit()
            conn.close()

            embed = discord.Embed(
                title="🏆 FIM DO TIROTEIO",
                description=f"{motivo}\n\n> Vencedor: {vencedor.mention} `(+{self.aposta:,})`\n> Perdedor: {perdedor.mention} `(-{self.aposta:,})`\n\n*Aham q lindo me paga um boquete dps desse capa.*",
                color=0x00FF00 if cor_clicada == self.cor_certa else 0xFFD700,
            )
            embed.set_thumbnail(url=vencedor.display_avatar.url)
            await interaction.response.edit_message(embed=embed, view=self)
            self.stop()

        return callback


class Jogos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Bros, mudei o nome de 'duelo' pra 'tiroteio' pra não bugar com o duelo de texto do crime.py!
    @app_commands.command(
        name="tiroteio", description="Desafie um xupeta. Teste seus reflexos com cores."
    )
    async def tiroteio(
        self, interaction: discord.Interaction, oponente: discord.Member, aposta: int
    ):
        if oponente.id == interaction.user.id or oponente.bot:
            await interaction.response.send_message(
                "🌀 Tá esquizofrênico, mísera? Escolhe alguém de verdade.",
                ephemeral=True,
            )
            return
        if aposta <= 0:
            await interaction.response.send_message(
                "💸 Aposta mixuruca não vale. Coloca dinheiro de verdade.",
                ephemeral=True,
            )
            return

        # Pup Minha linda, adicionei a verificação de saldo aqui pra não ter calote no servidor.
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT moedas FROM usuarios WHERE user_id = ?", (str(interaction.user.id),)
        )
        res_autor = c.fetchone()
        c.execute("SELECT moedas FROM usuarios WHERE user_id = ?", (str(oponente.id),))
        res_alvo = c.fetchone()
        conn.close()

        saldo_autor = res_autor[0] if res_autor else 0
        saldo_alvo = res_alvo[0] if res_alvo else 0

        if saldo_autor < aposta:
            return await interaction.response.send_message(
                f"❌ Tu é liso, parceiro! Não tem `{aposta:,}` moedas.", ephemeral=True
            )
        if saldo_alvo < aposta:
            return await interaction.response.send_message(
                f"❌ O {oponente.display_name} é um frango e não tem `{aposta:,}` moedas pra cobrir a aposta.",
                ephemeral=True,
            )

        embed_convite = discord.Embed(
            title="⚔️ TIROTEIO MARCADO",
            description=f"**{interaction.user.mention}** chamou **{oponente.mention}** pro x1!\n\n> Valor: `{aposta:,}` moedas.\n\n*Regras: Eu vou gritar uma cor. O primeiro que clicar no botão da cor certa, leva tudo. Clicou errado, vai de base na hora!*",
            color=0xFFD700,
        )

        class DueloAcceptView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.aceito = False

            @discord.ui.button(
                label="Cair pro Pau", style=discord.ButtonStyle.danger, emoji="⚔️"
            )
            async def aceitar(
                self, inter: discord.Interaction, button: discord.ui.Button
            ):
                if inter.user.id != oponente.id:
                    await inter.response.send_message(
                        "❌ Só o desafiado pode aceitar, intrometido.", ephemeral=True
                    )
                    return
                self.aceito = True
                self.stop()

                embed_prep = discord.Embed(
                    title="⚠️ PREPARAR...",
                    description="Dedos no gatilho. Leiam a cor que eu vou gritar na próxima mensagem!",
                    color=0xFF0000,
                )
                await inter.response.edit_message(embed=embed_prep, view=None)

        view = DueloAcceptView()
        await interaction.response.send_message(
            content=oponente.mention, embed=embed_convite, view=view
        )
        await view.wait()

        if view.aceito:
            # Suspense do cão
            await asyncio.sleep(random.uniform(2.0, 4.0))

            cor_certa = random.choice(["vermelho", "azul", "verde", "cinza"])

            embed_game = discord.Embed(
                title="🔫 ATIRAR!!!",
                description=f"CLICA NO BOTÃO **{cor_certa.upper()}** AGORA, SEUS LERDO!!!",
                color=0x00FF00,
            )

            game_view = DueloGameView(interaction.user, oponente, aposta, cor_certa)
            msg = await interaction.edit_original_response(
                embed=embed_game, view=game_view
            )

            await game_view.wait()
            if not game_view.clicado:
                embed_empate = discord.Embed(
                    title="🏳️ EMPATE DE XUPETAS",
                    description="Os dois dormiram no ponto. O tiroteio foi cancelado porque faltou mira.",
                    color=0x2B2D31,
                )
                await interaction.edit_original_response(embed=embed_empate, view=None)
        else:
            await interaction.edit_original_response(
                content=f"🐔 **{oponente.display_name}** arregou, meteu o pé e fugiu do x1.",
                embed=None,
                view=None,
            )

    # --- JOGO: ROLETA EXTREMA ---
    @app_commands.command(
        name="roleta_extrema",
        description="[TUDO OU NADA] Aposta todo o teu dinheiro. 50% de chance de dobrar, 50% de perder tudo.",
    )
    async def roleta_extrema(self, interaction: discord.Interaction):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT moedas FROM usuarios WHERE user_id = ?", (str(interaction.user.id),)
        )
        res = c.fetchone()
        saldo_atual = res[0] if res else 0

        if saldo_atual <= 0:
            conn.close()
            return await interaction.response.send_message(
                "❌ Ai dento! Tu já tem 0 moedas, vai apostar o quê? O caneco? Vai trampar!",
                ephemeral=True,
            )

        # bros, essa roleta é 50/50. Metade do tambor tem bala.
        sucesso = random.choice([True, False])

        if sucesso:
            c.execute(
                "UPDATE usuarios SET moedas = moedas * 2 WHERE user_id = ?",
                (str(interaction.user.id),),
            )
            novo_saldo = saldo_atual * 2
            embed = discord.Embed(
                title="🔥 MILAGRE NO VÁCUO",
                description=f"**O tambor girou e... CLIQUE! Vazia!**\n\n> Tu teve o peito de apostar tudo e a Entidade sorriu pra ti.\n> 💰 **Saldo Dobrado:** `{novo_saldo:,}` moedas.",
                color=0x00FF00,
            )
            embed.set_footer(text="Aham q lindo, agr me passa metade do lucro.")
        else:
            c.execute(
                "UPDATE usuarios SET moedas = 0 WHERE user_id = ?",
                (str(interaction.user.id),),
            )
            embed = discord.Embed(
                title="💀 F DE XUPETA",
                description=f"**O tambor girou e... BANG!**\n\n> Os teus miolos estão na parede e os bolsos vazios.\n> 📉 **Perdeu TUDO:** `{saldo_atual:,}` moedas pro ralo.",
                color=0xFF0000,
            )
            embed.set_footer(text="Volta pra CLT, liso.")

        conn.commit()
        conn.close()
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Jogos(bot))
