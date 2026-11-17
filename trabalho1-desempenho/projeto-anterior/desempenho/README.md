# Projeto anterior – desempenho do Estoque Fácil (Trabalho 1)

Teste de desempenho do sistema da equipe, o **Estoque Fácil** (`../estoque-facil`, Flask + SQLite, porta 5001), feito com Locust (Python).

| Arquivo | Para que serve |
|---|---|
| `locustfile_estoque.py` | Perfis Operador e Gerente, verificações de conteúdo, metas por operação, integridade dos saldos e proteção automática |
| `rodar_fases.sh` | Roda as fases N vezes e guarda as evidências em `../../resultados/projeto-anterior/` |
| `analisar_fases.py` | Gera `resumo.md` e `registro_resultados.csv` (formato do modelo da disciplina) |

## Como rodar

```sh
# terminal 1: Estoque Fácil com 1000 produtos
cd trabalho1-desempenho/projeto-anterior/estoque-facil
SEED_PRODUTOS=1000 python app.py --reset

# terminal 2: testes (venv com locust ativo)
cd trabalho1-desempenho/projeto-anterior/desempenho
./rodar_fases.sh 3                   # 8 fases x 3 repetições (~30 min)
CONTINUO=1 ./rodar_fases.sh 3        # + perfil contínuo 1200 -> 20 usuários (~40 min)
```

O script zera o banco (`POST /api/reset`) no início de cada fase, **exceto na recuperação**, que roda com `RESET=0` para começar com o banco do jeito que o estresse deixou.

## 1. Plano (escrito antes da execução)

### Contexto e pergunta

O Estoque Fácil atende uma papelaria com cerca de **1.000 itens** cadastrados. No pico (começo do ano letivo):
- operadores consultam produtos no balcão e registram entradas (recebimento) e saídas (venda ou requisição);
- o gerente acompanha o relatório do estoque.

**Pergunta:** com a carga nominal, as operações respondem rápido o bastante para não travar o atendimento, sem erro e sem quebrar o saldo? Até quantos usuários simultâneos o sistema aguenta? Depois de uma sobrecarga, ele volta ao normal?

### Operações, proporção e verificações

| Perfil | Operação | Peso | Verificação de conteúdo |
|---|---|---|---|
| Operador (90%) | Login pela tela (`POST /login`), **uma vez** por sessão | – | 302 para `/produtos` |
| | Buscar produto (`GET /api/produtos?q=`), 20% com o filtro "só estoque baixo" | 5 (50%) | 200, no máximo 20 itens, página 1, **todo item contém o termo** no nome ou SKU, filtro de baixa respeitado, situação coerente com a RN11 |
| | Consultar produto e histórico (`GET /api/produtos/<id>` e `/movimentacoes`) | 2 (20%) | 200, mesmo `id`, saldo ≥ 0, situação correta, histórico com no máximo 50 itens em ordem decrescente |
| | Registrar entrada ou saída (`POST /api/produtos/<id>/movimentacoes`), metade de cada, de 1 a 10 unidades | 3 (30%) | 201 com o mesmo produto, tipo e quantidade, e `saldo_apos` ≥ 0. **409 "Estoque insuficiente" é regra de negócio** e é contado à parte |
| Gerente (10%) | Relatório (`GET /api/relatorio`) | 1 | 200, `total_produtos` = 1000, unidades e valor ≥ 0, no máximo 5 "mais saídas" |

- **Proporção:** a busca é o que o balcão mais faz. A movimentação vem em seguida, porque cada venda ou recebimento vira uma movimentação. A consulta detalhada é menos frequente. O relatório é coisa do gerente, 1 a cada 10 usuários.
- **Entradas e saídas em igual proporção:** o estoque fica estável durante o teste. Assim, o número de recusas por falta de saldo não cresce sozinho e não distorce a medição.

### Metas (SLA) e justificativa

