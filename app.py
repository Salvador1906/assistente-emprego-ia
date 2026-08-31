# app.py (Esboço da estrutura de execução)

# 1. Tentar extrair do Portal da FEP
try:
    vagas_fep = extrair_vagas_fep()
except Exception as e:
    enviar_alerta_telegram(f"⚠️ Alerta Salvador: O login ou a extração no Portal da FEP falhou! Erro: {e}")
    vagas_fep = [] # Devolve uma lista vazia para o programa não quebrar

# 2. Tentar extrair do Net-Empregos
try:
    vagas_net_empregos = extrair_vagas_netempregos()
except Exception as e:
    print(f"Erro ao extrair do Net-Empregos: {e}")
    vagas_net_empregos = []

# 3. Tentar extrair do Upwork (Freelance)
try:
    vagas_upwork = extrair_vagas_upwork()
except Exception as e:
    print(f"Erro ao extrair do Upwork: {e}")
    vagas_upwork = []