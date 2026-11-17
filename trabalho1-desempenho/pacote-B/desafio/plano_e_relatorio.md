# Plano e Relatório de Teste de Desempenho

Equipe: Renato de Paiva Belarmino e Alisson Gabriel   Pacote/Projeto: Pacote B – Desafio B (consulta de minicursos)   Data: 17/11/2026

## 1. Plano (preencher ANTES de executar)

| Item | Preenchimento |
|---|---|
| Pergunta / hipótese | Com 20 usuários, a consulta de minicursos atende p95 ≤ 500 ms e falhas ≤ 1%? Qual o primeiro patamar que viola a meta? Depois do estresse, o sistema volta às metas em até 30 s? |
| Operações testadas e proporção | `GET /api/cursos` com peso 7 (70%) e `GET /api/cursos/1` com peso 3 (30%), como pede o guia. O peso define probabilidade, então a proporção medida é conferida no resumo |
| Verificações de conteúdo | Listagem: HTTP 200, `total` = 3 e exatamente os cursos 1 Python, 2 Java e 3 Testes de Software. Detalhe: HTTP 200, `id` = 1, `nome` = Python, `vagas` = 2. Status 503, timeout (> 5 s) ou conteúdo diferente contam como falha |
| Think time (pausa entre ações) | 0,2 a 0,6 s (`between(0.2, 0.6)`, o mesmo do exemplo resolvido) |
| Massa de dados | Somente leitura, sem dados por usuário. O estado do sistema não muda durante o teste |
| Perfis (usuários, ritmo, duração) | Verificação: 1 usuário, r=1, 15 s. Referência: 5, r=1, 90 s. Carga: 20, r=2, 90 s. Estresse: 50 (r=5) e 100 (r=10), 90 s cada. Pico: não se aplica a este desafio. Recuperação: 20, r=2, 90 s, logo depois do estresse; e um perfil contínuo opcional de 100 para 20 usuários, sem reiniciar o Locust |
| Repetições | 3 por fase, com nome de arquivo diferente em cada uma (`carga20_r1`, `carga20_r2`…) |
| Metas (SLA) | p95 ≤ 500 ms; falhas ≤ 1% (com 20 usuários); outras: voltar a essas metas em até 30 s com 20 usuários depois do estresse |
| Critério de parada | Automático no script: falhas > 20% ou p95 > 2000 ms por 10 s seguidos. A execução é encerrada e o motivo fica em `<fase>_protecao.txt` |

**Como cada fase é medida:**
- **Agregado:** a execução inteira, incluindo a rampa. Vem do `*_stats.csv`.
- **Patamar:** do instante em que todos os usuários estão ativos até o fim. Vem do `*_stats_history.csv`, como o README do pacote recomenda. Requisições, req/s e % de falhas são exatos. O p95 do patamar é a mediana do p95 da janela móvel de 10 s do Locust, descartando os 10 s iniciais.
- **Decisão:** a fase **atende** se o patamar tiver falhas ≤ 1% e p95 ≤ 500 ms.

**Como a recuperação é medida:**
- **`recuperacao20`:** uma execução separada, logo depois do estresse com 100. Mede o tempo até todas as janelas seguintes atenderem às metas. Entre uma execução e outra, o Locust reinicia (cerca de 2 s sem carga).
- **`continuo100para20`:** 100 usuários e, sem parar, 20. Mede o tempo desde a queda para 20 até as metas voltarem.
- A janela de 10 s do Locust atrasa a medida em até 10 s, então o tempo medido é **conservador**: o real é igual ou menor.

## 2. Ambiente

| Item | Valor |
|---|---|
| Processador / memória | Intel Core i7-13620H (16 threads) / 15 GiB |
| Sistema operacional | Ubuntu 24.04.5 LTS |
| Python ou JDK (versão) | Python 3.12.3 |
| Ferramenta e versão (Locust/Gatling) | Locust 2.47.0 |
| Servidor e gerador de carga na mesma máquina? | Sim. Sistema B: `app.py` do kit (`ThreadingHTTPServer`), `DATA_SIZE` = 100 (padrão), endereço `127.0.0.1` |

## 3. Resultados

- **Registro por execução:** [`registro_resultados.csv`](../../resultados/pacote-B-desafio/registro_resultados.csv), no formato do modelo.
- **Tabela completa:** [`resumo.md`](../../resultados/pacote-B-desafio/resumo.md).
- **Gráficos:** os `*.html` do Locust e a Figura 2 do `relatorio.pdf`.

Patamar, depois da rampa:

