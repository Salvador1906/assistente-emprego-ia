import os
import time
from curl_cffi import requests
from bs4 import BeautifulSoup

# IMPORTAÇÃO DA MEMÓRIA: Conectamos diretamente ao teu db_manager local
from database.db_manager import inicializar_db, guardar_vaga

def extrair_vagas_upwork() -> list:
    vagas_recolhidas = []
    
    # Garante que a base de dados SQLite está pronta e a tabela existe
    inicializar_db()
    
    # URL do Feed RSS do Upwork para procuras de Python e Web Scraping
    url_rss = "https://www.upwork.com/nx/search/jobs/?topic_id=9777648"
    print(f"\n🌐 A aceder ao Feed RSS do Upwork: {url_rss}")
    
    # Cabeçalho para simular um navegador comum e evitar restrições
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        # Efetuamos a requisição descarregando o XML
        resposta = requests.get(url_rss, headers=headers, impersonate="chrome110")
        if resposta.status_code != 200:
            print(f"❌ Erro ao aceder ao RSS do Upwork: Status {resposta.status_code}")
            return []
            
        # Como o feed é XML, lemos usando o parser de HTML do BeautifulSoup (que funciona perfeitamente para tags RSS)
        sopa = BeautifulSoup(resposta.text, "html.parser")
        
        # No formato RSS, cada vaga/projeto vem dentro de uma tag <item>
        itens = sopa.find_all("item")
        print(f"📋 Encontrados {len(itens)} projetos recentes no feed do Upwork.")
        
        for idx, item in enumerate(itens, 1):
            try:
                # 1. Extrair metadados básicos das tags do RSS
                elem_titulo = item.find("title")
                elem_link = item.find("link")
                elem_desc_raw = item.find("description")
                
                titulo = elem_titulo.get_text().strip() if elem_titulo else "Projeto Sem Título"
                link = elem_link.get_text().strip() if elem_link else ""
                
                if not link:
                    continue
                
                # 2. Limpar a descrição (o Upwork envia HTML codificado dentro do RSS)
                descricao_raw = elem_desc_raw.get_text().strip() if elem_desc_raw else ""
                
                # Usamos uma segunda passagem do BeautifulSoup para limpar quaisquer tags HTML do texto
                sopa_desc = BeautifulSoup(descricao_raw, "html.parser")
                descricao = sopa_desc.get_text(separator="\n").strip()
                
                # 3. Moldar a vaga para o molde padrão da tua base de dados SQLite
                vaga = {
                    "link": link,
                    "titulo": titulo,
                    "empresa": "Cliente Upwork",
                    "localizacao": "Trabalho Remoto (Global)",
                    "descricao": descricao,
                    "tipo": "Freelance",
                    "portal": "Upwork"
                }
                
                # 4. Guardar de forma segura na Memória SQLite (Deduplicação automática!)
                foi_guardada = guardar_vaga(vaga)
                if foi_guardada:
                    # Imprime as primeiras letras do título para o log ficar elegante
                    print(f"      💾 🆕 [BD] Novo projeto Upwork guardado: {titulo[:50]}...")
                    vagas_recolhidas.append(vaga)
                else:
                    print(f"      💾 ⏭️ [BD] Projeto Upwork repetido. Ignorado.")
                    
            except Exception as e_item:
                print(f"   ⚠️ Erro ao mapear item do RSS do Upwork: {e_item}")
                continue
                
    except Exception as e:
        print(f"❌ Falha geral ao processar o feed do Upwork: {e}")
        
    return vagas_recolhidas

if __name__ == "__main__":
    resultado = extrair_vagas_upwork()
    print(f"\n🎉 Processo do Upwork concluído! Novos projetos guardados: {len(resultado)}")