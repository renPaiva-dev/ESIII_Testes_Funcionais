# Plano e Relatório de Teste de Desempenho

Equipe: Renato de Paiva Belarmino e Alisson Gabriel   Pacote/Projeto: Projeto anterior – Estoque Fácil (Flask + SQLite)   Data: 17/11/2026

## 1. Plano (preencher ANTES de executar)

**Contexto.** O Estoque Fácil atende uma papelaria com cerca de **1.000 itens** cadastrados. No pico (começo do ano letivo), operadores consultam produtos no balcão e registram entradas (recebimento) e saídas (venda ou requisição), e o gerente acompanha o relatório do estoque.

| Item | Preenchimento |
|---|---|
| Pergunta / hipótese | Com a carga nominal (20 usuários), as operações respondem rápido o bastante para não travar o atendimento, sem erro e sem quebrar o saldo? Até quantos usuários simultâneos o sistema aguenta? Depois de uma sobrecarga, ele volta ao normal? |
| Operações testadas e proporção | Perfil Operador (90% dos usuários): login pela tela uma vez por sessão; busca de produto (peso 5, 20% com o filtro "só estoque baixo"); consulta de produto e histórico (peso 2); entrada ou saída de 1 a 10 unidades, metade de cada (peso 3). Perfil Gerente (10%): relatório do estoque |
| Verificações de conteúdo | Login: 302 para `/produtos`. Busca: 200, no máximo 20 itens, página 1, todo item contém o termo, filtro de baixa respeitado. Consulta: 200, mesmo `id`, saldo ≥ 0, histórico com no máximo 50 itens em ordem decrescente. Movimentação: 201 com o mesmo produto, tipo e quantidade, `saldo_apos` ≥ 0; **409 "Estoque insuficiente" é regra de negócio** e é contado à parte. Relatório: 200, `total_produtos` = 1000, valores ≥ 0. No fim: para os 1.000 produtos, `saldo final = inicial + entradas aceitas − saídas aceitas`, nunca negativo |
| Think time (pausa entre ações) | Operador: 1 a 3 s (olhar a tela, pegar o produto, digitar). Gerente: 3 a 8 s |
| Massa de dados | 1.000 produtos gerados (`SEED_PRODUTOS=1000`). Banco zerado no início de cada fase, **exceto na recuperação**, que começa com o banco deixado pelo estresse. Termos de busca sorteados de uma lista de itens de papelaria |
| Perfis (usuários, ritmo, duração) | Verificação: 1 usuário, 15 s. Referência: 5, r=1, 90 s. Carga: 20, r=2, 90 s. Estresse: 200 (r=20), 400 (r=40), 800 (r=80) e 1200 (r=100), 90 s cada. Pico: não planejado para o projeto. Recuperação: 20, r=2, 90 s, logo depois do estresse; e um perfil contínuo opcional de 1200 para 20 usuários (90 s + 90 s) |
| Repetições | 3 de cada fase (`carga20_r1`, `carga20_r2`, `carga20_r3`…) |
| Metas (SLA) | p95 da busca ≤ 300 ms; p95 da consulta de produto e histórico ≤ 300 ms; p95 da movimentação ≤ 500 ms; p95 do relatório ≤ 2000 ms; p95 do login ≤ 1000 ms; erros técnicos < 1%; outras: 0 divergências de saldo |
| Critério de parada | Automático no script: erros técnicos acima de 20% ou p95 acima de 2000 ms por 10 s seguidos. O motivo fica em `<fase>_protecao.txt` |

**Justificativa das metas** (premissas da equipe para o contexto da papelaria):

| Meta | Por quê |
|---|---|
| Busca ≤ 300 ms | O operador busca com o cliente esperando no balcão. Até cerca de 0,3 s a resposta parece imediata. É a operação mais frequente |
| Consulta ≤ 300 ms | Mesma situação de balcão; é uma leitura simples, por id |
| Movimentação ≤ 500 ms | O operador espera a confirmação da gravação. A gravação é transacional e serializada (SQLite), então admite um pouco mais que uma leitura |
| Relatório ≤ 2000 ms | Consulta gerencial, feita poucas vezes e fora do atendimento, que percorre todo o estoque |
| Login ≤ 1000 ms | Acontece uma vez por turno. O hash `scrypt` é lento de propósito (segurança) |
| Erros técnicos < 1% | 5xx (incluindo 503 "Banco de dados ocupado"), timeout acima de 10 s ou conteúdo errado. 409 é regra de negócio |
| 0 divergências | A **RN10** do sistema: o saldo nunca fica negativo |

**Justificativa da proporção:** a busca é o que o balcão mais faz. A movimentação vem em seguida, porque cada venda ou recebimento vira uma movimentação. A consulta detalhada é menos frequente, e o relatório é coisa do gerente, 1 a cada 10 usuários. Entradas e saídas em igual proporção mantêm o estoque estável, então as recusas por falta de saldo não crescem sozinhas.

**Carga nominal:** cerca de 3 lojas × 5 terminais, mais o depósito, ou seja, 20 usuários.

