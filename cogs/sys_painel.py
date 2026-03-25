import discord
from discord.ext import commands, tasks
from discord import app_commands
import sqlite3
import datetime

DB_PATH = "database/bot_data.db"


class Painel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.preparar_banco()
        # Pup Minha linda, o cronômetro liga sozinho aqui. Não precisa dar comando de start.
        self.loop_paineis.start()

    def cog_unload(self):
        # Bros, isso aqui evita do bot bugar e rodar dois cronômetros juntos se a gente reiniciar o arquivo.
        self.loop_paineis.cancel()

    def preparar_banco(self):
        # Cria uma tabela só para lembrar onde estão as mensagens dos painéis
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS paineis
                     (tipo TEXT PRIMARY KEY, canal_id TEXT, mensagem_id TEXT)""")
        conn.commit()
        conn.close()

    def formatar_tempo(self, minutos_totais):
        horas = minutos_totais // 60
        minutos = minutos_totais % 60
        if horas > 0:
            return f"{horas}h {minutos}m"
        return f"{minutos}m"

    # --- GERADORES DE VISUAL ---
    async def gerar_embed_xp(self, guilda):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Puxa o Top 10 pra expor quem não trabalha
        c.execute(
            "SELECT user_id, xp, nivel FROM usuarios ORDER BY nivel DESC, xp DESC LIMIT 10"
        )
        top_10 = c.fetchall()
        conn.close()

        embed = discord.Embed(
            title="🏆 RANKING DOS DESOCUPADOS (XP)",
            color=0x8A2BE2,
            timestamp=datetime.datetime.now(),
        )
        texto = ""
        for i, user_data in enumerate(top_10):
            uid, xp, nivel = int(user_data[0]), user_data[1], user_data[2]
            membro = guilda.get_member(uid)
            nome = membro.display_name if membro else f"Fugitivo ({uid})"
            rank = i + 1
            icone = (
                "🥇"
                if rank == 1
                else "🥈" if rank == 2 else "🥉" if rank == 3 else "💀"
            )
            texto += f"> **{icone} #{rank}** | 👤 **{nome}**\n> 🧬 Nível: `{nivel}` | ✨ XP: `{xp:,}`\n> ───────────────\n"

        embed.description = (
            texto if texto else "Ninguém upou nada ainda. Bando de CLT ocupado."
        )
        embed.set_footer(
            text="Atualizado a cada 10 min pra expor viciado",
            icon_url=self.bot.user.display_avatar.url,
        )
        return embed

    async def gerar_embed_voz(self, guilda):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT user_id, tempo_voz FROM usuarios WHERE tempo_voz > 0 ORDER BY tempo_voz DESC LIMIT 10"
        )
        top_10 = c.fetchall()
        conn.close()

        embed = discord.Embed(
            title="🎙️ RANKING DOS ZÉ RADINHO (CALL)",
            color=0x00FFFF,
            timestamp=datetime.datetime.now(),
        )
        texto = ""
        for i, user_data in enumerate(top_10):
            uid, tempo = int(user_data[0]), user_data[1]
            membro = guilda.get_member(uid)
            nome = membro.display_name if membro else f"Fugitivo ({uid})"
            rank = i + 1
            icone = (
                "🎧"
                if rank == 1
                else "🥈" if rank == 2 else "🥉" if rank == 3 else "🎙️"
            )
            texto += f"> **{icone} #{rank}** | 👤 **{nome}**\n> ⏳ Tempo de Fofoca: `{self.formatar_tempo(tempo)}`\n> ───────────────\n"

        embed.description = (
            texto
            if texto
            else "Ninguém entrou em call. Bando de antissocial do caralho."
        )
        embed.set_footer(
            text="Atualizado a cada 10 min", icon_url=self.bot.user.display_avatar.url
        )
        return embed

    # --- COMANDO PARA CRIAR O PAINEL (Só Admins) ---
    @app_commands.command(
        name="criar_painel",
        description="[ADMIN] Cria a mensagem fixa do placar que atualiza sozinha.",
    )
    @app_commands.choices(
        tipo=[
            app_commands.Choice(name="Mural de XP", value="xp"),
            app_commands.Choice(name="Mural de Call (Voz)", value="voz"),
        ]
    )
    @app_commands.default_permissions(administrator=True)  # Trava o comando só pra você
    async def criar_painel(
        self, interaction: discord.Interaction, tipo: app_commands.Choice[str]
    ):
        await interaction.response.defer(ephemeral=True)

        embed = (
            await self.gerar_embed_xp(interaction.guild)
            if tipo.value == "xp"
            else await self.gerar_embed_voz(interaction.guild)
        )

        # O bot manda a primeira mensagem no canal onde você digitou o comando
        msg = await interaction.channel.send(embed=embed)

        # Salva o ID da mensagem no banco de dados pra ele lembrar onde editar depois
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # REPLACE garante que se você rodar de novo, ele esquece o painel velho e foca no novo
        c.execute(
            "REPLACE INTO paineis (tipo, canal_id, mensagem_id) VALUES (?, ?, ?)",
            (tipo.value, str(interaction.channel.id), str(msg.id)),
        )
        conn.commit()
        conn.close()

        # Meu nobre, mensagem de sucesso braba aqui
        await interaction.followup.send(
            f"✅ Painel de {tipo.name} plantado com sucesso, meu nobre! Agora os xupetas podem ver quem é o mais desocupado. Eu atualizo sozinho.",
            ephemeral=True,
        )

    # --- O MOTOR QUE RODA DE 10 EM 10 MINUTOS ---
    @tasks.loop(minutes=10)
    async def loop_paineis(self):
        # Espera o bot terminar de ligar antes de tentar atualizar
        await self.bot.wait_until_ready()

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT tipo, canal_id, mensagem_id FROM paineis")
        paineis = c.fetchall()
        conn.close()

        for tipo, canal_id, msg_id in paineis:
            # Acha o canal
            canal = self.bot.get_channel(int(canal_id))
            if not canal:
                try:
                    canal = await self.bot.fetch_channel(int(canal_id))
                except:
                    continue

            # Acha a mensagem e edita ela
            try:
                msg = await canal.fetch_message(int(msg_id))
                novo_embed = (
                    await self.gerar_embed_xp(canal.guild)
                    if tipo == "xp"
                    else await self.gerar_embed_voz(canal.guild)
                )
                await msg.edit(embed=novo_embed)  # É AQUI QUE A MÁGICA ACONTECE!
            except discord.NotFound:
                # BRos, se apagarem a mensagem do painel lá no Discord, o bot percebe e não crasha a thread.
                print(
                    f"⚠️ Vish, algum corno apagou o painel de {tipo} no chat. Cria de novo dps com o comando."
                )
            except Exception as e:
                print(f"⚠️ Erro ao atualizar painel invisível ({tipo}): {e}")


async def setup(bot):
    await bot.add_cog(Painel(bot))
