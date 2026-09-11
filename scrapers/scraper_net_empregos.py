import time

from playwright.sync_api import sync_playwright

from database.db_manager import inicializar_db, guardar_vaga


def extrair_vagas_netempregos(paginas: int = 2) -> list:
    vagas_recolhidas = []
    inicializar_db()
    print("\n🌐 A iniciar o navegador Playwright para o Net-Empregos...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="pt-PT",
        )
        page = context.new_page()

        for num_pagina in range(1, paginas + 1):
            url = f"https://www.net-empregos.com/emprego-gestao-empresas-economia.asp?page={num_pagina}"
            print(f"\n🌐 [Página {num_pagina}/{paginas}] A iniciar leitura de: {url}")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                print(f" 📄 Título da página: {page.title()}")

                try:
                    page.wait_for_selector("div.job-item", timeout=12000)
                except Exception:
                    print(" ⚠️ Os cartões de vagas demoraram a carregar ou a página foi desafiada.")

                html_pagina = page.content()
                sopa = BeautifulSoup(html_pagina, "html.parser")
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
                        data = elementos_li[0].get_text(" ", strip=True) if len(elementos_li) > 0 else "N/D"
                        localizacao = elementos_li[1].get_text(" ", strip=True) if len(elementos_li) > 1 else "N/D"
                        empresa = elementos_li[2].get_text(" ", strip=True) if len(elementos_li) > 2 else "N/D"

                        print(f" [{idx}/{len(cartoes)}] A abrir detalhe de: {titulo}...")
                        page.goto(link_completo, wait_until="domcontentloaded", timeout=30000)
                        page.wait_for_timeout(1000)

                        sopa_vaga = BeautifulSoup(page.content(), "html.parser")
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
                            descricao = coluna_principal.get_text(separator="\n").strip() if coluna_principal else "Descrição indisponível."

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

        browser.close()
        return vagas_recolhidas


if __name__ == "__main__":
    resultado = extrair_vagas_netempregos(paginas=2)
    print(f"\n🎉 Processo do Net-Empregos concluído! Novas vagas guardadas: {len(resultado)}")