**Sondagem exploratória (antes de fixar os degraus de estresse).** Execuções curtas, de 45 s, para descobrir em que faixa ficava o limite. Os primeiros degraus pensados (50 e 200 usuários) não mostravam degradação:

| Usuários | req/s | p95 busca | p95 movimentação | p95 login | Erros |
|---|---|---|---|---|---|
| 50 | 26 | 9 ms | 19 ms | 150 ms | 0% |
| 200 | 106 | 27 ms | 61 ms | 250 ms | 0% |
| 400 | 210 | 70 ms | 92 ms | 370 ms | 0% |
| 800 | 408 | 370 ms | 510 ms | 650 ms | 0% |
| 1200 | 442 | 1700 ms | 3800 ms | 4500 ms | 0,5% (proteção aos 18 s) |

Por isso o estresse oficial sobe até 1200 usuários.

## 2. Ambiente

| Item | Valor |
|---|---|
| Processador / memória | Intel Core i7-13620H (16 threads) / 15 GiB |
| Sistema operacional | Ubuntu 24.04.5 LTS |
| Python ou JDK (versão) | Python 3.12.3 (Flask 3.1.3) |
| Ferramenta e versão (Locust/Gatling) | Locust 2.47.0 |
| Servidor e gerador de carga na mesma máquina? | Sim. Servidor embutido do Flask (`threaded=True`), um único processo. Banco SQLite em modo WAL, arquivo local, 1.000 produtos. Endereço `127.0.0.1` |

## 3. Resultados

- **Registro por execução:** [`registro_resultados.csv`](../../resultados/projeto-anterior/registro_resultados.csv), no formato do modelo.
- **Tabelas completas:** [`resumo.md`](../../resultados/projeto-anterior/resumo.md).
- **Metas e integridade de cada execução:** `*_metas.csv`.
- **Gráficos:** os `*.html` do Locust e a Figura 3 do `relatorio.pdf`.

A decisão de cada fase usa o **p95 exato da execução inteira**, que inclui a chegada dos usuários. Valores r1 / r2 / r3:

| Fase | Vazão | p95 busca (≤ 300) | p95 movimentação (≤ 500) | p95 relatório (≤ 2000) | p95 login (≤ 1000) | Erros | Decisão |
|---|---|---|---|---|---|---|---|
| Referência (5) | 2,7 req/s | 11 / 9 / 9 ms | 25 / 25 / 24 ms | 12 / 16 / 9 ms | 86 / 99 / 86 ms | 0% | atende 3/3 |
| **Carga nominal (20)** | **10,8 req/s** | **11 / 9 / 10 ms** | **21 / 24 / 23 ms** | 13 / 10 / 10 ms | 120 / 91 / 140 ms | **0%** | **atende 3/3** |
| Estresse 200 | 108 req/s | 16 / 16 / 14 ms | 22 / 42 / 42 ms | 51 / 37 / 29 ms | 280 / 210 / 210 ms | 0% | atende 3/3 |
| Estresse 400 | 216 req/s | 23 / 35 / 16 ms | 76 / 53 / 24 ms | 49 / 53 / 40 ms | 460 / 370 / 350 ms | 0% | atende 3/3 |
| **Estresse 800** | 420 req/s | 110 / 200 / 100 ms | **540 / 1200 / 420 ms** | 63 / 150 / 96 ms | 590 / **1900** / 640 ms | 0% | **não atende 2/3** |
| Estresse 1200 | 590–610 req/s | 210 / 280 / 280 ms | **930 / 2500 / 1800 ms** | 190 / 200 / 220 ms | **1700 / 1600 / 1900 ms** | < 0,01% | não atende 3/3 (r2: proteção aos 79 s) |
| Recuperação (20) | 10,8 req/s | 10 / 9 / 10 ms | 48 / 23 / 23 ms | 23 / 20 / 25 ms | 90 / 94 / 100 ms | 0% | atende 3/3 |

- **Consulta de produto e de histórico:** seguiram a busca e ficaram abaixo de 300 ms até 800 usuários.
- **Linha do tempo (estresse com 800, r1, valores a cada 5 s):**

| t (s) | Usuários | Logins/s | p95 geral (janela) | p95 movimentação (janela) |
|---|---|---|---|---|
| 5–15 | 400 → 800 (chegando) | 49–63 | 570–860 ms | 500–1100 ms |
| 20–35 | 800 | 0 | 25–43 ms | 42–64 ms |
| 40–50 | 800 | 0 | 88–1000 ms | **1400–2800 ms** |
| 55–85 | 800 | 0 | 26–29 ms | 37–46 ms |

- **Com 1200 usuários estáveis** (perfil contínuo, r2): a movimentação teve rajadas de 2,0–2,8 s a cada cerca de 20 s. Entre as rajadas, ficou em 0,2–0,9 s.
- **Erros técnicos:** nenhum 5xx e nenhum 503 em 27 execuções. Só **timeouts isolados** (sem resposta em 10 s) com 1200 usuários: 2 na r1, 1 na r2 e 1 no perfil contínuo r3 (movimentações), e 2 logins no contínuo r1.
- **Integridade:** nenhum saldo negativo em todas as execuções. **Uma** divergência, no estresse com 1200 (r2): o produto 494 terminou com **+6 unidades** além do esperado (inicial 349 − 20 aceitas = 329; final 335). Na mesma execução, **1 movimentação ficou sem resposta** (timeout).
- **Recuperação:**
  - fase `recuperacao20`, com o banco mantido do estresse: metas atendidas em 3–4 s nas 3 repetições;
  - perfil contínuo de 1200 para 20: metas atendidas 4 / 0 / 4 s depois do início da redução.

