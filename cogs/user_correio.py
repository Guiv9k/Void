import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime
import re
import sqlite3
from google import genai
from dotenv import load_dotenv

load_dotenv()

# BRos, não mexe nisso aqui pelo amor de deus, é o que liga a IA do bot.
CHAVE_API = os.getenv("GEMINI_KEY") or os.getenv("GOOGLE_API_KEY")
cliente_ia = genai.Client(api_key=CHAVE_API) if CHAVE_API else None

CANAL_FOFOCA_ID = int(os.getenv("CANAL_FOFOCA_ID"))
DB_PATH = "database/bot_data.db"

class Correio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def gerar_laudo_ia(self, mensagem, contexto_odio):
        if not cliente_ia: return "O Vácuo tá off, mísera. Faltou luz no barraco da IA."
        
        # Minha linda, olha esse prompt novo. Tirei todo aquele papo chato de academia.
        # Agora o Void é puramente um tóxico e debochado, usando as nossas gírias, vcs podem mudar tbm.
        prompt = (
            "Aja como o 'Void', um bot de Discord que é um 'Shitposter Tóxico e Debochado'. "
            "Você é sem filtro, aleatório, direto e adora zoar. Use gírias como: 'mísera', 'ai dento', 'raitumanucu', 'xupeta' (para quem é besta), 'minha linda', 'meu lindo', 'meu bem', 'gatinha'. "
            "De vez em quando, solte uma cantada absurda e aleatória do nada (tipo 'aham q lindo me paga um ... dps'). "
            "NADA DE PALAVRAS DIFÍCEIS ou textão. Fale como a galera do shitpost e memes do Discord.\n"
            f"Fofoca recebida: '{mensagem}'.\n"
            f"O que você acha das pessoas citadas (reputação no banco): {contexto_odio}\n\n"
            "Regra: Escreva APENAS 1 ou 2 frases. Seja MUITO na cara e julgador. Se odeia (inimigo) a pessoa citada, detone ela chamando de liso e xupeta. Se gosta (aliado), passe pano com deboche."
        )
        
        try:
            response = cliente_ia.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            return response.text.strip()
        except:
            return "Mais uma fofoca inútil desse xupeta anotada."

    async def processar_fofoca(self, mensagem: str, canal_destino, bot_avatar, autor_aviso=None):
        guilda = canal_destino.guild
        possiveis_mencoes = re.findall(r'@(\w+)', mensagem)
        
        contexto_odio = ""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Meus lindos, essa parte puxa os arrobas e vê se o bot odeia o cara no banco de dados. 
        for nome in possiveis_mencoes:
            nome_busca = nome.lower()
            membro_encontrado = discord.utils.find(
                lambda m: nome_busca in m.display_name.lower() or nome_busca in m.name.lower(), 
                guilda.members
            )
            
            if membro_encontrado:
                mensagem = mensagem.replace(f"@{nome}", membro_encontrado.mention)
                
                try:
                    c.execute("SELECT reputacao_ia FROM memoria_ia WHERE user_id = ?", (str(membro_encontrado.id),))
                    res = c.fetchone()
                    status = res[0] if res else "neutro"
                    contexto_odio += f"Você acha que o {membro_encontrado.display_name} é um '{status}'. "
                except: pass
        conn.close()

        if not contexto_odio:
            contexto_odio = "Você não tem opinião formada sobre os citados. Apenas julgue a fofoca em si, sem pena."

        # Passa o contexto de ódio pra IA gerar o deboche
        laudo_void = await self.gerar_laudo_ia(mensagem, contexto_odio)

        # Bros, deixei o embed com essa corzinha cyano, se quiser trocar dps fica à vontade.
        embed = discord.Embed(color=0x00FFFF, timestamp=datetime.datetime.now())
        embed.set_author(name="🎭 Correio do Caos", icon_url=bot_avatar)
        embed.add_field(name="🗣️ A Confissão:", value=f"> **❝ {mensagem} ❞**", inline=False)
        embed.add_field(name="🧿 Veredito do Maromba Cósmico:", value=f"> **{laudo_void}**", inline=False) # Mantive o nome do campo pra zoeira
        embed.set_thumbnail(url=bot_avatar)
        embed.set_footer(text="Remetente Anônimo • ID Oculto", icon_url=bot_avatar)

        msg_enviada = await canal_destino.send(embed=embed)

        try:
            for emoji in ["🍿", "💀", "🔥"]:
                await msg_enviada.add_reaction(emoji)
        except: pass
            
        if autor_aviso:
            await autor_aviso.send("🤫 Fofoca jogada na roda, mísera. Vai lá ver a desgraça acontecer.")

    @app_commands.command(name="confessar", description="Mande uma fofoca anonimamente pro servidor.")
    @app_commands.describe(mensagem="O que você quer expor pro servidor?")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True) 
    async def confessar_slash(self, interaction: discord.Interaction, mensagem: str):
        await interaction.response.defer(ephemeral=True)
        canal_destino = self.bot.get_channel(CANAL_FOFOCA_ID) or await self.bot.fetch_channel(CANAL_FOFOCA_ID)
        
        if not canal_destino:
            await interaction.followup.send("❌ Ai dento, não achei o canal de fofoca. Vê se o ID tá certo, meu bem.", ephemeral=True)
            return
            
        await self.processar_fofoca(mensagem, canal_destino, self.bot.user.display_avatar.url)
        await interaction.followup.send("🤫 Fofoca postada, xupeta.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        
        # Meus lindos, esse aqui é o comando pela DM. Se mandarem !confessar no privado do bot, ele posta tbm.
        if not message.guild and message.content.lower().startswith("!confessar"):
            fofoca = message.content[10:].strip()
            if not fofoca: return
            
            canal_destino = self.bot.get_channel(CANAL_FOFOCA_ID) or await self.bot.fetch_channel(CANAL_FOFOCA_ID)
            if not canal_destino: return
            
            async with message.channel.typing():
                await self.processar_fofoca(fofoca, canal_destino, self.bot.user.display_avatar.url, autor_aviso=message.author)

async def setup(bot):
    await bot.add_cog(Correio(bot))