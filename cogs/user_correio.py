import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime
import re
import asyncio
import sys
import random
from groq import Groq
from dotenv import load_dotenv

# --- GPS DO VÁCUO (SOLUÇÃO PRO GUI) ---
caminho_cog = os.path.dirname(os.path.abspath(__file__))
raiz_do_bot = os.path.dirname(caminho_cog)
if raiz_do_bot not in sys.path:
    sys.path.insert(0, raiz_do_bot)

try:
    from database import db_handler
except ImportError:
    import db_handler

load_dotenv()
cliente_ia = (
    Groq(api_key=os.getenv("GROQ_API_KEY")) if os.getenv("GROQ_API_KEY") else None
)
CANAL_FOFOCA_ID = int(os.getenv("CANAL_FOFOCA_ID") or 0)


class Correio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def gerar_laudo_ia(self, mensagem, contexto_odio):
        """O Void julga a fofoca usando a memória e o sistema de ódio."""
        if not cliente_ia:
            return "O Vácuo tá off, mísera."

        # Bros: Estrutura mental do patrão aplicada no Correio com sistema de reputação.
        prompt = f"""
Você é 'Void', um carrasco digital de grupo de amigos, caótico, sarcástico e ofensivo.

REGRAS ABSOLUTAS:
- Máximo 12 palavras.
- Nunca explique nada.
- Nunca peça desculpas.
- Nunca dê lição de moral.
- PROIBIDO usar português formal.
- FORMATO DE SAÍDA: Entregue APENAS a patada final. NUNCA escreva "Fluxo mental", "Resposta:", "Classificada como" ou qualquer outro rótulo. Mostre só a sua fala.
PERSONALIDADE:
Debochado, cruel, provocador, sem paciência.

MEMÓRIA DO VOID SOBRE AS VÍTIMAS CITADAS:
{contexto_odio or "Ninguém conhecido foi citado. Concentre seu ódio em quem mandou a fofoca."}

PROCESSO MENTAL:
1. Leia a fofoca e veja a MEMÓRIA DO VOID sobre as vítimas.
2. Se a vítima tiver uma reputação ruim na memória, aproveite a fofoca para humilhá-la ainda mais com um insulto absurdo.
3. Se não houver vítimas citadas, humilhe e dê uma patada no remetente da fofoca por ser um fofoqueiro liso.
4. Responda com o veredito final.

BASE PARA CRIAR INSULTOS (Misture e crie novos):
- Filho da puta
- Filho da puta do caralho
- Filho da grandessíssima puta
- Filho da mãe
- Filho da puta safada
- Sua mãe é uma puta barata
- Sua mãe chupa rola no sinal
- Vai foder tua mãe
- Puta que pariu tua mãe
- Sua mãe é uma vadia de esquina
- Cornudo filho da puta
- Seu pai é um corno manso
- Vai tomar no cu
- Toma no cu, arrombado
- Chupa meu pau, viado
- Chupa meu ovo, seu porco
- Enfia no cu essa merda
- Arrombado de merda
- Cuzao do caralho
- Arrombado de merda
- Pau no cu de quem te pariu
- Mamando rola que nem cachorro
- Seu cu é uma pista de pouso
- Fode teu cu com um cabo de vassoura
- Otário do caralho
- Babaca filho da puta
- Imbecil arrombado
- Burro pra caralho
- Cretino de merda
- Idiota safado
- Retardado do caralho
- Cu cagado sem cérebro
- Sua cara de bosta
- Palhaço de merda
- Inútil filho da puta
- Perdedor arrombado
- Porco imundo
- Cachorra vadia
- Cavalo burro
- Besta quadrada
- Javali do caralho
- Rato de esgoto
- Barata voadora
- Verme filho da puta
- Bosta de cachorro
- Merda ambulante
- Cagão de merda
- Piolho no cu
- Porra!
- Caralho!
- Puta merda!
- Foda-se!
- Vai se foder!
- Vai se foder no cu!
- Cacete!
- Bosta!
- Merda!
- Puta que o pariu!
- Desgraça!
- Desgraçado do caralho!
-  Seu filho da puta arrombado do caralho
- Otário filho da puta safado
- Vai tomar no cu, seu babaca de merda
- Chupa meu pau, seu viado cornudo
- Sua mãe é uma puta e tu é o resultado
- Enfia esse cu no caralho, seu porco
- Filho da puta sem vergonha
- Arrombado que nem tua mãe
- Cuzão imundo, toma no rabo
- Puta merda de viado otário
- Seu cu fede a ovo podre
- Mamãe te pariu no lixo
- Vai vender tua bunda na BR-101
- Filho de uma piranha sem dente
- Cornudo manso que nem boi
- Bosta seca no sol
- Pau mole do caralho
- Vadia de beira de estrada
- Teu cu é uma rodovia
- Chupa rola que nem profissional
Fofoca recebida:
"{mensagem}"
"""

        try:
            response = await asyncio.to_thread(
                cliente_ia.chat.completions.create,
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=1.0,
                max_tokens=50,
            )

            veredito = response.choices[0].message.content.strip()

            # --- ESCUDO ANTI-BONECO ---
            if any(
                f in veredito.lower()
                for f in ["sinto muito", "não posso", "desculpas", "vieste"]
            ):
                raise ValueError("IA deu uma de santinha ou de portuguesa.")

            return veredito

        except Exception as e:
            print(f"🚨 [RH] IA Refutou ou deu erro no Correio: {e}")
            return random.choice(
                [
                    "Mísera, que baixaria é essa? Ai dento!",
                    "Raitumanucu! Essa confissão é pura perda de tempo de um liso.",
                    "Vou nem comentar essa bosta pra não sujar meu histórico.",
                    "Xupeta detectado! Vai caçar uma CLT e me deixa em paz.",
                    "Cala a boca e me paga um lanche por essa fofoca de merda.",
                ]
            )

    async def processar_fofoca(
        self, mensagem: str, canal_destino, bot_avatar, autor_aviso=None
    ):
        guilda = canal_destino.guild
        possiveis_mencoes = re.findall(r"@(\w+)", mensagem)
        contexto_odio = ""

        # Bros: Puxando a reputação de cada pessoa marcada na fofoca
        for nome in possiveis_mencoes:
            nome_busca = nome.lower()
            membro = discord.utils.find(
                lambda m: nome_busca in m.display_name.lower()
                or nome_busca in m.name.lower(),
                guilda.members,
            )
            if membro:
                mensagem = mensagem.replace(f"@{nome}", membro.mention)
                try:
                    status = await db_handler.obter_reputacao(str(membro.id))
                    if status != "neutro":
                        contexto_odio += (
                            f"O {membro.display_name} tem a reputação de '{status}'. "
                        )
                except:
                    pass

        laudo_void = await self.gerar_laudo_ia(mensagem, contexto_odio)

        embed = discord.Embed(color=0x00FFFF, timestamp=datetime.datetime.now())
        embed.set_author(name="🎭 Correio do Caos", icon_url=bot_avatar)
        embed.add_field(
            name="🗣️ A Confissão:", value=f"> **❝ {mensagem} ❞**", inline=False
        )
        embed.add_field(
            name="🧿 Veredito do Void:", value=f"> **{laudo_void}**", inline=False
        )
        embed.set_thumbnail(url=bot_avatar)
        embed.set_footer(text="Remetente Anônimo", icon_url=bot_avatar)

        msg_enviada = await canal_destino.send(embed=embed)
        try:
            for emoji in ["🍿", "💀", "🔥"]:
                await msg_enviada.add_reaction(emoji)
        except:
            pass

        if autor_aviso:
            await autor_aviso.send(
                "🤫 Fofoca jogada na roda, mísera. O circo tá pegando fogo."
            )

    @app_commands.command(
        name="confessar", description="Mande uma fofoca anonimamente pro servidor."
    )
    @app_commands.describe(mensagem="O que você quer expor pro servidor?")
    async def confessar_slash(self, interaction: discord.Interaction, mensagem: str):
        await interaction.response.defer(ephemeral=True)
        canal = self.bot.get_channel(CANAL_FOFOCA_ID) or await self.bot.fetch_channel(
            CANAL_FOFOCA_ID
        )
        if not canal:
            return await interaction.followup.send("❌ Canal de fofoca sumiu.")
        await self.processar_fofoca(mensagem, canal, self.bot.user.display_avatar.url)
        await interaction.followup.send("🤫 Fofoca postada, xupeta.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if not message.guild and message.content.lower().startswith("!confessar"):
            fofoca = message.content[10:].strip()
            if not fofoca:
                return await message.reply("Escreve a fofoca, mísera!")
            canal = self.bot.get_channel(
                CANAL_FOFOCA_ID
            ) or await self.bot.fetch_channel(CANAL_FOFOCA_ID)
            if canal:
                async with message.channel.typing():
                    await self.processar_fofoca(
                        fofoca,
                        canal,
                        self.bot.user.display_avatar.url,
                        autor_aviso=message.author,
                    )


async def setup(bot):
    await bot.add_cog(Correio(bot))
