# Desafio B – Consulta de minicursos (Trabalho 1)

Teste de desempenho da consulta de minicursos do sistema B (`http://127.0.0.1:8000`), feito com Locust (Python).

| Arquivo | Para que serve |
|---|---|
| `desafio_locust.py` | As duas tarefas (pesos 7 e 3), as verificações de conteúdo e a proteção automática |
| `rodar_fases.sh` | Roda as 6 fases do guia N vezes e guarda as evidências em `../../resultados/pacote-B-desafio/` |
| `analisar_fases.py` | Gera `resumo.md` e `registro_resultados.csv` (formato do modelo da disciplina) |

## Como rodar

```sh
# terminal 1: sistema B
cd <kit>/03_Pacote_B_Biblioteca_Minicursos
python app.py

# terminal 2: testes (venv com locust ativo)
cd trabalho1-desempenho/pacote-B/desafio
./rodar_fases.sh 3                  # 6 fases x 3 repetições (~25 min)
CONTINUO=1 ./rodar_fases.sh 3       # + perfil contínuo estresse -> recuperação (~35 min)
python analisar_fases.py ../../resultados/pacote-B-desafio   # refaz só a análise
```

Uma fase isolada, igual ao guia:

```sh
python -m locust -f desafio_locust.py --host http://127.0.0.1:8000 --headless \
  -u 20 -r 2 -t 90s --stop-timeout 5s --csv-full-history --csv carga20_r1 --html carga20_r1.html
```

## 1. Plano (escrito antes da execução)

| Item | Decisão |
|---|---|
| Pergunta | Com 20 usuários, a consulta de minicursos atende p95 ≤ 500 ms e falhas ≤ 1%? Qual o primeiro patamar que viola a meta? Depois do estresse, o sistema volta às metas em até 30 s? |
| Operações e proporção | `GET /api/cursos` com peso 7 (70%) e `GET /api/cursos/1` com peso 3 (30%), como pede o guia. O peso define probabilidade, então a proporção medida é conferida no resumo |
| Verificações | Listagem: HTTP 200, `total` = 3, exatamente os cursos 1 Python, 2 Java e 3 Testes de Software. Detalhe: HTTP 200, `id` = 1, `nome` = Python, `vagas` = 2. Status 503, timeout (> 5 s) ou conteúdo diferente contam como falha |
| Think time | 0,2 a 0,6 s (`between(0.2, 0.6)`, o mesmo do exemplo resolvido) |
| Massa de dados | Somente leitura, sem dados por usuário. O estado do sistema não muda durante o teste |
| Fases | Verificação 1 usuário (r=1, 15 s) · referência 5 (r=1, 90 s) · carga 20 (r=2, 90 s) · estresse 1 com 50 (r=5, 90 s) · estresse 2 com 100 (r=10, 90 s) · recuperação 20 (r=2, 90 s), logo em seguida |
| Repetições | 3 por fase, com nome de arquivo diferente em cada uma (`carga20_r1`, `carga20_r2`…) |
| Metas | p95 ≤ 500 ms e falhas ≤ 1% com 20 usuários. Recuperação: voltar a essas metas em até 30 s com 20 usuários |
| Critério de parada | Automático no script: falhas > 20% ou p95 > 2000 ms por 10 s seguidos. A execução é encerrada e o motivo fica em `<fase>_protecao.txt` |

### Como cada fase é medida

- **Agregado:** a execução inteira, incluindo a rampa. Vem do `*_stats.csv`.
- **Patamar:** do instante em que todos os usuários estão ativos até o fim. Vem do `*_stats_history.csv`, como o README do pacote recomenda.
  - Requisições, req/s e % de falhas são exatos: diferença dos contadores acumulados.
  - O p95 do patamar é a mediana do p95 da janela móvel de 10 s do Locust, descartando os 10 s iniciais.
- **Decisão:** a fase **atende** se o patamar tiver falhas ≤ 1% e p95 ≤ 500 ms.

### Como a recuperação é medida

- **`recuperacao20`:** é uma execução separada, que começa logo depois do estresse 2. Mede-se o tempo até todas as janelas seguintes atenderem às metas.
  - Limitação: entre uma execução e outra o Locust reinicia, uns 2 s sem carga.
- **`continuo100para20` (opcional, `CONTINUO=1`):** 100 usuários e, sem parar, 20 usuários.
  - Mede o tempo desde a queda para 20 até as metas voltarem, sem o intervalo de reinício.
  - Se a proteção disparar durante o estresse, a carga cai para 20 naquele momento.

A janela de 10 s do Locust atrasa a medida em até 10 s. Por isso, o tempo de recuperação medido é **conservador**: o real é igual ou menor.

## 2. Ambiente

| Item | Valor |
|---|---|
| Processador / memória | Intel Core i7-13620H (16 threads) / 15 GiB |
| Sistema operacional | Ubuntu 24.04.5 LTS |
| Python / Locust | 3.12.3 / 2.47.0 |
| Sistema B | `app.py` do kit (biblioteca padrão, `ThreadingHTTPServer`), `DATA_SIZE` = 100 (padrão) |
| Servidor e gerador de carga na mesma máquina? | Sim |

## 3. Resultados (3 repetições, 17/11/2026)

