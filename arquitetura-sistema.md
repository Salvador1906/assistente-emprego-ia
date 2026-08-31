# 🤖 Arquitetura do Assistente Pessoal de Emprego e Freelance (Python + IA)

Este documento descreve detalhadamente a arquitetura, o fluxo de dados e a infraestrutura de deployment do **Assistente Pessoal de Emprego e Freelance**. O sistema foi concebido de forma modular e inteligente em Python, com o objetivo de monitorizar vagas corporativas e projetos rápidos de freelancing, triando-os através de Inteligência Artificial e notificando o utilizador de acordo com o nível de urgência.

---

## 🧭 1. Visão Geral do Projeto
O assistente é uma ferramenta de automação pessoal voltada para as necessidades de um estudante da Licenciatura em Economia da FEP, que simultaneamente desenvolve competências de programação e automação em Python. O sistema monitoriza portais nacionais, agregadores de trabalho remoto internacional e plataformas de freelance, centralizando toda a gestão numa base de dados local leve e notificando o utilizador em tempo real ou de forma consolidada na nuvem.

### Objetivos Principais:
1. **Otimização de Tempo:** Evitar a consulta manual diária de múltiplas plataformas.
2. **Filtragem Inteligente:** Delegar a análise semântica e contextual das ofertas de emprego à API do Gemini, descartando ruído e vagas inadequadas.
3. **Celeridade em Freelancing:** Detetar projetos rápidos no Upwork que combinem com as competências atuais de Python e notificar instantaneamente por Telegram para garantir submissões rápidas.
4. **Independência de Hardware:** Execução automatizada e contínua através do **GitHub Actions**, permitindo que o sistema funcione na nuvem mesmo com o computador pessoal desligado.

---

## 🧱 2. Os 4 Blocos Estruturais

A arquitetura do sistema divide-se em quatro blocos lógicos independentes e modulares:

```
                  ┌──────────────────────────────────────────────┐
                  │           [ BLOCO 1: O EXTRATOR ]            │
                  │   Scrapers Modulares (FEP, Upwork, etc.)     │
                  └──────────────────────┬───────────────────────┘
                                         │  (Dados Brutos)
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │            [ BLOCO 2: A MEMÓRIA ]            │
                  │       Deduplicação SQLite (Links Únicos)     │
                  └──────────────────────┬───────────────────────┘
                                         │  (Novos Anúncios)
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │          [ BLOCO 3: O FILTRO IA ]            │
                  │       Análise Semântica (Gemini API)         │
                  └──────────────────────┬───────────────────────┘
                                         │  (Vagas Recomendadas)
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │          [ BLOCO 4: A NOTIFICAÇÃO ]          │
                  │    Urgentes (Telegram) | Geral (E-mail)      │
                  │        Painel de Controlo (Sheets)           │
                  └──────────────────────────────────────────────┘
```

### Bloco 1: O Extrator (Os Scrapers)
Cada portal de origem possui um script ou função autónoma. Esta modularidade garante que a alteração de layout num site não afete o funcionamento dos restantes extratores.
*   **Career Portal FEP:** Utiliza o **Playwright** para simular o fluxo de login de todas as vezes (devido a requisitos de segurança da faculdade) e clica individualmente em cada anúncio para extrair a descrição completa.
*   **Upwork / Portais Remotos:** Utiliza o **Playwright** ou ferramentas otimizadas para imitar a assinatura TLS de navegadores reais (como o `curl_cffi`) para contornar proteções robustas como a Cloudflare.
*   **Formatador de Saída:** Independentemente da ferramenta ou site, todos os scrapers devolvem os dados normalizados num dicionário ou DataFrame Pandas com as chaves: `Título`, `Empresa`, `Localização`, `Link` e `Descrição`.

### Bloco 2: A Memória (Deduplicação)
Para evitar o processamento duplicado de anúncios e o spam na caixa de entrada, o sistema utiliza o **SQLite** (módulo nativo `sqlite3` do Python).
*   **Identificador Único:** O link do anúncio (`URL`) funciona como chave primária na tabela SQLite (`anuncios_processados`).
*   **Fluxo:** Antes de enviar qualquer anúncio para análise de IA, o script principal faz uma consulta rápida à base de dados. Se o link já existir, a vaga é ignorada. Caso contrário, o link é registado e o anúncio segue para a triagem.

### Bloco 3: O Filtro de IA (Gemini API)
A API do Gemini (através do modelo `gemini-2.5-flash` ou `gemini-2.0-flash`) atua como avaliador humano dos anúncios novos de acordo com o teu perfil de interesses.
*   **Perfil Corporativo:** Foca-se em posições analíticas, estágios de verão ou de integração profissional nas áreas de Finanças Corporativas, Consultoria de Gestão e Análise de Dados Económicos, descartando vagas administrativas ou de vendas diretas.
*   **Perfil Técnico/Freelance:** Filtra anúncios de automação e Web Scraping que usam ferramentas do teu "cinto de utilidades" técnico (Playwright, Pandas, `gspread`, `re`, `shutil` e `os`).
*   **Output Estruturado:** A IA é instruída através de *System Instructions* para devolver obrigatoriamente um formato JSON estruturado com os campos: `veredito` ("RECOMENDADO" ou "IGNORAR"), `nota_compatibilidade` (1-10), `resumo` (1 frase descritiva) e `competencias_requeridas`.