| Meta | Valor | Por quê |
|---|---|---|
| p95 da busca | ≤ 300 ms | O operador busca com o cliente esperando no balcão. Até cerca de 0,3 s a resposta parece imediata e não interrompe o atendimento. É a operação mais frequente |
| p95 da consulta de produto e do histórico | ≤ 300 ms | Mesma situação de balcão: é uma leitura simples, por id |
| p95 da movimentação | ≤ 500 ms | O operador espera a confirmação de que a venda ou o recebimento foi gravado. A gravação é transacional e serializada (SQLite), então admite um pouco mais que uma leitura, mas precisa caber em meio segundo para não atrasar a fila |
| p95 do relatório | ≤ 2000 ms | É uma consulta gerencial, feita poucas vezes e fora do atendimento, e percorre todo o estoque e o histórico. Esperar até 2 s é aceitável |
| p95 do login | ≤ 1000 ms | Acontece uma vez por turno. O hash `scrypt` é lento de propósito (segurança), então 1 s é tolerável |
| Erros técnicos | < 1% | 5xx (incluindo 503 "Banco de dados ocupado"), timeout acima de 10 s ou conteúdo errado. Os 409 são regra de negócio e não contam |
| Integridade | 0 divergências | A **RN10** do sistema: o saldo nunca fica negativo. No fim de cada execução, para os 1.000 produtos: `saldo final = saldo inicial + entradas aceitas − saídas aceitas` |

### Perfis de carga

| Fase | Usuários | Ritmo (-r) | Duração | Observação |
|---|---|---|---|---|
| Verificação | 1 | 1 | 15 s | Confere o script |
| Referência | 5 | 1 | 90 s | Movimento fraco |
| **Carga nominal** | **20** | 2 | 90 s | Pico esperado: cerca de 3 lojas × 5 terminais + depósito |
| Estresse | 200 · 400 · 800 · 1200 | 20 · 40 · 80 · 100 | 90 s cada | Degraus escolhidos depois de uma **sondagem exploratória** (abaixo) |
| Recuperação | 20 | 2 | 90 s | Logo depois do estresse, **sem zerar o banco** |
| Contínuo (opcional) | 1200 → 20 | 100 | 90 s + 90 s | Mede a recuperação sem reiniciar o Locust |

- **Think time:** de 1 a 3 s para o operador (olhar a tela, pegar o produto, digitar) e de 3 a 8 s para o gerente.
- **Repetições:** 3 de cada fase.
- **Critério de parada (proteção automática):** erros técnicos acima de 20% ou p95 acima de 2000 ms por 10 s seguidos. A execução é encerrada e o motivo fica em `<fase>_protecao.txt`.

### Sondagem exploratória (antes do plano final)

Execuções curtas, de 45 s, para descobrir em que faixa ficava o limite. Os primeiros degraus planejados (50 e 200 usuários) não mostravam degradação nenhuma:

| Usuários | req/s | p95 busca | p95 movimentação | p95 login | Erros |
|---|---|---|---|---|---|
| 50 | 26 | 9 ms | 19 ms | 150 ms | 0% |
| 200 | 106 | 27 ms | 61 ms | 250 ms | 0% |
| 400 | 210 | 70 ms | 92 ms | 370 ms | 0% |
| 800 | 408 | 370 ms | 510 ms | 650 ms | 0% |
| 1200 | 442 | 1700 ms | 3800 ms | 4500 ms | 0,5% (a proteção parou aos 18 s) |

Por isso, o estresse oficial sobe até 1200 usuários, onde a sondagem mostrou p95 acima de 2 s. Nas execuções oficiais, de 90 s, a vazão continuou crescendo até cerca de 640 req/s. A sondagem com 1200 tinha sido interrompida cedo pela proteção, durante a chegada dos usuários.

## 2. Ambiente

