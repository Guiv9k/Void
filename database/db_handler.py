import sqlite3
import os
import asyncio
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bot_data.db")


def setup_db():
    """Inicializa o banco de dados e as tabelas necessárias."""
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabela de Usuários (XP, Nível, Moedas, Casamento)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            user_id TEXT PRIMARY KEY,
            xp INTEGER DEFAULT 0,
            nivel INTEGER DEFAULT 1,
            moedas INTEGER DEFAULT 0,
            conjuge TEXT,
            data_casamento TEXT,
            escudo_ate TEXT,
            tempo_voz INTEGER DEFAULT 0
        )
    """)

    # Tabela de Memória da IA (Usado pelo Correio e Chat)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memoria_ia (
            user_id TEXT PRIMARY KEY, 
            reputacao_ia TEXT DEFAULT 'neutro'
        )
    """)

    # Tabelas Extras (Facções e Recompensas)
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS faccoes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE, dono_id TEXT, caixa INTEGER DEFAULT 0, nivel INTEGER DEFAULT 1)"
    )
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS recompensas (alvo_id TEXT PRIMARY KEY, contratante_id TEXT, valor INTEGER)"
    )

    conn.commit()
    conn.close()
    print("🧠 [DB] Serasa do Vácuo Online: XP 500 flat e tabelas sincronizadas!")


# =========================================================================
# LÓGICA DE XP (REGRA 3: SEM TRAVAR O BOT)
# =========================================================================


def _adicionar_xp_sync(user_id, quantidade):
    """Soma XP, aplica buff de gado (casamento) e sobe de nível."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO usuarios (user_id) VALUES (?)", (str(user_id),)
        )

        cursor.execute(
            "SELECT xp, nivel, conjuge FROM usuarios WHERE user_id = ? LIMIT 1",
            (str(user_id),),
        )
        xp_atual, nivel_atual, conjuge = cursor.fetchone()

        # Buff de Casamento: +50% de XP
        if conjuge:
            quantidade = int(quantidade * 1.5)

        novo_xp = xp_atual + quantidade
        novo_nivel = nivel_atual
        upou = False

        # Regra do Projeto: 500 XP fixo para subir de nível
        while novo_xp >= 500:
            novo_xp -= 500
            novo_nivel += 1
            upou = True

        cursor.execute(
            "UPDATE usuarios SET xp = ?, nivel = ? WHERE user_id = ?",
            (novo_xp, novo_nivel, str(user_id)),
        )
        conn.commit()
        return upou, novo_nivel


async def adicionar_xp(user_id, quantidade=20):
    """Versão assíncrona para ser chamada nos Cogs."""
    return await asyncio.to_thread(_adicionar_xp_sync, user_id, quantidade)


def _obter_dados_sync(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM usuarios WHERE user_id = ? LIMIT 1", (str(user_id),)
        )
        return cursor.fetchone()


async def obter_dados_usuario(user_id):
    """Puxa o perfil completo do usuário no banco."""
    return await asyncio.to_thread(_obter_dados_sync, user_id)


def _obter_reputacao_sync(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT reputacao_ia FROM memoria_ia WHERE user_id = ? LIMIT 1",
            (str(user_id),),
        )
        res = c.fetchone()
        return res[0] if res else "neutro"


async def obter_reputacao(user_id):
    """Puxa o laudo psiquiátrico que o Correio usa para julgar fofocas."""
    return await asyncio.to_thread(_obter_reputacao_sync, user_id)