### Bloco 4: A Notificação (Telegram, E-mail & Google Sheets)
O sistema possui três rotas de entrega baseadas na urgência do anúncio:
1.  **Rota de Urgência (Telegram):** Projetos de freelance (Upwork) aprovados pela IA são enviados instantaneamente pelo bot de Telegram. A rapidez de submissão é essencial para garantir estes trabalhos.
2.  **Rota Diária (E-mail Newsletter):** Vagas corporativas tradicionais e de estágios de verão são guardadas e consolidadas num e-mail formatado em HTML limpo enviado todas as manhãs às 09:00.
3.  **Rota de Gestão (Google Sheets):** Todos os anúncios "Recomendados" pela IA são registados automaticamente como linhas numa folha de cálculo no Google Sheets do utilizador via API (`gspread`). Na folha, uma coluna manual "Estado da Candidatura" com menu pendente permite gerir o progresso das mesmas semanalmente.

---

## 📊 3. Diagrama do Fluxo Unificado

Abaixo encontra-se o desenho completo de como os dados viajam entre o teu computador, a internet, a base de dados SQLite, a API de IA da Google e os teus canais de comunicação diários:

```text
       [ Scrapers / Extratores ]
                  │
                  ▼
         [ Memória SQLite ] ➔ Descarta duplicados
                  │
                  ▼
         [ Filtro de IA ] ➔ Avalia e pontua as vagas com Gemini API
                  │
       ┌──────────┴──────────┐
       ▼                     ▼
[ É Urgente? ]         [ É Tradicional? ]
  (ex: Upwork)         (ex: FEP / Net-Empregos)
       │                     │
       ▼                     ▼
[ Alerta Telegram ]     [ Guarda no SQLite ]
 (Tempo Real)                │
                             ▼
                        [ GitHub Actions ]
                             │ (Todos os dias às 9h)
                             ▼
                        [ Envia Newsletter ]
                             │
                             ▼
                        [ Registo Geral no Google Sheets ]
                         (Para gestão e estado semanal)
```

---

## 🗂️ 4. Estrutura de Ficheiros do Projeto

Para manter o projeto profissional, modular e em conformidade com o princípio de separação de responsabilidades, o repositório Git privado está estruturado da seguinte forma:

```text
assistente-emprego-ia/
├── .github/
│   └── workflows/
│       └── pipeline.yml         # Ficheiro de configuração do GitHub Actions
├── scrapers/
│   ├── __init__.py
│   ├── fep_portal.py            # Extrator específico para o Career Portal FEP (Playwright)
│   ├── net_empregos.py          # Extrator específico para Net-Empregos (BeautifulSoup/curl_cffi)
│   └── upwork_python.py         # Extrator específico para Upwork (Feed RSS/curl_cffi)
├── database/
│   ├── __init__.py
│   └── db_manager.py            # Funções de ligação, consulta e inserção no SQLite
├── ai/
│   ├── __init__.py
│   └── gemini_filter.py         # Prompt, validação de JSON e comunicação com o Gemini
├── notifications/
│   ├── __init__.py
│   ├── telegram_bot.py          # Envio de alertas instantâneos de projetos rápidos
│   ├── email_sender.py          # Conexão SMTP para gerar e enviar a newsletter diária HTML
│   └── sheets_sync.py           # Integração gspread para carregar os recomendados na nuvem
├── .gitignore                   # Lista de exclusão para o Git (esconde credenciais e cache)
├── app.py                       # Orquestrador central que une todos os blocos
├── credentials.json             # Chaves da Service Account do Google Cloud (NÃO SUBIR AO GIT)
├── requirements.txt             # Dependências das bibliotecas de Python
└── README.md                    # Documentação do projeto para o teu portfólio
```

---

## ☁️ 5. Configuração Cloud com GitHub Actions

O **GitHub Actions** permite executar o teu assistente de forma 100% gratuita nos servidores da Microsoft na nuvem, correndo o scraper mesmo com o teu computador pessoal desligado.

### Configuração do Workflow (`.github/workflows/pipeline.yml`)
Cria o ficheiro neste caminho dentro do teu repositório para definir a rotina de execução na nuvem:

