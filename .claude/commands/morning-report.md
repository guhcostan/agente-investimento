---
description: Relatório matinal de investimentos B3
---

Execute o script de análise e gere o relatório de investimentos do dia.

Passos:
1. Execute `bash run.sh` e capture o output completo (macro + screener + portfolio + recomendação)
2. Para cada um dos top 3 candidatos retornados pelo screener, execute `/last30days <TICKER>` para buscar notícias e discussões dos últimos 30 dias
3. Apresente o relatório consolidado em markdown com o cabeçalho: `# Relatório Matinal — <data de hoje>`
4. Se houver erro em qualquer etapa, mostre o erro e indique a causa provável (yfinance fora do ar, BCB API indisponível, etc.)

Formato do relatório:
- **Macro** — SELIC, CDI, IPCA, USD/BRL
- **Top Candidatos** — ranking Logan com scores e critérios aprovados
- **Notícias (last30days)** — uma seção por candidato com os destaques dos últimos 30 dias
- **Sua Carteira** — posições atuais ou "Carteira vazia — primeiro aporte"
- **Recomendação do Mês** — ticker + quantidade de ações + preço estimado + justificativa