| Item | Valor |
|---|---|
| Processador / memória | Intel Core i7-13620H (16 threads) / 15 GiB |
| Sistema operacional | Ubuntu 24.04.5 LTS |
| Python / Flask / Locust | 3.12.3 / 3.1.3 / 2.47.0 |
| Banco | SQLite em modo WAL, arquivo local, 1.000 produtos (`SEED_PRODUTOS=1000`) |
| Servidor | Servidor embutido do Flask (`threaded=True`), um único processo |
| Servidor e gerador de carga na mesma máquina? | Sim |

## 3. Resultados (3 repetições, 17/11/2026)

Os dados brutos estão em `../../resultados/projeto-anterior/`:
- `resumo.md` traz as tabelas completas;
- `registro_resultados.csv` está no formato do modelo;
- `*_metas.csv`, `*_stats.csv`, `*_stats_history.csv`, `*.html` e `*.log` são de cada execução.

### 3.1 O que foi medido

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

Consulta de produto e consulta de histórico seguiram a busca e ficaram abaixo de 300 ms até 800 usuários.

**Linha do tempo (exemplo: estresse com 800 usuários, r1).** Valores a cada 5 s:

| t (s) | Usuários | Logins/s | p95 geral (janela) | p95 movimentação (janela) |
|---|---|---|---|---|
| 5–15 | 400 → 800 (chegando) | 49–63 | 570–860 ms | 500–1100 ms |
| 20–35 | 800 | 0 | 25–43 ms | 42–64 ms |
| 40–50 | 800 | 0 | 88–1000 ms | **1400–2800 ms** |
| 55–85 | 800 | 0 | 26–29 ms | 37–46 ms |

Com 1200 usuários estáveis (perfil contínuo, r2), a movimentação teve rajadas de 2,0–2,8 s a cada cerca de 20 s (t = 45–57 s e 66–75 s). Entre as rajadas, ficou em 0,2–0,9 s.

**Erros técnicos:** nenhum 5xx e nenhum 503 em 27 execuções. Houve só **timeouts isolados** (sem resposta em 10 s) com 1200 usuários: 2 na r1, 1 na r2 e 1 no perfil contínuo r3 (movimentações), e 2 logins no contínuo r1.

**Integridade:**
- Nenhum saldo negativo em todas as execuções.
- **Uma** divergência, no estresse com 1200 (r2): o produto 494 terminou com **+6 unidades** além do esperado (inicial 349 − 20 aceitas = 329; final 335). Na mesma execução, **1 movimentação ficou sem resposta** (timeout).

**Recuperação:**
- Fase `recuperacao20`, com o banco mantido do estresse: metas atendidas em 3–4 s nas 3 repetições.
- Perfil contínuo de 1200 para 20 usuários: metas atendidas 4 / 0 / 4 s depois do início da redução.

### 3.2 Análise (interpretação)

**As metas foram atendidas na carga nominal?** Sim, com muita folga, nas 3 repetições. Com 20 usuários, a busca respondeu em cerca de 10 ms (meta de 300 ms) e a movimentação em cerca de 23 ms (meta de 500 ms), sem erros e sem divergência de saldo.

**Até onde o sistema aguenta?** As metas continuam sendo atendidas com **400 usuários** (3 de 3) e passam a ser violadas com **800** (2 de 3), principalmente na movimentação e no login. O limite fica **entre 400 e 800 usuários simultâneos**, ou seja, de 20 a 40 vezes a carga nominal. A vazão cresceu quase linearmente até o fim (11 → 108 → 216 → 420 → cerca de 600 req/s). O sistema não "trava": ele fica lento.

**O que piora primeiro?** Dois efeitos diferentes, visíveis na linha do tempo:
1. **A chegada de muitos usuários ao mesmo tempo.**
   - Enquanto entram de 50 a 80 logins por segundo, **todas** as operações passam de 0,5–1 s. Quando os logins acabam, tudo volta a 25–45 ms.
   - *Hipótese:* o hash `scrypt` do login, caro de propósito, consome a CPU do mesmo processo que atende as outras requisições.
   - Na prática, isso só aconteceria se centenas de pessoas entrassem no mesmo minuto. Com 20 usuários e sessões que duram o turno, é improvável.
