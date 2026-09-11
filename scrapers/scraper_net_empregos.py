import time
from bs4 import BeautifulSoup
from curl_cffi import requests
from database.db_manager import inicializar_db, guardar_vaga


def extrair_vagas_netempregos(paginas: int = 2) -> list:
    vagas_recolhidas = []
    inicializar_db()

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-PT,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.pt/",
    }

    for num_pagina in range(1, paginas + 1):
        if num_pagina == 1:
            url = "https://www.net-empregos.com/emprego-gestao-empresas-economia.asp"
        else:
            url = f"https://www.net-empregos.com/emprego-gestao-empresas-economia.asp?page={num_pagina}"

        print(f"\n🌐 [Página {num_pagina}/{paginas}] A iniciar leitura de: {url}")

        try:
            resposta = requests.get(url, headers=headers, impersonate="chrome110", timeout=30)
            if resposta.status_code != 200:
                print(f"❌ Erro ao aceder à página {num_pagina}: Status {resposta.status_code}")
                continue

            sopa = BeautifulSoup(resposta.content, "html.parser", from_encoding="cp1252")
            cartoes = sopa.find_all("div", class_="job-item")
            print(f"📋 Encontradas {len(cartoes)} vagas na página {num_pagina}.")

            for idx, cartao in enumerate(cartoes, 1):
                try:
                    elem_link = cartao.find("a", class_="oferta-link") or cartao.find("a", href=True)
                    if not elem_link:
                        continue

                    titulo = elem_link.get_text().strip()
                    link_parcial = elem_link["href"]
                    link_completo = f"https://www.net-empregos.com{link_parcial}" if not link_parcial.startswith("http") else link_parcial

                    elementos_li = cartao.find_all("li")
                    data = elementos_li[0].get_text().strip() if len(elementos_li) > 0 else "N/D"
                    localizacao = elementos_li[1].get_text().strip() if len(elementos_li) > 1 else "N/D"
                    empresa = elementos_li[2].get_text().strip() if len(elementos_li) > 2 else "N/D"

                    print(f" [{idx}/{len(cartoes)}] A abrir detalhe de: {titulo}...")
                    headers_detalhe = headers.copy()
                    headers_detalhe["Referer"] = url
                    time.sleep(1)

                    resposta_vaga = requests.get(link_completo, headers=headers_detalhe, impersonate="chrome110", timeout=30)
                    descricao = "Descrição indisponível."

                    if resposta_vaga.status_code == 200:
                        sopa_vaga = BeautifulSoup(resposta_vaga.content, "html.parser", from_encoding="cp1252")
                        elem_desc = (
                            sopa_vaga.find("div", class_="job-description")
                            or sopa_vaga.find("div", class_="job-description-content")
                            or sopa_vaga.find("div", class_="job-details")
                            or sopa_vaga.find("div", class_="job-desc")
                            or sopa_vaga.find("div", class_="job-body")
                            or sopa_vaga.find("div", class_="oferta-desc")
                            or sopa_vaga.find("span", class_="anuncio-texto")
                            or sopa_vaga.find("div", class_="anuncio-texto")
                            or sopa_vaga.find("div", class_="anuncio-detalhe")
                            or sopa_vaga.find("span", id="Noticia")
                            or sopa_vaga.find("article")
                        )

                        if elem_desc:
                            descricao = elem_desc.get_text(separator="\n").strip()
                        else:
                            coluna_principal = (
                                sopa_vaga.find("div", class_="col-lg-8")
                                or sopa_vaga.find("div", class_="col-md-8")
                                or sopa_vaga.find("div", class_="main-content")
                            )
                            if coluna_principal:
                                descricao = coluna_principal.get_text(separator="\n").strip()

                    vaga = {
                        "link": link_completo,
                        "titulo": titulo,
                        "empresa": empresa,
                        "localizacao": localizacao,
                        "descricao": descricao,
                        "tipo": "Gestão / Economia",
                        "portal": "Net-Empregos",
                    }

                    foi_guardada = guardar_vaga(vaga)
                    if foi_guardada:
                        print(" 💾 🆕 [BD] Vaga nova guardada com sucesso!")
                        vagas_recolhidas.append(vaga)
                    else:
                        print(" 💾 ⏭️ [BD] Vaga repetida. Ignorada.")
                except Exception as e_vaga:
                    print(f" ⚠️ Erro ao processar dados desta vaga: {e_vaga}")
                    continue
        except Exception as e_pagina:
            print(f"❌ Falha ao ler a página {num_pagina}: {e_pagina}")
            continue

    return vagas_recolhidas


if __name__ == "__main__":
    resultado = extrair_vagas_netempregos(paginas=2)
    print(f"\n🎉 Processo do Net-Empregos concluído! Novas vagas guardadas: {len(resultado)}")
