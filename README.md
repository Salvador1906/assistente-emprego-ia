

# 💼 Assistente de Emprego Inteligente com IA (AI Career Assistant)

Um pipeline automático *end-to-end* desenvolvido em Python que monitoriza portais de emprego, utiliza Inteligência Artificial (Google Gemini) para avaliar e filtrar de forma pragmática as melhores ofertas de acordo com o perfil do candidato, e envia um resumo diário formatado em HTML por e-mail.

---

## 🎬 Demonstração em Vídeo (1 min 25s)

> **https://youtu.be/q1fcMpDWdDA**

*O vídeo demonstra a execução completa do pipeline: extração nos portais de emprego, triagem e decisão da IA, verificação de duplicados em base de dados SQLite e receção da newsletter por e-mail.*

---

## ⚙️ Arquitetura do Sistema

O sistema divide-se em 4 etapas modulares e autónomas:

1. **Scraping Multi-Fonte:**
   * **Career Portal FEP:** Automação de autenticação e navegação em área reservada utilizando **Playwright** com ecrã virtual (`xvfb-run`).
   * **Net-Empregos:** Extração de ofertas em categorias de Gestão e Economia utilizando **`curl_cffi`** (com simulação de *TLS Fingerprint* do Chrome) e descodificação adequada de caracteres (`cp1252`).
2. **Memória de Longo Prazo (Deduplicação):**
   * Gestão de base de dados relacional **SQLite** para registar vagas processadas anteriormente e evitar envios repetidos.
3. **Triagem Inteligente com IA (Google Gemini):**
   * Avaliação do texto completo de cada anúncio através de um prompt adaptável onde a IA atua como **Recrutador de Elite e Assistente de Carreira**, decidindo pragmaticamente entre `RECOMENDADO` ou `IGNORADO` com base nos critérios do candidato.
4. **Notificação por E-mail:**
   * Envio automático via **SMTP (Gmail)** de uma newsletter em **HTML/CSS** responsivo, contendo apenas as ofertas recomendadas pendentes.

---

## 🤖 Engenharia de Prompt (Filtro do Recrutador IA)

A triagem é realizada pelo modelo **Google Gemini**, instruído com o seguinte perfil e regras de decisão personalizáveis:

```text
Tu és um Recrutador de Elite e o Assistente de Carreira pessoal do Candidato.
O teu objetivo é analisar propostas de emprego e decidir de forma pragmática se deves recomendá-los ou ignorá-los.

O Candidato tem o seguinte perfil:
- Licenciado em Economia na Faculdade de Economia do Porto (FEP).
- Domina Python, Web Scraping (Playwright, BeautifulSoup, curl_cffi), tratamento de dados (Pandas, CSV) e Automação de Tarefas (RPA).
- Procura: Estágios Curriculares, Estágios Profissionais, programas de Trainee ou vagas Júnior/Entry-level.
- Áreas de interesse: Análise de Dados Financeiros (Financial Data Analyst), Consultoria, Business Analyst, Controlling, Business Intelligence ou Automação de Processos (RPA).

Regras de Decisão:
1. RECOMENDA (RECOMENDADO): Vagas júnior, estágios ou trainee nas áreas de interesse ou que valorizem competências analíticas, dados (Excel, SQL, Python) ou finanças/gestão.
2. IGNORA (IGNORADO): Vagas que exijam mais de 2-3 anos de experiência (Sénior/Diretor), áreas totalmente fora do âmbito ou que não se alinhem com o perfil.

Deves responder estritamente no seguinte formato:
DECISAO: [RECOMENDADO ou IGNORADO] | MOTIVO: [Explicação curta de 1 frase em português de Portugal]
```

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.12
* **Navegação & Web Scraping:** Playwright, BeautifulSoup4, `curl_cffi`
* **Inteligência Artificial:** API do Google Gemini (`google-genai`)
* **Base de Dados:** SQLite3
* **Automação & CI/CD:** GitHub Actions / Execução Local
* **Comunicação:** `smtplib`, `email.mime`

---

## 🚀 Como Executar e Configurar

1. **Clonar o repositório:**
   ```bash
   git clone https://github.com/Salvador1906/assistente-emprego-ia.git
   cd assistente-emprego-ia
   ```

2. **Instalar dependências:**
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

3. **Configurar variáveis de ambiente (`.env`):**
   Cria um ficheiro `.env` na raiz do projeto com as credenciais necessárias:
   ```env
   GEMINI_API_KEY=sua_chave_gemini_aqui
   EMAIL_USER=email_remetente@gmail.com
   EMAIL_PASSWORD=palavra_passe_de_aplicacao_gmail
   EMAIL_DEST=email_destino@gmail.com
   FEP_EMAIL=utilizador_fep
   FEP_PASSWORD=palavra_passe_fep
   ```

4. **Executar o pipeline:**
   ```bash
   python app.py
   ```

---

## 🛡️ Segurança e Privacidade

Os dados sensíveis (chaves de API, credenciais de acesso, palavras-passe de aplicação e o ficheiro da base de dados local `assistente.db`) encontram-se devidamente protegidos e excluídos do controlo de versões através do ficheiro `.gitignore`.