| Fase | Usuários | req/s (r1 / r2 / r3) | Falhas (r1 / r2 / r3) | p95 (r1 / r2 / r3) | Decisão |
|---|---|---|---|---|---|
| Verificação | 1 | 2,3 / 2,3 / 2,4 | 0% / 0% / 0% | 36 / 37 / 35 ms | atende |
| Referência | 5 | 11,3 / 11,6 / 11,6 | 0% / 0% / 0% | 36 / 37 / 36 ms | atende |
| **Carga nominal** | **20** | 46,1 / 45,7 / 46,2 | **0% / 0% / 0%** | **36 / 37 / 36 ms** | **atende** |
| Estresse 1 | 50 | 112,8 / 112,2 / 111,0 | 0,02% / 0,01% / 0,02% | 72 / 70 / 69 ms | atende |
| **Estresse 2** | **100** | 195,3 / 193,4 / 196,0 (oferecidas) | **32,6% / 32,1% / 32,9%** | 130 / 130 / 130 ms | **não atende**, proteção acionada aos 24–25 s |
| Recuperação | 20 | 45,9 / 46,1 / 46,5 | 0% / 0% / 0% | 37 / 37 / 37 ms | atende |

- **Falhas no estresse 2:** todas foram `HTTP 503` ("Capacidade didática ocupada"). Não houve timeout nem conteúdo errado.
- **Mistura medida na carga de 20 usuários:** `GET /api/cursos` 69,7% e `GET /api/cursos/1` 30,3%.
- **Recuperação:**
  - `recuperacao20`, logo depois do estresse 2: metas atendidas em 3–4 s;
  - perfil contínuo de 100 para 20: metas atendidas **12 s** depois da queda, nas 3 repetições.
- **Aviso sobre os logs:** os `continuo100para20_r*.log` dizem "INTERROMPIDA", mas a proteção só reduziu a carga para 20 e o teste seguiu. Esses logs foram gerados antes de a mensagem do script ser corrigida.

## 4. Análise

**A meta foi atendida em cada teste? Em qual patamar deixou de ser?**
- Na **carga nominal**, sim, com folga, nas 3 repetições: p95 de 36–37 ms e 0% de falhas.
- O primeiro patamar que viola a meta é o **estresse 2, com 100 usuários**, nas 3 repetições. Com 50, a meta ainda é atendida, mas aparecem os primeiros sinais de saturação: o p95 dobra (36 → 70 ms) e surgem as primeiras falhas (0,02%).

**Qual endpoint piora primeiro? A vazão parou de crescer em algum ponto?**
- Os dois endpoints pioram juntos, porque disputam o mesmo limite do servidor: no máximo 4 consultas ao mesmo tempo, com cerca de 30 ms cada. Isso dá um teto de uns **133 respostas/s**.
- Com 100 usuários chegaram cerca de 195 req/s. As respostas com sucesso ficaram perto de 131/s (195 × 67%), praticamente no teto: **a vazão útil parou de crescer**, e o excedente recebeu 503.
- O sistema **recusa em vez de ficar lento**: o p95 ficou baixo (130 ms) mesmo com 33% de falhas. Olhar só o tempo esconderia o problema.
- Estimativa (interpretação): pela vazão por usuário na carga (cerca de 2,3 req/s), o teto deve ser atingido perto de **58 usuários**, coerente com 50 passarem e 100 não.

**O sistema se recuperou após o estresse? Em quanto tempo?**
- Sim, dentro da meta de 30 s: 12 s no perfil contínuo e 3–4 s na fase separada. Os números incluem o atraso da janela de 10 s do Locust, então a recuperação real é quase imediata. Como o servidor recusa o excedente em vez de enfileirar, não sobra fila para esvaziar.

**As repetições deram resultados parecidos? O que explica as diferenças?**
- Sim. Em todas as fases, req/s, falhas e p95 variaram muito pouco entre r1, r2 e r3 (falhas com 100 usuários entre 32,1% e 32,9%). Como o limite é fixo e não há dados mudando, o comportamento é bem previsível.

## 5. Limitações e recomendações

**Limitações:**
- O limite de 4 consultas e os 30 ms por chamada são **artificiais**: o README do pacote avisa que servem para estudar métricas, não para estimar capacidade real.
- O servidor e o gerador de carga rodam na mesma máquina.
- O p95 do patamar é aproximado (mediana da janela de 10 s do Locust). Requisições, req/s e % de falhas são exatos.
- O estresse 2 foi interrompido aos 24–25 s pela proteção, então o patamar de 100 usuários teve só uns 15 s de medição depois da rampa.
- Na fase `recuperacao20`, o Locust reinicia entre o estresse e a recuperação. Por isso a recuperação também foi medida com o perfil contínuo.

**Recomendações:**
- Se a demanda real passar de uns 50 usuários simultâneos, aumentar a capacidade da consulta: mais consultas simultâneas ou cache da listagem de cursos, que muda pouco e é 70% do tráfego.
- Do lado do cliente, tratar o 503 com uma nova tentativa depois de uma pausa curta.