2. **As gravações em regime estável.**
   - A partir de 800 usuários, a **movimentação** tem rajadas de 1,4–3,3 s a cada 20–30 s. Com 1200, ela fica acima da meta quase o tempo todo. As leituras (busca e consulta) sofrem bem menos.
   - *Hipótese:* o SQLite aceita uma gravação por vez (`BEGIN IMMEDIATE`), então as movimentações formam fila. As rajadas periódicas são compatíveis com o checkpoint automático do WAL, que grava o log no arquivo principal.
   - Para confirmar, seria preciso monitorar o banco durante o teste. Não fizemos isso.

**Achado de integridade: gravação sem confirmação.**
- No estresse com 1200, uma entrada de 6 unidades no produto 494 demorou mais de 10 s. O cliente desistiu e registrou erro, mas **o servidor concluiu e gravou a movimentação**.
- O banco continua coerente: o saldo bate com o histórico. O risco é de **negócio**: o operador vê o erro, acha que não gravou, registra de novo e **duplica** a entrada.
- O script foi melhorado depois dessa execução: agora guarda as movimentações sem resposta e classifica sozinho esse tipo de divergência como "gravada sem confirmação" (linha `risco` no `*_metas.csv`).

**O sistema se recupera?** Sim. Assim que a carga diminui, as metas voltam em até 4 s, e nas execuções com 20 usuários logo depois do estresse, em 3–4 s. Esse número inclui o atraso da janela de 10 s do Locust, então a recuperação real é quase imediata. Também não houve degradação por causa do banco maior: o relatório, que percorre todo o histórico, continuou em cerca de 20–25 ms na recuperação.

### 3.3 Recomendações

Para o contexto atual, com cerca de 20 usuários, **nenhuma mudança é necessária**. A folga é grande. Se o uso crescer para centenas de usuários simultâneos:

1. **Evitar duplicidade em caso de timeout.** Criar uma chave de idempotência na movimentação: o cliente gera um identificador, e o reenvio com o mesmo identificador não grava de novo. Na tela, depois de um erro, orientar o operador a conferir o histórico antes de repetir.
2. **Servidor de produção com vários processos.** Por exemplo, gunicorn ou waitress no lugar do servidor de desenvolvimento do Flask, para distribuir o custo do `scrypt` e das requisições entre núcleos.
3. **Limitar logins simultâneos ou escalonar a entrada**, se houver início de turno com muitas pessoas ao mesmo tempo.
4. **Gravações:** investigar o checkpoint do WAL (`wal_autocheckpoint`) e, se a meta for passar de cerca de 400 usuários, considerar um banco com gravação concorrente, como PostgreSQL.

### 3.4 Limitações

- **Carga nominal e metas são premissas da equipe** para o contexto de uma papelaria. Os números absolutos dependem dessa hipótese.
- O teste usa a **API** para busca, consulta, movimentação e relatório. As telas HTML (templates Jinja) não foram medidas, só o login. Na vida real, o uso é pelas telas, e cada página renderizada custa um pouco mais.
- A API não exige login, uma limitação do próprio sistema. O login foi medido pela tela, uma vez por sessão.
- Servidor de desenvolvimento do Flask, com servidor e gerador de carga na mesma máquina.
- O p95 do patamar (`resumo.md`) é aproximado, pela janela de 10 s. A decisão usa o p95 exato da execução inteira.
- As hipóteses sobre o `scrypt` e o checkpoint do WAL não foram confirmadas com monitoramento de CPU e do banco.
- A divergência do produto 494 foi analisada a partir do log daquela execução, rodada antes da melhoria do script. Ela é explicada pela única movimentação sem resposta: o valor bate (+6 de uma entrada) e não houve outra falha.
