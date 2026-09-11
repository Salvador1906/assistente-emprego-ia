import time

from bs4 import BeautifulSoup
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
                    page.wait_for_selector("div.job-item", timeout=10000)
                except Exception:
                    print(" ⚠️ Aviso: O seletor 'div.job-item' não apareceu no tempo limite (possível bloqueio).")

                html_pagina = page.content()
                sopa = BeautifulSoup(html_pagina, "html.parser")
                cartoes = sopa.select("div.job-item")
                print(f"📋 Encontradas {len(cartoes)} vagas na página {num_pagina}.")

                for idx, cartao in enumerate(cartoes, 1):
                    try:
                        elem_link = cartao.select_one("a.oferta-link") or cartao.find("a", href=True)
                        if not elem_link:
                            continue

                        titulo = elem_link.get_text(" ", strip=True)
                        href = elem_link.get("href", "")
                        link_completo = href if href.startswith("http") else f"https://www.net-empregos.com{href}"

                        itens = [li.get_text(" ", strip=True) for li in cartao.select("li")]
                        data = itens[0] if len(itens) > 0 else "N/D"
                        localizacao = itens[1] if len(itens) > 1 else "N/D"
                        empresa = itens[2] if len(itens) > 2 else "N/D"

                        print(f" [{idx}/{len(cartoes)}] A abrir detalhe de: {titulo}...")
                        page.goto(link_completo, wait_until="domcontentloaded", timeout=30000)
                        page.wait_for_timeout(1000)

                        sopa_vaga = BeautifulSoup(page.content(), "html.parser")
                        elem_desc = (
                            sopa_vaga.select_one("div.job-description")
                            or sopa_vaga.select_one("div.job-description-content")
                            or sopa_vaga.select_one("div.job-details")
                            or sopa_vaga.select_one("div.job-desc")
                            or sopa_vaga.select_one("div.job-body")
                            or sopa_vaga.select_one("div.oferta-desc")
                            or sopa_vaga.select_one("span.anuncio-texto")
                            or sopa_vaga.select_one("div.anuncio-texto")
                            or sopa_vaga.select_one("div.anuncio-detalhe")
                            or sopa_vaga.select_one("span#Noticia")
                            or sopa_vaga.select_one("article")
                        )

                        if elem_desc:
                            descricao = elem_desc.get_text("\n", strip=True)
                        else:
                            coluna_principal = (
                                sopa_vaga.select_one("div.col-lg-8")
                                or sopa_vaga.select_one("div.col-md-8")
                                or sopa_vaga.select_one("div.main-content")
                            )
                            descricao = coluna_principal.get_text("\n", strip=True) if coluna_principal else "Descrição indisponível."

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
