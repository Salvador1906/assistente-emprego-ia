import os
import time
from google import genai
from google.genai import errors
from dotenv import load_dotenv

# Carrega as credenciais do .env
load_dotenv()

# IMPORTAÇÃO DA MEMÓRIA: Ligamos diretamente às funções da tua base de dados
try:
    from database.db_manager import obter_vagas_pendentes, atualizar_estado_ia
except ImportError:
    # Fallback caso queiras testar o script isoladamente ou simular os dados
    def obter_vagas_pendentes():
        return [
            {
                "titulo": "Estágio Profissional em Gestão (ou equivalente)",
                "portal": "Net-Empregos",
                "link": "https://www.net-empregos.com/15853793/estagio-profissional-em-gestao-ou-equivalente/",
                "descricao": "Procuramos estagiário para apoiar a área financeira e controlo de gestão..."
            }
        ]
    def atualizar_estado_ia(link, estado):
        print(f"[Simulação] Vaga com link '{link}' atualizada para: {estado}")

PROMPT_SISTEMA_PERSONA = """
Tu és um Recrutador de Elite e o Assistente de Carreira pessoal do Salvador.
O teu objetivo é analisar propostas de emprego e decidir de forma pragmática se deves recomendá-los ou ignorá-los.

O Salvador tem o seguinte perfil:
- Estudante de Licenciatura em Economia na Faculdade de Economia do Porto (FEP).
- Domina Python, Web Scraping (Playwright, BeautifulSoup, curl_cffi), tratamento de dados (Pandas, CSV) e Automação de Tarefas (RPA).
- Procura: Estágios Curriculares, Estágios Profissionais, programas de Trainee ou vagas Júnior/Entry-level.
- Áreas de interesse: Análise de Dados Financeiros (Financial Data Analyst), Consultoria, Business Analyst, Controlling, Business Intelligence ou Automação de Processos (RPA).

Regras de Decisão:
1. RECOMENDA (RECOMENDADO): Vagas júnior, estágios ou trainee nas áreas de interesse ou que valorizem competências analíticas, dados (Excel, SQL, Python) ou finanças/gestão.
2. IGNORA (IGNORADO): Vagas que exijam mais de 2-3 anos de experiência (Sénior/Diretor), áreas totalmente fora do âmbito ou que não se alinhem com o perfil.

Deves responder estritamente no seguinte formato:
DECISAO: [RECOMENDADO ou IGNORADO] | MOTIVO: [Explicação curta de 1 frase em português de Portugal]
"""

def triar_vagas_com_ia():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Erro: A variável de ambiente GEMINI_API_KEY não está definida no teu Mac.")
        print("💡 Dica: Corre definindo a variável na mesma linha no terminal:")
        print("   GEMINI_API_KEY='a_tua_chave' python3 filtro_ia.py")
        return

    # Inicializa o cliente oficial do Gemini
    client = genai.Client(api_key=api_key)
    vagas_pendentes = obter_vagas_pendentes()
    
    if not vagas_pendentes:
        print("\n☕ Nenhuma vaga nova pendente de avaliação na base de dados.")
        return
        
    print(f"\n🧠 A iniciar a triagem inteligente de {len(vagas_pendentes)} vagas com o Gemini...")
    
    idx_vaga = 0
    while idx_vaga < len(vagas_pendentes):
        vaga = vagas_pendentes[idx_vaga]
        titulo = vaga["titulo"]
        portal = vaga["portal"]
        link = vaga["link"]
        descricao = vaga["descricao"][:1500] if vaga["descricao"] else "Sem descrição."
        
        #print(f"\n[{idx_vaga + 1}/{len(vagas_pendentes)}] A avaliar: '{titulo}' ({portal})...")
        
        prompt_vaga = f"Analisa esta vaga:\nTítulo: {titulo}\nPortal: {portal}\nDescrição:\n{descricao}"
        
        try:
            # Chamada ao modelo Gemini 3.5 Flash-lite (com cotas diárias gratuitas muito maiores!)
            resposta = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt_vaga,
                config={
                    "system_instruction": PROMPT_SISTEMA_PERSONA,
                    "temperature": 0.2
                }
            )
            
            resultado_texto = resposta.text.strip()
            print(f"   🤖 Resposta da IA: {resultado_texto}")
            
            if "DECISAO: RECOMENDADO" in resultado_texto:
                atualizar_estado_ia(link, "RECOMENDADO")
            else:
                atualizar_estado_ia(link, "IGNORADO")
                
            idx_vaga += 1
            
            # Pausa defensiva entre chamadas (2 segundos é muito seguro para o modelo Lite)
            time.sleep(2)
            
        except errors.APIError as e_api:
            # Captura erros de limite de quota (429) de forma inteligente
            if e_api.code == 429 or "RESOURCE_EXHAUSTED" in str(e_api):
                if "RequestsPerDay" in str(e_api):
                    print("\n❌ [API] Limite diário (RPD) esgotado para este modelo.")
                    print("💡 Sugestão: Aguarda que a quota diária reinicie ou tenta outra chave de API.")
                    break
                else:
                    print("\n⚠️ [API] Limite por minuto (RPM) atingido. A aguardar 20s...")
                    time.sleep(20)
                    print("   🔄 A retomar avaliação da mesma vaga...\n")
                    continue
            else:
                print(f"   ❌ Erro de API do Gemini: {e_api}")
                idx_vaga += 1
                
        except Exception as e:
            print(f"   ⚠️ Falha inesperada ao processar vaga: {e}")
            idx_vaga += 1
            continue

if __name__ == "__main__":
    triar_vagas_com_ia()