## 4. Análise

**A meta foi atendida em cada teste? Em qual patamar deixou de ser?**
- Na **carga nominal**, sim, com muita folga, nas 3 repetições: busca em cerca de 10 ms (meta 300) e movimentação em cerca de 23 ms (meta 500), sem erros e sem divergência de saldo.
- As metas continuam atendidas com **400 usuários** (3 de 3) e passam a ser violadas com **800** (2 de 3), principalmente na movimentação e no login. O limite fica **entre 400 e 800 usuários simultâneos**, de 20 a 40 vezes a carga nominal.

**Qual endpoint piora primeiro? A vazão parou de crescer em algum ponto?**
- A **movimentação** e o **login**, por dois efeitos diferentes, visíveis na linha do tempo:
  1. **Chegada em massa.** Enquanto entram de 50 a 80 logins por segundo, todas as operações passam de 0,5–1 s; quando os logins acabam, tudo volta a 25–45 ms. *Hipótese:* o hash `scrypt` do login consome a CPU do mesmo processo que atende as outras requisições.
  2. **Gravações em regime estável.** A partir de 800 usuários, a movimentação tem rajadas de 1,4–3,3 s a cada 20–30 s; as leituras sofrem bem menos. *Hipótese:* o SQLite aceita uma gravação por vez (`BEGIN IMMEDIATE`), e as rajadas são compatíveis com o checkpoint automático do WAL.
  - As duas hipóteses não foram confirmadas com monitoramento de CPU e do banco.
- **Vazão:** cresceu quase linearmente até o fim (11 → 108 → 216 → 420 → cerca de 600 req/s). O sistema não "trava": ele fica lento.
- **Achado de integridade: gravação sem confirmação.** No estresse com 1200, uma entrada de 6 unidades demorou mais de 10 s: o cliente desistiu, mas o servidor gravou. O banco continua coerente (o saldo bate com o histórico), mas o risco é de negócio: o operador acha que não gravou, registra de novo e **duplica** a entrada. Depois dessa execução, o script passou a classificar sozinho esse tipo de divergência como "gravada sem confirmação" (linha `risco` no `*_metas.csv`). Os `*_metas.csv` já gravados são da versão anterior e não têm essa linha.

**O sistema se recuperou após o estresse? Em quanto tempo?**
- Sim. As metas voltam em até 4 s depois que a carga diminui, e em 3–4 s nas execuções com 20 usuários logo depois do estresse. O número inclui o atraso da janela de 10 s do Locust. O banco maior não piorou nada: o relatório, que percorre todo o histórico, ficou em 20–25 ms na recuperação.

**As repetições deram resultados parecidos? O que explica as diferenças?**
- Até 400 usuários, sim: as três repetições ficaram próximas e todas atenderam.
- Com 800, a movimentação variou bastante (540 / 1200 / 420 ms), e a r3 atendeu. A diferença vem das rajadas de gravação: o p95 depende de quantas rajadas caem dentro da execução de 90 s e de quanto cada uma dura. Por isso a decisão foi tomada pela maioria das repetições.

## 5. Limitações e recomendações

**Limitações:**
- **Carga nominal e metas são premissas da equipe** para o contexto de uma papelaria. Os números absolutos dependem dessa hipótese.
- O teste usa a **API** para busca, consulta, movimentação e relatório. As telas HTML não foram medidas, só o login.
- A API não exige login, uma limitação do próprio sistema. O login foi medido pela tela, uma vez por sessão.
- Servidor de desenvolvimento do Flask, com servidor e gerador de carga na mesma máquina.
- O p95 por patamar (`resumo.md`) é aproximado, pela janela de 10 s. A decisão usa o p95 exato da execução inteira.
- A divergência do produto 494 foi analisada a partir do log daquela execução. Ela é explicada pela única movimentação sem resposta: o valor bate (+6 de uma entrada) e não houve outra falha.

**Recomendações.** Para o contexto atual, com cerca de 20 usuários, **nenhuma mudança é necessária**. Se o uso crescer para centenas de usuários simultâneos:
1. **Evitar duplicidade em caso de timeout:** chave de idempotência na movimentação; na tela, depois de um erro, orientar o operador a conferir o histórico antes de repetir.
2. **Servidor de produção com vários processos** (gunicorn ou waitress), para distribuir o custo do `scrypt` e das requisições entre núcleos.
3. **Limitar logins simultâneos ou escalonar a entrada** no início do turno.
4. **Gravações:** investigar o checkpoint do WAL (`wal_autocheckpoint`) e, acima de cerca de 400 usuários, considerar um banco com gravação concorrente, como PostgreSQL.