Os dados brutos estão em `../../resultados/pacote-B-desafio/`:
- `resumo.md` traz a tabela completa por execução;
- `registro_resultados.csv` está no formato do modelo;
- `*_stats.csv`, `*_stats_history.csv`, `*.html` e `*.log` são de cada execução.

### 3.1 O que foi medido (patamar, depois da rampa)

| Fase | Usuários | req/s (r1 / r2 / r3) | Falhas (r1 / r2 / r3) | p95 (r1 / r2 / r3) | Decisão |
|---|---|---|---|---|---|
| Verificação | 1 | 2,3 / 2,3 / 2,4 | 0% / 0% / 0% | 36 / 37 / 35 ms | atende |
| Referência | 5 | 11,3 / 11,6 / 11,6 | 0% / 0% / 0% | 36 / 37 / 36 ms | atende |
| **Carga nominal** | **20** | 46,1 / 45,7 / 46,2 | **0% / 0% / 0%** | **36 / 37 / 36 ms** | **atende** |
| Estresse 1 | 50 | 112,8 / 112,2 / 111,0 | 0,02% / 0,01% / 0,02% | 72 / 70 / 69 ms | atende |
| **Estresse 2** | **100** | 195,3 / 193,4 / 196,0 (oferecidas) | **32,6% / 32,1% / 32,9%** | 130 / 130 / 130 ms | **não atende**, proteção acionada aos 24–25 s |
| Recuperação | 20 | 45,9 / 46,1 / 46,5 | 0% / 0% / 0% | 37 / 37 / 37 ms | atende |

Outras medidas:
- **Falhas no estresse 2:** todas foram `HTTP 503` ("Capacidade didática ocupada"). Não houve timeout nem conteúdo errado.
- **Mistura medida na carga de 20 usuários:** `GET /api/cursos` 69,7% e `GET /api/cursos/1` 30,3%. O pedido era 70/30.
- **Recuperação:**
  - execução `recuperacao20`, logo depois do estresse 2: metas atendidas em 3–4 s;
  - perfil contínuo de 100 para 20 usuários, sem reiniciar o Locust: metas atendidas **12 s** depois da queda, nas 3 repetições.
- **Aviso sobre os logs:** os `continuo100para20_r*.log` dizem "INTERROMPIDA", mas a proteção só reduziu a carga para 20, e o teste seguiu. A mensagem já foi corrigida no script.

### 3.2 Análise (interpretação)

**A meta da carga nominal foi atendida?** Sim, com folga, nas 3 repetições: p95 de 36–37 ms (meta ≤ 500 ms) e 0% de falhas.

**Qual o primeiro patamar que viola a meta?** O **estresse 2, com 100 usuários**, nas 3 repetições. Com 50 usuários a meta ainda é atendida, mas aparecem os primeiros sinais de saturação:
- o p95 dobra (36 → 70 ms);
- surgem as primeiras falhas (0,02%).

**Como o sistema degrada?** Ele **recusa em vez de ficar lento**:
- O servidor atende no máximo 4 consultas ao mesmo tempo, com cerca de 30 ms cada. Isso dá um teto de uns **133 respostas/s** (4 ÷ 0,03 s).
- Com 100 usuários chegaram cerca de 195 req/s. As respostas com sucesso ficaram perto de 131/s (195 × 67%), praticamente no teto. O excedente esperou até 100 ms por uma vaga e recebeu 503.
- Por isso o p95 ficou baixo (130 ms) mesmo com 33% de falhas: **erros rápidos convivem com um p95 baixo**. Olhar só o tempo de resposta esconderia o problema.
- Pela vazão por usuário na carga (cerca de 2,3 req/s), o teto deve ser atingido perto de **58 usuários** (133 ÷ 2,3). Isso é coerente com o que foi medido: 50 usuários ainda passam e 100 não.

**O sistema se recuperou?** Sim, dentro da meta de 30 s. No perfil contínuo, as metas voltaram 12 s depois da queda para 20 usuários. Esse número inclui o atraso da janela de 10 s do Locust, então a recuperação real é quase imediata. Faz sentido: como o servidor recusa o excedente em vez de enfileirar, não sobra fila acumulada para esvaziar.

**Recomendações:**
- Se a demanda real passar de uns 50 usuários simultâneos, aumentar a capacidade da consulta, por exemplo com mais consultas simultâneas ou cache da listagem de cursos. Ela muda pouco e é 70% do tráfego.
- Do lado do cliente, tratar o 503 com uma nova tentativa depois de uma pausa curta.

### 3.3 Limitações

- O limite de 4 consultas e os 30 ms por chamada são **artificiais**: o README do pacote avisa que servem para estudar métricas, não para estimar capacidade real.
- O servidor e o gerador de carga rodam na mesma máquina.
- O p95 do patamar é aproximado: mediana da janela de 10 s do Locust, já que o Locust não guarda as amostras individuais. Requisições, req/s e % de falhas são exatos.
- O estresse 2 foi interrompido aos 24–25 s pela proteção, então o patamar de 100 usuários teve só uns 15 s de medição depois da rampa. Mesmo assim, as 3 repetições ficaram muito próximas: falhas entre 32,1% e 32,9%.
- Na fase `recuperacao20`, o Locust reinicia entre o estresse e a recuperação. Por isso a recuperação foi medida também com o perfil contínuo.
