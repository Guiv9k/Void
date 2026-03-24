import sqlite3
import os

DB_PATH = "database/bot_data.db"

def setup_db():
    # Cria a pasta do banco de dados se algum xupeta tiver apagado sem querer
    if not os.path.exists('database'):
        os.makedirs('database')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- 1. TABELA PRINCIPAL DO AGIOTA (USUÁRIOS) ---
    cursor.execute('''
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
    ''')

    # --- 2. GARANTIR COLUNAS NOVAS (Atualização Segura) ---
    # Bros, isso aqui garante que se tu já tiver um DB antigo, ele não apaga nada, só adiciona as novidades.
    novas_colunas = [
        ("conjuge", "TEXT"),
        ("data_casamento", "TEXT"),
        ("escudo_ate", "TEXT"),
        ("tempo_voz", "INTEGER DEFAULT 0")
    ]
    for nome, tipo in novas_colunas:
        try:
            cursor.execute(f"ALTER TABLE usuarios ADD COLUMN {nome} {tipo}")
        except sqlite3.OperationalError:
            pass # Se a coluna já existir, o bot ignora e segue a vida

    # --- 3. TABELAS SECUNDÁRIAS DOS SISTEMAS ---
    
    # Tabela das Facções (O Cartel dos CLTs)
    cursor.execute('''CREATE TABLE IF NOT EXISTS faccoes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE, dono_id TEXT, caixa INTEGER DEFAULT 0, nivel INTEGER DEFAULT 1)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS membros_faccao (user_id TEXT PRIMARY KEY, faccao_id INTEGER)''')

    # Tabela de Caça a Recompensas (Mercenários)
    cursor.execute('''CREATE TABLE IF NOT EXISTS recompensas (alvo_id TEXT PRIMARY KEY, contratante_id TEXT, valor INTEGER)''')
    
    # Tabela de Pérolas 
    cursor.execute('''CREATE TABLE IF NOT EXISTS quotes (user_id TEXT, frase TEXT, data TEXT)''')
    
    # Tabela do Painel Automático (Ranking invisível que atualiza sozinho)
    cursor.execute('''CREATE TABLE IF NOT EXISTS paineis (tipo TEXT PRIMARY KEY, canal_id TEXT, mensagem_id TEXT)''')
    
    # Tabela do Tribunal (Reputação / Laudo Psiquiátrico)
    cursor.execute('''CREATE TABLE IF NOT EXISTS reputacao (user_id TEXT, categoria TEXT, quantidade INTEGER, UNIQUE(user_id, categoria))''')
    
    # Tabela de Estatísticas (O Exame Toxicológico de palavras)
    cursor.execute('''CREATE TABLE IF NOT EXISTS stats (user_id TEXT, palavra TEXT, data TEXT)''')

    # Tabela de Conquistas (Aparece lá no /perfil)
    cursor.execute('''CREATE TABLE IF NOT EXISTS conquistas (user_id TEXT, conquista TEXT)''')

    conn.commit()
    conn.close()
    
    # Mensagem pro terminal avisando que a base tá pronta
    print("🧠 [DB] Serasa do Vácuo online: Todas as tabelas e colunas sincronizadas pro Agiota trabalhar!")