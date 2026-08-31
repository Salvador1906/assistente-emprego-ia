import os
import sqlite3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header

# Tentamos carregar as variáveis do ficheiro .env se a biblioteca python-dotenv estiver instalada
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configurações de Caminhos (compatível com Mac/Windows/Linux)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def encontrar_db_e_tabela():
    """Busca dinamicamente o arquivo de banco de dados e a tabela correta."""
    caminhos_possiveis = [
        os.path.join(BASE_DIR, "database", "assistente.db"),
        os.path.join(BASE_DIR, "assistente.db"),
        os.path.join(BASE_DIR, "database", "vagas.db"),
        os.path.join(BASE_DIR, "vagas.db"),
    ]
    
    # Tenta importar as configurações oficiais do db_manager do projeto do Salvador
    try:
        from database.db_manager import DB_PATH as DB_PATH_MANAGER
        if DB_PATH_MANAGER not in caminhos_possiveis:
            caminhos_possiveis.append(DB_PATH_MANAGER)
    except Exception:
        pass

    db_valido = None
    tabela_valida = None
    tabelas_encontradas_geral = []
    
    for caminho in caminhos_possiveis:
        if not caminho or not os.path.exists(caminho):
            continue
            
        try:
            conn = sqlite3.connect(caminho)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tabelas = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            tabelas_encontradas_geral.extend([(caminho, t) for t in tabelas])
            
            # Procuramos por tabelas prováveis que guardam vagas
            for tab in ["anuncios_processados", "vagas", "anuncios"]:
                if tab in tabelas:
                    db_valido = caminho
                    tabela_valida = tab
                    break
            
            if db_valido:
                break
        except Exception:
            continue
            
    return db_valido, tabela_valida, caminhos_possiveis, tabelas_encontradas_geral

# Inicializamos a busca do banco e tabela
DB_PATH, TABELA_VAGAS, CAMINHOS_SCANNED, TABELAS_SCANNED = encontrar_db_e_tabela()

def garantir_coluna_notificado(conn):
    """Garante de forma robusta que a coluna 'notificado' existe na tabela de vagas."""
    if not TABELA_VAGAS:
        return
        
    cursor = conn.cursor()
    try:
        # Tenta verificar se a coluna já existe
        cursor.execute(f"SELECT notificado FROM {TABELA_VAGAS} LIMIT 1")
    except sqlite3.OperationalError:
        # Se a coluna não existe, vamos adicioná-la
        print(f"🔧 A adicionar a coluna 'notificado' à tabela '{TABELA_VAGAS}' para controlo de envios...")
        try:
            cursor.execute(f"ALTER TABLE {TABELA_VAGAS} ADD COLUMN notificado INTEGER DEFAULT 0")
            conn.commit()
            print("✅ Coluna 'notificado' adicionada com sucesso!")
        except Exception as e:
            print(f"⚠️ Erro ao adicionar coluna: {e}")

def obter_vagas_recomendadas():
    """Recupera as vagas marcadas como RECOMENDADO pela IA e que ainda não foram enviadas."""

    # 🔥 MODO DE TESTE TEMPORÁRIO PARA FORÇAR ENVIO NA NUVEM 🔥
    return [{
        "titulo": "Estágio Júnior em Análise de Dados Financeiros (FEP Teste)",
        "portal": "FEP Career Portal",
        "link": "https://www.fep.up.pt",
        "descricao": "Vaga de teste gerada automaticamente para validar a integração do GitHub Actions com o Gmail do Salvador!"
    }]

    if not DB_PATH or not TABELA_VAGAS:
        print("❌ Erro: Não foi possível localizar a base de dados ou a tabela de vagas activa.")
        print("💡 Diagnóstico de caminhos verificados:")
        for idx, cam in enumerate(CAMINHOS_SCANNED, 1):
            status = "Existe" if os.path.exists(cam) else "Não existe"
            print(f"   [{idx}] {cam} ({status})")
        if TABELAS_SCANNED:
            print("💡 Tabelas encontradas nos arquivos existentes:")
            for cam, tab in TABELAS_SCANNED:
                print(f"   - Arquivo: {os.path.basename(cam)} | Tabela: {tab}")
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permite aceder às colunas pelo nome (ex: vaga['titulo'])
    garantir_coluna_notificado(conn)
    
    cursor = conn.cursor()
    # Selecionamos apenas as recomendadas e não notificadas (notificado = 0)
    cursor.execute(f"""
        SELECT link, titulo, portal, descricao 
        FROM {TABELA_VAGAS} 
        WHERE estado_ia = 'RECOMENDADO' AND notificado = 0
    """)
    vagas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return vagas

def marcar_como_notificadas(links):
    """Atualiza o estado de notificação das vagas na base de dados SQLite."""
    if not DB_PATH or not TABELA_VAGAS:
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for link in links:
        cursor.execute(f"""
            UPDATE {TABELA_VAGAS} 
            SET notificado = 1 
            WHERE link = ?
        """, (link,))
    conn.commit()
    conn.close()
    print(f"💾 {len(links)} vagas marcadas como 'NOTIFICADO' na base de dados SQLite.")

