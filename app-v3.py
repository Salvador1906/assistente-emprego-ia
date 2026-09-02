import os
import sys
import subprocess

# Tentamos carregar as variáveis do ficheiro .env se a biblioteca python-dotenv estiver instalada
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def executar_modulo(nome_ficheiro):
    """Executa um script Python como um sub-processo de forma limpa e isolada."""
    caminho_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), nome_ficheiro)
    
    if not os.path.exists(caminho_script):
        print(f"⚠️ Aviso: O ficheiro '{nome_ficheiro}' não foi encontrado neste diretório.")
        return False

    print(f"\n⚙️ A executar: {nome_ficheiro}...")
    
    # Solução de Engenharia de Sistemas para o erro ModuleNotFoundError: No module named 'database'
    # Injetamos o caminho da raiz do projeto no PYTHONPATH do sub-processo
    # Isso garante que qualquer script na pasta 'scrapers/' consiga importar de pastas na raiz (como 'database/')
    diretorio_raiz = os.path.dirname(os.path.abspath(__file__))
    env_sub = os.environ.copy()
    
    separador_path = ";" if sys.platform == "win32" else ":"
    if "PYTHONPATH" in env_sub:
        env_sub["PYTHONPATH"] = diretorio_raiz + separador_path + env_sub["PYTHONPATH"]
    else:
        env_sub["PYTHONPATH"] = diretorio_raiz

    try:
        # Corre o script usando o mesmo interpretador de Python ativo e injetando o PYTHONPATH
        resultado = subprocess.run(
            [sys.executable, caminho_script],
            check=True,
            text=True,
            env=env_sub
        )
        print(f"✅ {nome_ficheiro} concluído com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar {nome_ficheiro}: {e}")
        return False

def orquestrar_assistente():
    print("=" * 60)
    print("🤖 INICIANDO PIPELINE DIÁRIO DO ASSISTENTE DE EMPREGO IA 🤖")
    print("=" * 60)

    # 1. BLOCO 1 & 2: O EXTRATOR E A MEMÓRIA
    # Configurado com os nomes exatos de ficheiro detetados na tua pasta scrapers/
    scrapers = [
        os.path.join("scrapers", "scraper_net_empregos.py"),
        os.path.join("scrapers", "scraper_fep.py")
    ]
    
    scrapers_executados = 0
    for scraper in scrapers:
        if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), scraper)):
            executar_modulo(scraper)
            scrapers_executados += 1
            
    if scrapers_executados == 0:
        print("\nℹ️ Nota: Nenhum scraper externo ativo foi detetado na pasta 'scrapers/'.")
        print("   O pipeline continuará com as vagas atualmente pendentes na base de dados.")

    # 2. BLOCO 3: O FILTRO IA (Triagem com o Gemini)
    # Corre o filtro de inteligência artificial para avaliar novas vagas pendentes
    filtro_sucesso = executar_modulo("filtro_ia-v2.py")

    if not filtro_sucesso:
        print("\n⚠️ O Filtro de IA falhou ou não foi executado. O envio de e-mails será cancelado para evitar inconsistências.")
        return

    # 3. BLOCO 4: A NOTIFICAÇÃO (Newsletter de vagas recomendadas)
    # Corre o notificador que envia o HTML formatado para o teu e-mail
    executar_modulo("notificador_email-v7.py")

    print("\n" + "=" * 60)
    print("🎉 PIPELINE DO ASSISTENTE DE CARREIRA CONCLUÍDO COM SUCESSO! 🎉")
    print("=" * 60)

if __name__ == "__main__":
    orquestrar_assistente()
