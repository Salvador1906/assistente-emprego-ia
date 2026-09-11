import time
from curl_cffi import requests
from bs4 import BeautifulSoup

# IMPORTAÇÃO DA MEMÓRIA: Ligamos diretamente ao teu gestor de base de dados
from database.db_manager import inicializar_db, guardar_vaga

def extrair_vagas_netempregos(paginas: int = 2) -> list:
    vagas_recolhidas = []
    
    # Garante que a base de dados SQLite está pronta
    inicializar_db()
    
    # Disfarce para evitar bloqueios do servidor
    headers_base = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-PT,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.pt/",
    }

    # BLINDAGEM DE ÍNDICES: Variáveis para evitar colisões com Markdown
    idx_0 = 0
    idx_1 = 1
    idx_3 = 3
    
    # CICLO DE PAGINAÇÃO DINÂMICA
    for num_pagina in range(1, paginas + 1):
        url = f"https://www.net-empregos.com/emprego-gestao-empresas-economia.asp?page={num_pagina}"
        print(f"\n🌐 [Página {num_pagina}/{paginas}] A iniciar leitura de: {url}")
        
        try:
            resposta = requests.get(url, headers=headers_base, impersonate="chrome110")
            if resposta.status_code != 200:
                print(f"❌ Erro ao aceder à listagem (Pág {num_pagina}): Status {resposta.status_code}")
                continue


            sopa = BeautifulSoup(resposta.content, "html.parser", from_encoding="cp1252")
            
            # Captura os cartões de cada vaga
            cartoes = sopa.find_all("div", class_="job-item")
            print(f"📋 Encontradas {len(cartoes)} vagas na página {num_pagina}.")
            
            for idx, cartao in enumerate(cartoes, 1):
                try:
                    # 1. Extrair Título e Link
                    elem_link = cartao.find("a", class_="oferta-link")
                    if not elem_link:
                        elem_link = cartao.find("a", href=True)
                        
                    if not elem_link:
                        continue
                        
                    titulo = elem_link.get_text().strip()
                    link_parcial = elem_link["href"]
                    link_completo = f"https://www.net-empregos.com{link_parcial}" if not link_parcial.startswith("http") else link_parcial
                    
                    # 2. Extrair metadados (Data, Localização, Empresa) de dentro das tags <li>
                    elementos_li = cartao.find_all("li")
                    
                    data = "N/D"
                    localizacao = "N/D"
                    empresa = "N/D"
                    
                    if len(elementos_li) > idx_0:
                        data = elementos_li[idx_0].get_text().strip()
                    if len(elementos_li) > idx_1:
                        localizacao = elementos_li[idx_1].get_text().strip()
                    if len(elementos_li) > idx_3:
                        empresa = elementos_li[idx_3].get_text().strip()
                    
                    # 3. FASE B: Visitar a página individual para recolher a descrição completa
                    print(f"   [{idx}/{len(cartoes)}] A abrir detalhe de: {titulo}...")
                    
                    # Definição do cabeçalho com referer para simular cliques reais do site
                    headers_detalhe = headers_base.copy()
                    headers_detalhe["Referer"] = url
                    
                    # Pausa de cortesia para segurança de rede
                    time.sleep(1.5)
                    
                    resposta_vaga = requests.get(link_completo, headers=headers_detalhe, impersonate="chrome110")
                    descricao = "Descrição indisponível."
                    
                    if resposta_vaga.status_code == 200:
                        sopa_vaga = BeautifulSoup(resposta_vaga.text, "html.parser")
                        
                        # ALGORITMO MULTICAMADA ATUALIZADO:
                        # Procura primeiro pelas novas classes modernas de descrição do site
                        elem_desc = (
                            sopa_vaga.find("div", class_="job-description") or 
                            sopa_vaga.find("div", class_="job-description-content") or 
                            sopa_vaga.find("div", class_="job-details") or 
                            sopa_vaga.find("div", class_="job-desc") or 
                            sopa_vaga.find("div", class_="job-body") or
                            sopa_vaga.find("div", class_="oferta-desc") or 
                            sopa_vaga.find("span", class_="anuncio-texto") or 
                            sopa_vaga.find("div", class_="anuncio-texto") or 
                            sopa_vaga.find("div", class_="anuncio-detalhe") or
                            sopa_vaga.find("span", id="Noticia") or
                            sopa_vaga.find("article")
                        )
                        
                        if elem_desc:
                            # get_text(separator="\n") preserva parágrafos e quebras de linha reais
                            descricao = elem_desc.get_text(separator="\n").strip()
                        else:
                            # Se não encontrar nenhuma classe conhecida, tentamos isolar a coluna principal
                            # evitando o container global (que traz os menus de navegação do site)
                            coluna_principal = (
                                sopa_vaga.find("div", class_="col-lg-8") or 
                                sopa_vaga.find("div", class_="col-md-8") or 
                                sopa_vaga.find("div", class_="main-content")
                            )
                            if coluna_principal:
                                descricao = coluna_principal.get_text(separator="\n").strip()
                        
                        print(f"      ✅ Detalhe aberto com sucesso! ({len(descricao)} carateres)")
                    else:
                        print(f"      ❌ Erro de ligação à página de detalhe: Status {resposta_vaga.status_code}")
                    
                    # 4. Moldar a vaga para a base de dados
                    vaga = {
                        "link": link_completo,
                        "titulo": titulo,
                        "empresa": empresa,
                        "localizacao": localizacao,
                        "descricao": descricao,
                        "tipo": "Gestão / Economia",
                        "portal": "Net-Empregos"
                    }
                    
                    # 5. Guardar de forma segura na Memória SQLite (Deduplicação automática!)
                    foi_guardada = guardar_vaga(vaga)
                    if foi_guardada:
                        print(f"      💾 🆕 [BD] Vaga nova guardada com sucesso!")
                        vagas_recolhidas.append(vaga)
                    else:
                        print(f"      💾 ⏭️ [BD] Vaga repetida. Ignorada.")
                        
                except Exception as e_vaga:
                    print(f"   ⚠️ Erro ao processar dados desta vaga: {e_vaga}")
                    continue
                    
        except Exception as e_pagina:
            print(f"❌ Falha ao ler a página {num_pagina}: {e_pagina}")
            continue
            
    return vagas_recolhidas

if __name__ == "__main__":
    resultado = extrair_vagas_netempregos(paginas=2)
    print(f"\n🎉 Processo do Net-Empregos concluído! Novas vagas guardadas: {len(resultado)}")