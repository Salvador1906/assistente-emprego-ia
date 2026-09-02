import os
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# IMPORTAÇÃO DA MEMÓRIA
from database.db_manager import inicializar_db, guardar_vaga

# Carrega as credenciais do .env
load_dotenv()

FEP_EMAIL = os.getenv("FEP_EMAIL")
FEP_PASSWORD = os.getenv("FEP_PASSWORD")

def extrair_vagas_fep() -> list:
    vagas_fep = []
    
    # Garante que o SQLite está de pé
    inicializar_db()
    
    print("\n🌐 A iniciar o navegador para o portal da FEP...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        url_login = "https://sigarra.up.pt/wsgi/fep/pt/academic/career_portal/home_page" 
        page.goto(url_login, wait_until="domcontentloaded")
        time.sleep(2)
        
        print("🔑 A simular o login...")
        try:
            if page.is_visible("#authIconID"):
                print("📱 Ecrã mobile detetado. A clicar no botão para revelar formulário...")
                page.click("#authIconID")
                page.wait_for_selector("input[name='p_user']", state="visible", timeout=5000)
            else:
                print("💻 Ecrã desktop detetado. Os campos de login já estão visíveis.")

            page.fill("input[name='p_user']", FEP_EMAIL) 
            page.fill("input[name='p_pass']", FEP_PASSWORD)
            page.press("input[name='p_pass']", "Enter")
            
            page.wait_for_load_state("networkidle")
            print("✅ Login efetuado com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro durante o login: {e}")
            browser.close()
            raise e
            
        # Navegar para os anúncios
        url_anuncios = "https://sigarra.up.pt/wsgi/fep/pt/academic/career_portal/institutions/advertisements/list"
        print(f"🔄 A navegar para a página de anúncios: {url_anuncios}")
        page.goto(url_anuncios, wait_until="domcontentloaded")
        time.sleep(3)
        
        print("🔍 A recolher anúncios da tabela de listagem...")
        linhas = page.query_selector_all("table.table-striped tbody tr")
        print(f"📋 Encontradas {len(linhas)} linhas na tabela. A processar metadados...")
        
        vagas_temporarias = []
        
        for linha in linhas:
            try:
                colunas = linha.query_selector_all("td")
                if len(colunas) < 4:
                    continue
                
                # DATA: Acedemos à primeira coluna da linha [Índice 0]
                data = colunas[0].text_content().strip()
                
                # INFORMAÇÕES: Acedemos à segunda coluna da linha [Índice 1]
                coluna_info = colunas[1]
                elem_link = coluna_info.query_selector("a.advertisement_view")
                
                if elem_link:
                    titulo = elem_link.text_content().strip()
                    link_parcial = elem_link.get_attribute("href")
                    link_completo = f"https://sigarra.up.pt{link_parcial}"
                else:
                    continue
                    
                elem_empresa = coluna_info.query_selector("span.empresa")
                empresa = elem_empresa.text_content().strip() if elem_empresa else "N/D"
                
                # TIPO DE VAGA: Acedemos à quarta coluna da linha [Índice 3]
                tipo_vaga = colunas[2].text_content().strip()
                
                # Adicionamos as informações mapeadas
                vagas_temporarias.append({
                    "data": data,
                    "titulo": titulo,
                    "empresa": empresa,
                    "link": link_completo,
                    "tipo": tipo_vaga,
                    "portal": "FEP",
                    "localizacao": "Porto"
                })
                print(f"   📍 Metadados mapeados: {titulo} ({empresa})")
                
            except Exception as e_linha:
                print(f"⚠️ Erro ao ler metadados de uma linha: {e_linha}")
                continue

        print(f"\n📌 Fase 1 Concluída: {len(vagas_temporarias)} vagas mapeadas com sucesso.")
        print("📥 A iniciar a Fase 2: Navegar, extrair descrições e guardar na Memória...\n")

        # Fase B: Visitar links, ler descrições e salvar na base de dados
        vagas_novas_guardadas = 0
        
        for idx, vaga in enumerate(vagas_temporarias, 1):
            try:
                print(f"   [{idx}/{len(vagas_temporarias)}] A abrir detalhe de: {vaga['titulo']}...")
                page.goto(vaga["link"], wait_until="domcontentloaded")
                time.sleep(2)
                
                html_detalhe = page.content()
                sopa_detalhe = BeautifulSoup(html_detalhe, "html.parser")
                
                descricao = "Descrição não encontrada."
                for dt in sopa_detalhe.find_all("dt"):
                    texto_dt = dt.get_text().strip()
                    if "descrição" in texto_dt.lower():
                        dd_vizinho = dt.find_next_sibling("dd")
                        if dd_vizinho:
                            descricao = dd_vizinho.get_text(separator="\n").strip()
                        break
                
                vaga["descricao"] = descricao
                print(f"      ✅ Descrição obtida! ({len(descricao)} carateres)")
                
                # 💾 GRAVAÇÃO NO SQLITE
                foi_guardada = guardar_vaga(vaga)
                
                if foi_guardada:
                    print("      💾 🆕 [BD] Vaga nova identificada e guardada com sucesso!")
                    vagas_novas_guardadas += 1
                    vagas_fep.append(vaga)
                else:
                    print("      💾 ⏭️ [BD] Vaga repetida. Ignorada para evitar spam.")
                
            except Exception as e_detalhe:
                print(f"      ❌ Erro ao ler detalhe da vaga: {e_detalhe}")
                continue

        browser.close()
        
    print(f"\n📊 Resumo da execução: Guardadas {vagas_novas_guardadas} novas vagas de {len(vagas_temporarias)} analisadas.")
    return vagas_fep

if __name__ == "__main__":
    try:
        resultado = extrair_vagas_fep()
    except Exception as e:
        print(f"Ocorreu uma falha no teste geral: {e}")