def gerar_html_newsletter(vagas):
    """Gera um template de e-mail HTML elegante e moderno com CSS embutido."""
    itens_html = ""
    for vaga in vagas:
        titulo = vaga["titulo"]
        portal = vaga["portal"]
        link = vaga["link"]
        # Resumo ou descrição curta (primeiros 250 caracteres)
        resumo = vaga["descricao"][:250] + "..." if vaga["descricao"] else "Sem descrição disponível."
        
        itens_html += f"""
        <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); margin-top: 10px;">
            <span style="background-color: #ebf8ff; color: #2b6cb0; font-size: 11px; font-weight: bold; text-transform: uppercase; padding: 4px 8px; border-radius: 4px; display: inline-block; margin-bottom: 10px;">
                📍 {portal}
            </span>
            <h3 style="margin: 0 0 10px 0; color: #1a202c; font-size: 18px; font-family: 'Segoe UI', Helvetica, Arial, sans-serif;">
                {titulo}
            </h3>
            <p style="color: #4a5568; font-size: 14px; line-height: 1.5; margin: 0 0 15px 0; font-family: 'Segoe UI', Helvetica, Arial, sans-serif;">
                {resumo}
            </p>
            <a href="{link}" target="_blank" style="background-color: #3182ce; color: #ffffff; text-decoration: none; padding: 8px 16px; border-radius: 6px; font-size: 14px; font-weight: 500; display: inline-block; font-family: 'Segoe UI', Helvetica, Arial, sans-serif;">
                Ver Anúncio Real ➔
            </a>
        </div>
        """

    html_completo = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="background-color: #f7fafc; margin: 0; padding: 20px; font-family: 'Segoe UI', Helvetica, Arial, sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #f7fafc;">
            <tr>
                <td style="padding: 20px 0; text-align: center;">
                    <h1 style="margin: 0; color: #2d3748; font-size: 24px; font-weight: 800; letter-spacing: -0.5px;">
                        💼 Assistente de Emprego IA
                    </h1>
                    <p style="margin: 5px 0 0 0; color: #718096; font-size: 14px;">
                        As tuas recomendações personalizadas de Economia e Automação
                    </p>
                </td>
            </tr>
            <tr>
                <td>
                    {itens_html}
                </td>
            </tr>
            <tr>
                <td style="padding: 20px 0; text-align: center; color: #a0aec0; font-size: 12px; border-top: 1px solid #e2e8f0; margin-top: 20px;">
                    Este e-mail foi gerado automaticamente pelo teu pipeline de dados em Python.<br>
                    Faculdade de Economia do Porto (FEP) • Porto, Portugal
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    return html_completo

def enviar_newsletter():
    # 1. Recuperar configurações de variáveis de ambiente
    email_remetente_raw = os.environ.get("EMAIL_USER")
    email_destinatario_raw = os.environ.get("EMAIL_DEST")
    password_aplicacao_raw = os.environ.get("EMAIL_PASSWORD")

    if not email_remetente_raw or not password_aplicacao_raw:
        print("❌ Erro: As variáveis de ambiente EMAIL_USER e EMAIL_PASSWORD não foram encontradas.")
        print("💡 Dica: Garante que criaste um ficheiro '.env' na pasta do teu projeto contendo:")
        print("   EMAIL_USER=o_teu_email@gmail.com")
        print("   EMAIL_PASSWORD=abcd efgh ijkl mnop")
        return

    # SANITIZAÇÃO DE ERROS DE COPY-PASTE (Remoção absoluta de espaços em branco e non-breaking spaces \xa0)
    email_remetente = email_remetente_raw.strip().replace('\xa0', '').replace(' ', '')
    
    if email_destinatario_raw:
        email_destinatario = email_destinatario_raw.strip().replace('\xa0', '').replace(' ', '')
    else:
        email_destinatario = email_remetente

    # Para a password, o Gmail usa blocos de 4 caracteres. Se houver \xa0 entre eles, convertemos para espaços normais
    password_aplicacao = password_aplicacao_raw.strip().replace('\xa0', ' ')

    # 2. Obter vagas recomendadas pendentes de envio
    vagas_recomendadas = obter_vagas_recomendadas()

    if not vagas_recomendadas:
        print("☕ Sem novas vagas recomendadas para enviar hoje.")
        return

    print(f"📧 Encontradas {len(vagas_recomendadas)} vagas recomendadas. A preparar e-mail...")

    # 3. Montar a mensagem de e-mail de forma robusta e compatível com caracteres UTF-8
    msg = MIMEMultipart('alternative')
    
    # IMPORTANTE: Usar Header para codificar corretamente o assunto com emojis e caracteres não-ASCII
    msg['Subject'] = Header(f"🔔 {len(vagas_recomendadas)} Novas Vagas Recomendadas para Ti!", 'utf-8')
    msg['From'] = email_remetente
    msg['To'] = email_destinatario

    corpo_html = gerar_html_newsletter(vagas_recomendadas)
    
    # IMPORTANTE: Especificar o charset 'utf-8' explicitamente para evitar erros de encode ASCII ('\xa0')
    msg.attach(MIMEText(corpo_html, 'html', 'utf-8'))

    # 4. Enviar via servidor SMTP do Gmail
    try:
        print("🔌 A ligar ao servidor SMTP do Gmail (Porta 587)...")
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()  # Ativa a encriptação de segurança TLS
        
        print("🔑 A efetuar login de segurança...")
        server.login(email_remetente, password_aplicacao)
        
        print("✉️ A enviar e-mail...")
        # SOLUÇÃO DE SEGURANÇA MÁXIMA: send_message trata da serialização de todos os cabeçalhos UTF-8
        server.send_message(msg)
        server.quit()
        
        print("🚀 E-mail enviado com sucesso absoluto!")
        
        # 5. Marcar como notificadas no SQLite para evitar duplicados no dia seguinte
        links_enviados = [vaga["link"] for vaga in vagas_recomendadas]
        marcar_como_notificadas(links_enviados)

    except Exception as e:
        print(f"❌ Falha ao enviar e-mail: {e}")

if __name__ == "__main__":
    enviar_newsletter()
