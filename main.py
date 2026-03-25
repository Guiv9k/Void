import discord
from discord.ext import commands, tasks
import os
import random
import asyncio
from dotenv import load_dotenv
from database.db_handler import setup_db

# --- NOTA DO GUI ---
# Bros, esse é o coração do Void.
# Eu que organizei a estrutura pra carregar tudo automático nessa bomba
# Cuidado ao mexer na ordem do setup_db se não o banco explode KKKKKKKKKKKKKKKKK
# ------------------

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.all()


class VoidBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Pup Minha linda,eu deixei o cérebro do banco ligado aqui primeiro.
        setup_db()

        print("=" * 50)
        print("💀 INICIANDO O PROTOCOLO AGIOTA...")
        print("=" * 50)

        # Bros, eu fiz esse loop pra gente não ter que importar cog por cog.
        # É só jogar o arquivo .py na pasta cogs e o py aqui puxa sozinho.
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and filename != "__init__.py":
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"✅ [Sistema Injetado] -> {filename}")
                except Exception as e:
                    print(
                        f"❌ [ERRO CRÍTICO] O Gui avisou que deu ruim no {filename}: {e}"
                    )
        print("=" * 50)

        # Inicia o balãozinho de fala
        self.mudar_status_balao.start()

    # --- STATUS PERSONALIZADO (O BALÃOZINHO DO GUI) ---
    @tasks.loop(seconds=5)
    async def mudar_status_balao(self):
        # Vcs podem mudar isso pra oq vcs quiser
        frases_balao = [
            "Gui me deve 50k, não confiem nele.",
            "Marcele é Mestre a cumputaria.",
            "Artur liberou o acesso do Serasa.",
            "By: Gui, Marcele e Artur.",
            "Passa o daily senão o Gui te quebra.",
            "Marcele tá Clonado teu cpf.",
            "Artur Morgan hackeou seu IP.",
            "O Gui tentou me vender por um Marea Turbo.",
        ]

        try:
            # aq foi 100% no balão (CustomActivity) pra estética ficar clean
            status_balao = discord.CustomActivity(name=random.choice(frases_balao))

            await self.change_presence(
                status=discord.Status.do_not_disturb, activity=status_balao
            )
        except Exception as e:
            print(f"⚠️ Erro no balão do Gui: {e}")

    @mudar_status_balao.before_loop
    async def antes_do_status(self):
        await self.wait_until_ready()


# Inicializa o Bot do Gui
bot = VoidBot()


@bot.event
async def on_ready():
    # Sincronização rápida
    guild = discord.Object(id=GUILD_ID)
    print("🔄 Sincronizando comandos de elite...")

    try:
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)

        print("=" * 50)
        print(f"👁️ O VÁCUO TE OBSERVA: {bot.user} tá online!")
        print(f"🚀 {len(synced)} comandos do Gui prontos pro crime!")
        print("=" * 50)
    except Exception as e:
        print(f"❌ Falha na sincronização do Gui: {e}")


if __name__ == "__main__":
    bot.run(TOKEN)
