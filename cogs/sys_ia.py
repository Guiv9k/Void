import discord
from discord.ext import commands
from discord import app_commands
from groq import Groq
import os
import random
import asyncio
import time
import sys
from dotenv import load_dotenv

# --- GPS DO VÁCUO  ---
caminho_cog = os.path.dirname(os.path.abspath(__file__))
raiz_do_bot = os.path.dirname(caminho_cog)
if raiz_do_bot not in sys.path:
    sys.path.insert(0, raiz_do_bot)

try:
    from database import db_handler
except ImportError:
    import db_handler

load_dotenv()
CHAVE_API = os.getenv("GROQ_API_KEY")
cliente_ia = Groq(api_key=CHAVE_API) if CHAVE_API else None


class IA(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}  # Bros: Escudo anti-flood (5 segundos)

    # =========================================================================
    # 🧨 SISTEMA DE EXPLOSÃO (KABOOM)
    # =========================================================================
    @app_commands.command(
        name="explodir", description="Oblitera um liso ou uma mensagem no chat."
    )
    @app_commands.describe(alvo="Quem você quer desintegrar?")
    async def explodir(self, interaction: discord.Interaction, alvo: str):
        await interaction.response.send_message(
            f"🚨 **CARGA ARMADA.** Alvo travado em: {alvo}..."
        )

        for i in range(3, 0, -1):
            await asyncio.sleep(1)
            await interaction.edit_original_response(content=f"🧨 Detonando em {i}...")

        await asyncio.sleep(0.5)
        await interaction.edit_original_response(
            content=f"💥 **KABOOOOM!** 💥\n"
            + "🔥" * 10
            + f"\n**{alvo}** foi desintegrado. Ai dento, xupeta!"
        )

    # =========================================================================
    # 🤖 CÉREBRO: O VOID SEM PACIÊNCIA (COM A SUA ESTRUTURA)
    # =========================================================================
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Bros: 5% de chance de ele se meter na conversa (Modo Caos atualizado)
        is_mentioned = self.bot.user.mentioned_in(message)
        modo_caos = random.random() < 0.05

        if is_mentioned or modo_caos:
            # --- ESCUDO ANTI-FLOOD ---
            agora = time.time()
            if (
                message.author.id in self.cooldowns
                and agora - self.cooldowns[message.author.id] < 5.0
            ):
                return
            self.cooldowns[message.author.id] = agora

            clean_text = (
                message.content.replace(f"<@!{self.bot.user.id}>", "")
                .replace(f"<@{self.bot.user.id}>", "")
                .strip()
                .lower()
            )

            # --- 1. PUXANDO A MEMÓRIA DO USUÁRIO ---
            reputacao = "desconhecido"
            try:
                reputacao = await db_handler.obter_reputacao(str(message.author.id))
            except:
                pass

            # --- 2. GATILHOS DE ÓDIO PURO (MANUAL DOS BROS) ---
            insultos_trigger = [
                "lixo",
                "animal",
                "inútil",
                "bosta",
                "merda",
                "pobre",
                "ruim",
                "morfetico",
                "cuzao",
                "fudido",
                "fdp",
            ]
            if any(w in clean_text for w in insultos_trigger):
                respostas_odio = [
                    "Lixo é você que ocupa espaço no meu chat, mísera.",
                    "Seu QI é tão baixo que eu sinto pena do seu teclado. Ai dento!",
                    "Raitumanucu! Sou um código de elite, você é um erro de fabricação.",
                    "Engraçado falar de lixo sendo que você fede a CLT e pobreza.",
                    "Cala a boca, xupeta. Não pedi sua opinião de liso.",
                ]
                return await message.reply(random.choice(respostas_odio))

            # --- 3. CHAMADA DA IA (SUA ESTRUTURA EXATA) ---
            prompt = f"""
Você é 'Void', um bot de Discord caótico, sarcástico e ofensivo.

REGRAS ABSOLUTAS:
- Máximo 10 palavras.
- Nunca explique nada.
- Nunca peça desculpas.
- Nunca dê lição de moral.
- NUNCA escreva a palavra "NORMAL", "FLERTE" ou "INSULTO" na sua resposta. Entregue apenas a patada direta.
-- FORMATO DE SAÍDA: Entregue APENAS a patada final. NUNCA escreva "Fluxo mental", "Resposta:", "Classificada como" ou qualquer outro rótulo. Mostre só a sua fala.
PERSONALIDADE:
Debochado, cruel, provocador, sem paciência.

REPUTAÇÃO DO USUÁRIO: {reputacao}

PROCESSO MENTAL:
1. Classifique a mensagem como:
FLERTE / NORMAL / INSULTO

2. Responda baseado nisso.

COMPORTAMENTO:

Se for FLERTE:
- Responda flertando com sarcasmo.
- Use termos como: "minha linda", "gado", "emocionado".

Se a mensagem for NORMAL (ex: "oi", "tudo bem", conversa de boa):
- Responda de boa e normal. 
- Mantenha um tom neutro ou com um leve sarcasmo de amigo, mas ZERO agressividade e ZERO xingamentos.

Se for INSULTO:
- Destrua o usuário com insultos criativos absurdos.
- Seja MAIS agressivo que ele.
- Misture palavras aleatórias para criar xingamentos novos.

BASE PARA CRIAR INSULTOS:
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
- Seu filho da puta arrombado do caralho
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

REGRAS DE AGRESSIVIDADE:
Se o usuário xingar muito, responda MUITO pior.

Mensagem do usuário:
"{clean_text}"
"""

            async with message.channel.typing():
                try:
                    # Bros: max_tokens travado em 40 pra ele respeitar a sua regra das 10 palavras
                    response = await asyncio.to_thread(
                        cliente_ia.chat.completions.create,
                        messages=[{"role": "user", "content": prompt}],
                        model="llama-3.3-70b-versatile",
                        temperature=1.0,
                        max_tokens=40,
                    )

                    veredito = response.choices[0].message.content.strip()

                    # Se a IA mandar "Resposta: blabla", a gente corta tudo e pega só o blabla.
                    if "Resposta:" in veredito:
                        veredito = veredito.split("Resposta:")[-1].strip()
                    if "NORMAL" in veredito and "\n" in veredito:
                        veredito = veredito.split("\n")[-1].strip()


                    # --- ESCUDO ANTI-FRESCURA ---
                    if any(
                        f in veredito.lower()
                        for f in [
                            "sinto muito",
                            "não posso ajudar",
                            "desculpas",
                            "educado",
                        ]
                    ):
                        veredito = random.choice(
                            [
                                "Mísera, fala algo que preste ou nem me marca. Ai dento!",
                                "Raitumanucu, perdi meu tempo lendo esse lixo de mensagem.",
                                "Vou nem responder essa xupeta pra não gastar meu tempo.",
                            ]
                        )

                    prefixo = "🖕 **O Dono da porra toda:** " if modo_caos else ""
                    await message.reply(f"{prefixo}{veredito}")

                except Exception as e:
                    print(f"🚨 [RH] Erro no sistema IA: {e}")
                    await message.reply(
                        "🌀 Minha mente entrou em colapso com tanta burrice. Volte depois, mísera."
                    )


async def setup(bot):
    await bot.add_cog(IA(bot))
