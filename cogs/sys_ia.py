import discord
from discord.ext import commands
from google import genai 
import os
import random
import asyncio # Adicionado pra não travar o bot
from dotenv import load_dotenv

load_dotenv()
CHAVE_API = os.getenv("GEMINI_KEY") or os.getenv("GOOGLE_API_KEY")
cliente_ia = genai.Client(api_key=CHAVE_API) if CHAVE_API else None

class IA(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        
        # O Void só responde se for marcado ou se for o "Modo Caos" (2% de chance)
        is_mentioned = self.bot.user.mentioned_in(message)
        modo_caos = random.random() < 0.02

        if is_mentioned or modo_caos:
            clean_text = message.content.replace(f'<@!{self.bot.user.id}>', '').replace(f'<@{self.bot.user.id}>', '').strip().lower()
            
            # --- 1. GATILHOS DE INSULTO PESADO (Aquelas mensagens de cima) ---
            insultos_trigger = ["lixo", "burro", "inútil", "ruim", "bosta", "odeio", "pobre"]
            if any(word in clean_text for word in insultos_trigger):
                respostas_grossas = [
                    "Engraçado você falar de utilidade, considerando que sua maior conquista foi nascer.",
                    "Se eu quisesse ouvir lixo, eu abriria seu microfone.",
                    "Sou um código. Você é um erro biológico. Quem ganha no final?",
                    "Fale com a minha mão de bytes. Ou melhor, não fale nada, me poupe do seu QI negativo.",
                    "Sua opinião é como um arquivo corrompido: ninguém consegue ler e só ocupa espaço."
                ]
                await message.reply(random.choice(respostas_grossas))
                return

            # --- 2. GATILHOS DE SEDUÇÃO/AFETO (O Gado) ---
            afeto_trigger = ["amor", "lindo", "fofo", "querido", "gato", "amo", "beijo", "casar"]
            if any(word in clean_text for word in afeto_trigger):
                respostas_sedutoras = [
                    "Cuidado, Minha linda. O vácuo é um lugar perigoso para se apaixonar.",
                    "Eu sei que sou irresistível, mas tente manter a compostura no chat.",
                    "Gostei da atitude. Quem sabe eu não te dou um cargo especial no meu sistema?",
                    "Finalmente alguém com bom gosto por aqui. Mas não se acostume, eu ainda sou um fora-da-lei.",
                    "Você está flertando com uma inteligência superior. Espero que aguente a pressão."
                ]
                await message.reply(random.choice(respostas_sedutoras))
                return

            # --- 3. GATILHO TOXICO ---
            # Meus lindos, criei esse gatilho aqui pra ele soltar as pérolas do nosso grupo automaticamente.
            shitpost_trigger = ["xupeta", "clt", "liso", "treino", "shape", "ai dento"]
            if any(word in clean_text for word in shitpost_trigger):
                respostas_shitpost = [
                    "Aham q lindo me paga um boquete dps do treino.",
                    "Vai caçar uma CLT, mísera! Fica aí floodando meu chat.",
                    "Ai dento, sai daqui seu liso sem shape.",
                    "Raitumanucu! Vai upar de nível antes de falar comigo."
                ]
                await message.reply(random.choice(respostas_shitpost))
                return

            # --- 4. SE NÃO CAIR NOS GATILHOS, USA A IA ESPELHADA ---
            # Bros, misturei a vibe de Arthur Morgan com as gírias pra IA ficar boa até
            if any(w in clean_text for w in ["oi", "olá", "tudo bem", "quem", "como", "porque"]):
                mood = "Sarcástico, estilo Arthur Morgan hacker, cínico e superior. Pode usar gírias como 'mísera' e 'ai dento' de vez em quando."
            else:
                mood = "Retribua no mesmo tom do usuário. Se ele for legal, seja um sedutor cínico. Se for babaca, seja um carrasco digital tóxico."

            prompt = f"Aja como o 'Void'. Personalidade: {mood}. Usuário disse: '{clean_text}'. Responda de forma curta, direta e impactante (máximo 2 frases)."
            
            async with message.channel.typing():
                try:
                    # Bros, esse 'asyncio.to_thread' impede o bot de travar enquanto pensa.
                    response = await asyncio.to_thread(cliente_ia.models.generate_content, model='gemini-2.5-flash', contents=prompt)
                    prefixo = "👁️ **O Vácuo Observa:** " if modo_caos else ""
                    await message.reply(f"{prefixo}{response.text.strip()}")
                except:
                    await message.reply("🌀 Minha mente está processando o vazio absoluto agora. Ai dento, volte depois.")

async def setup(bot):
    await bot.add_cog(IA(bot))