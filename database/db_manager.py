import sqlite3
import os

# Caminho dinâmico para garantir que a base de dados é guardada na pasta correta
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "assistente.db")

def inicializar_db():
    """
    Cria a base de dados e a tabela de vagas caso ainda não existam.
    """
    print("🗃️ A ligar à base de dados SQLite...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Criamos a tabela de vagas com as nossas colunas estruturadas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vagas (
            link TEXT PRIMARY KEY,
            titulo TEXT NOT NULL,
            empresa TEXT,
            localizacao TEXT,
            descricao TEXT,
            tipo_vaga TEXT,
            portal TEXT NOT NULL,
            estado_ia TEXT DEFAULT 'PENDENTE',
            data_extracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Base de dados e tabela 'vagas' prontas a usar!")

def guardar_vaga(vaga: dict) -> bool:
    """
    Tenta guardar uma vaga na base de dados.
    Devolve True se for guardada com sucesso (vaga nova).
    Devolve False se a vaga já existia (duplicada).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    sql = """
        INSERT INTO vagas (link, titulo, empresa, localizacao, descricao, tipo_vaga, portal)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    
    try:
        # Passamos os dados de forma segura (prevenindo SQL Injection)
        cursor.execute(sql, (
            vaga["link"],
            vaga["titulo"],
            vaga.get("empresa", "N/D"),
            vaga.get("localizacao", "Porto"), # Sendo a FEP, Porto por padrão
            vaga.get("descricao", ""),
            vaga.get("tipo", "N/D"),
            vaga.get("portal", "FEP") # Garante um fallback seguro para o portal
        ))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        # Este erro dispara se o link já existir (PRIMARY KEY violada)
        conn.close()
        return False

def obter_vagas_pendentes() -> list:
    """
    Retorna todas as vagas que ainda não foram avaliadas pela IA.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT link, titulo, descricao, portal FROM vagas WHERE estado_ia = 'PENDENTE'")
    linhas = cursor.fetchall()
    conn.close()
    
    vagas_pendentes = []
    for linha in linhas:
        vagas_pendentes.append({
            "link": linha[0],
            "titulo": linha[1],
            "descricao": linha[3],
            "portal": linha[2]
        })
    return vagas_pendentes

def atualizar_estado_ia(link: str, estado: str):
    """
    Atualiza o estado de triagem da IA (ex: 'RECOMENDADO' ou 'IGNORADO') de uma vaga específica.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE vagas SET estado_ia = ? WHERE link = ?", (estado, link))
    conn.commit()
    conn.close()
    print(f"   💾 Estado da vaga atualizado no SQLite para: {estado}")

if __name__ == "__main__":
    inicializar_db()