```yaml
name: Execucao Assistente Emprego IA

on:
  schedule:
    # Corre todos os dias às 09:00 UTC (ajustar ao fuso de Portugal)
    - cron: '0 9 * * *'
  # Permite correr manualmente o script a partir do site do GitHub
  workflow_dispatch:

jobs:
  executar_assistente:
    runs-on: ubuntu-latest

    steps:
    - name: Copiar Codigo do Repositorio
      uses: actions/checkout@v4

    - name: Configurar o Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'
        cache: 'pip'

    - name: Instalar Dependencias
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        playwright install chromium

    - name: Restaurar Base de Dados SQLite
      # O GitHub Actions corre num ambiente fresco a cada dia.
      # Usamos uma cache para persistir a base de dados SQLite entre execuções.
      uses: actions/cache@v4
      with:
        path: database/assistente.db
        key: db-sqlite-${{ github.run_id }}
        restore-keys: |
          db-sqlite-

    - name: Executar o Assistente
      env:
        GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
        TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        EMAIL_USER: ${{ secrets.EMAIL_USER }}
        EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
        GOOGLE_CREDENTIALS: ${{ secrets.GOOGLE_CREDENTIALS }}
      run: |
        # Recria o credentials.json a partir do segredo configurado no GitHub
        echo "$GOOGLE_CREDENTIALS" > credentials.json
        python app.py

    - name: Guardar Cache da Base de Dados Atualizada
      uses: actions/cache/save@v4
      with:
        path: database/assistente.db
        key: db-sqlite-${{ github.run_id }}
```

### Onde Configurar as Chaves no GitHub?
Para que o código aceda às tuas contas de serviço e APIs sem expor as chaves ao público:
1. No teu repositório do GitHub, vai a **Settings** > **Secrets and variables** > **Actions**.
2. Clica em **New repository secret** e adiciona as variáveis:
   * `GEMINI_API_KEY`: A tua chave do Google AI Studio.
   * `TELEGRAM_TOKEN` e `TELEGRAM_CHAT_ID`: O token do BotFather e o teu ID de chat.
   * `EMAIL_USER` e `EMAIL_PASSWORD`: O teu endereço de e-mail e password de aplicação (gerada na tua conta de e-mail para acesso seguro de scripts).
   * `GOOGLE_CREDENTIALS`: Copia e cola todo o texto que está dentro do teu ficheiro `credentials.json` neste segredo.

---

## 🛠️ 6. Trechos Base de Implementação

Eis os blocos lógicos essenciais que o teu projeto vai usar para que possas visualizar como escrever cada parte do assistente:

### Exemplo do Bloco 2: Gestor SQLite (`database/db_manager.py`)
```python
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "assistente.db")

def inicializar_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anuncios_processados (
            link TEXT PRIMARY KEY,
            data_descoberta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def link_ja_processado(link: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM anuncios_processados WHERE link = ?", (link,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado is not None

def registar_link(link: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO anuncios_processados (link) VALUES (?)", (link,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()
```

### Exemplo do Bloco 3: Chamada Inteligente à IA (`ai/gemini_filter.py`)
```python
import json
from google import genai

def analisar_vaga_com_ia(titulo: str, descricao: str, api_key: str) -> dict:
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    És um assistente de recrutamento especializado em Economia e Automação de Processos.
    Avalia a seguinte oportunidade com base neste perfil de interesse:
    - O candidato estuda Economia na FEP. Interessa-se por Finanças, Consultoria, Análise de Dados e Controlo de Gestão. Deseja estojos de verão ou vagas entry-level analíticas.
    - O candidato sabe programar em Python (especialmente automação, web scraping e limpeza de dados com Pandas). Interessa-se por projetos de freelance rápidos nestas áreas.
    - Ignora vagas puramente comerciais de telemarketing, vendas diretas ou trabalho administrativo repetitivo.

    Anúncio:
    Título: {titulo}
    Descrição: {descricao}

    Responde APENAS no formato JSON especificado abaixo, sem qualquer outro texto:
    {{
        "veredito": "RECOMENDADO" ou "IGNORAR",
        "nota_compatibilidade": número de 1 a 10,
        "resumo": "Uma frase que explique o motivo do veredito",
        "competencias_requeridas": ["lista", "de", "competencias"]
    }}
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        # Limpar eventuais blocos de código markdown que o modelo envie no JSON
        texto_limpo = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(texto_limpo)
    except Exception as e:
        print(f"⚠️ Erro ao chamar a Gemini API: {e}")
        return {
            "veredito": "IGNORAR",
            "nota_compatibilidade": 1,
            "resumo": "Erro na execução da IA.",
            "competencias_requeridas": []
        }
```

---

## 🔒 7. Considerações Éticas e de Segurança
O teu assistente respeita rigorosamente as boas práticas de engenharia web e limites éticos de recolha de dados:
*   **Controlo de Requisições:** O extrator inclui uma pausa cortês de 2 a 3 segundos entre chamadas a páginas ou anúncios, evitando sobrecarregar os servidores originais ou simular um ataque de negação de serviço.
*   **Proteção de Dados do GitHub:** O ficheiro `.gitignore` está configurado para garantir que dados reais de anúncios extraídos (ficheiros `.csv`), histórico de cookies/perfis de Chrome do Playwright e chaves de acesso privadas (`credentials.json`, tokens) nunca sejam carregados no repositório público ou privado, sendo mantidos estritamente como segredos encriptados no GitHub.
