# Plano e Relatório de Teste de Desempenho

Equipe: Renato de Paiva Belarmino e Alisson Gabriel   Pacote/Projeto: Pacote A – Desafio A (abertura da matrícula)   Data: 17/11/2026

## 1. Plano (preencher ANTES de executar)

| Item | Preenchimento |
|---|---|
| Pergunta / hipótese | Com 100 alunos por 2 min, a matrícula atende p95 geral ≤ 800 ms, p95 do comprovante ≤ 1,5 s e erros técnicos < 1%, sem vagas negativas? Até quantos alunos aguenta? |
| Operações testadas e proporção | `GET /api/disciplinas`, `POST /api/matriculas` e `GET /api/matriculas/<id>/comprovante`, com pesos 5 / 3 / 2 (justificativa abaixo) |
| Verificações de conteúdo | Oferta: 200, 7 disciplinas, `vagas` inteiro ≥ 0. Matrícula 201: `id`, o mesmo aluno, as mesmas disciplinas e comprovante `COMP-NNNNNN`. Comprovante: 200, o mesmo `id`, formato `COMP-NNNNNN`. 409 e 422 são regra de negócio, marcados como sucesso e contados à parte. Erro técnico: 5xx, timeout (> 10 s), 401 ou resposta incoerente. No fim: vagas finais = vagas iniciais − matrículas 201, por disciplina, e nenhum aluno com duas matrículas (R6) |
| Think time (pausa entre ações) | 1 a 4 s (leitura da oferta e escolha das disciplinas) |
| Massa de dados | Um aluno diferente por usuário virtual (20260001 a 20260200). De 2 a 4 disciplinas sorteadas **entre as que têm vaga e sem choque de horário**. Acima de 200 usuários, o aluno se repete, representando o mesmo aluno numa segunda aba |
| Perfis (usuários, ritmo, duração) | Carga: rampa de 10 s até 100 alunos, mais 120 s com 100. Estresse: degraus de +50 alunos a cada 30 s (50, 100, …, 400). Pico: 0 → 200 alunos em 10 s, 60 s com 200, depois 30 s com 20. Recuperação: os 30 s finais do pico, com 20 alunos |
| Repetições | 3 de cada tipo (`carga_r1`, `carga_r2`, `carga_r3`…), mais uma verificação com 1 aluno por 15 s |
| Metas (SLA) | p95 geral ≤ 800 ms; p95 do comprovante ≤ 1500 ms; erros técnicos < 1%; outras: nunca vaga negativa |
| Critério de parada | Interromper se a máquina ficar instável, se os erros técnicos passarem de 20% por 10 s ou se o p95 geral passar de 2000 ms por 10 s. Neste script o acompanhamento é feito pelo terminal (não há parada automática). Não é obrigatório derrubar o sistema |

**Justificativa da proporção:**
- **Consultar a oferta (peso 5):** é o mais comum. Na abertura, o aluno atualiza a página para ver as vagas, e quem já se matriculou ou desistiu continua só consultando.
- **Matricular (peso 3):** acontece **uma vez por aluno**. Se a vaga acaba entre a consulta e o envio (409), o aluno consulta de novo e tenta outra combinação, até 3 vezes.
- **Comprovante (peso 2):** só existe depois da matrícula, e cada aluno baixa **no máximo 2 vezes**.

Quando a ação sorteada não faz sentido naquele momento (por exemplo, o comprovante antes da matrícula), o aluno consulta a oferta. Por isso a proporção medida muda ao longo do teste; ela está nos `*_stats.csv`.

## 2. Ambiente

| Item | Valor |
|---|---|
| Processador / memória | Intel Core i7-13620H (16 threads) / 15 GiB |
| Sistema operacional | Ubuntu 24.04.5 LTS (kernel 7.0) |
| Python ou JDK (versão) | Python 3.12.3 (Flask 3.1.3) |
| Ferramenta e versão (Locust/Gatling) | Locust 2.47.0 |
| Servidor e gerador de carga na mesma máquina? | Sim (os dois disputam a CPU). Servidor de desenvolvimento do Flask, dados em memória, endereço `127.0.0.1` |

## 3. Resultados

- **Registro por execução:** [`registro_resultados.csv`](../../resultados/pacote-A-desafio/registro_resultados.csv), no formato do modelo.
- **Comparação das repetições:** [`comparacao.md`](../../resultados/pacote-A-desafio/comparacao.md).
- **Tabela por patamar de cada execução:** `*_patamares.md`.
- **Gráficos:** os `*.html` do Locust (p95, req/s e usuários ao longo do tempo) e as Figuras 1 e 2 do `relatorio.pdf`.

Execução inteira, valores r1 / r2 / r3:

| Teste | p95 geral (≤ 800 ms) | p95 comprovante (≤ 1500 ms) | Vazão | Erros técnicos (< 1%) | Integridade | SLA |
|---|---|---|---|---|---|---|
| Carga (100 alunos, 2 min) | 55 / 55 / 55 ms | **4700 / 5000 / 5500 ms** | 38 req/s | 0% | OK nas 3 | **não atendido** (3 de 3) |
| Pico (0 → 200 em 10 s) | 55 / 57 / 55 ms | **7900 / 6800 / 5600 ms** | 53 req/s | 0% | OK nas 3 | **não atendido** (3 de 3) |
| Estresse (50 → 400) | 32 / 31 / 30 ms | 1400 / 1500 / 1100 ms | 89 req/s | 0% | OK nas 3 | atendido no agregado (3 de 3), no limite |

- **Outros endpoints:** oferta com p95 entre 27 e 30 ms e matrícula entre 59 e 71 ms, nas 9 execuções.

Pior p95 do comprovante (janela móvel de cerca de 10 s), por quantidade de alunos simultâneos, r1 / r2 / r3:

| Alunos | Carga (rampa de 10 s) | Pico (rampa de 10 s) | Estresse (degraus de 30 s) |
|---|---|---|---|
| 50 | 490 ms (r2) | – | 670 / 1200 / 1200 ms |
| 80–90 | 560 / 490 / 350 ms | – | – |
| **100** | **5000 / 5400 / 5900 ms** | 260 ms (ainda subindo) | 1200 / 1200 / 1100 ms |
| 180 | – | 670 / 660 / 840 ms | – |
| **200** | – | **8300 / 7600 / 5900 ms** | 260 / 440 / 260 ms |
| **250–300** | – | – | **2300 / 2300 / 2300 ms** |
| 400 | – | – | 260 ms |

- **Integridade:** nas 9 execuções, as vagas finais bateram exatamente com `inicial − matrículas 201` em todas as disciplinas. Nenhuma ficou negativa e nenhum aluno foi matriculado duas vezes. De 84 a 89 matrículas foram efetivadas por execução, antes de as 230 vagas acabarem.
- **Execução exploratória:** a que antecedeu as repetições deu 2300 ms no p95 agregado do comprovante no estresse. Ela foi substituída pela r1 atual.

## 4. Análise

**A meta foi atendida em cada teste? Em qual patamar deixou de ser?**
- **Carga e pico: não**, nas 3 repetições, sempre por causa do comprovante, que levou de 4,7 a 7,9 s.
- **Estresse:** atendido no agregado, mas no limite (1,1 a 1,5 s), com momentos de 2,3 s nos degraus de 250 e 300 alunos. Não dá para afirmar que atende com segurança.
- O p95 geral (cerca de 55 ms) e a taxa de erros (0%) passaram com folga em tudo. Mais de 90% das requisições são consultas rápidas à oferta, então **o agregado esconde o gargalo**.

**Qual endpoint piora primeiro? A vazão parou de crescer em algum ponto?**
- **O comprovante.** A piora não depende do total de alunos conectados, e sim de **quantos se matriculam ao mesmo tempo**:
  - na carga, os 100 entram em 10 s e se matriculam quase juntos, e o comprovante passa de cerca de 500 ms (com 80–90 alunos) para **5 a 6 s ao chegar a 100**;
  - no estresse, os alunos entram em degraus de 50 e o comprovante fica em cerca de 1,2 s.
- **Resposta direta:** o comprovante deixa de atender quando **entre 50 e 100 alunos se matriculam juntos**.
- **Vazão:** a do comprovante ficou em cerca de **4 por segundo**, com 1 ou com 400 alunos conectados. A da oferta cresceu de 16 para 156 req/s no estresse, sem degradar (cerca de 28 ms); a matrícula ficou em cerca de 60 ms.
- **Hipótese de causa** (interpretação, coerente com todos os números): cada comprovante leva cerca de 250 ms e é gerado **um de cada vez**, o que limita a vazão a 4 por segundo e forma fila acima disso.

**O sistema se recuperou após o estresse? Em quanto tempo?**
- Sim. Nos 30 s finais do pico, com 20 alunos, o comprovante voltou para 250–260 ms e a oferta para 27 ms, nas 3 repetições (`pico_r*_patamares.md`, linha de 20 alunos). Esvaziada a fila de comprovantes, não sobra degradação.
- Limitação: nesse trecho houve poucos pedidos de comprovante (a maioria dos alunos já tinha baixado), então o tempo exato de recuperação não pode ser medido com precisão.

**As repetições deram resultados parecidos? O que explica as diferenças?**
- **Oferta, matrícula, erros e integridade:** praticamente idênticos nas três.
- **Comprovante:** variou entre 8% (carga) e 17% (pico e estresse) da média. Isso é esperado: o tamanho da fila depende de quantos alunos, por sorteio, se matriculam no mesmo segundo.
- A conclusão "carga e pico não atendem" se manteve em 3 de 3. No estresse, a variação é o que torna o resultado inconclusivo.

## 5. Limitações e recomendações

**Limitações:**
- **As vagas acabam no primeiro minuto.** São 230 vagas e cada aluno escolhe de 2 a 4 disciplinas, então só de 84 a 89 alunos se matriculam. Depois disso, a carga vira quase só consulta, e o estresse não mostra até quantos alunos o POST de matrícula aguentaria com mais vagas.
- Acima de 200 usuários virtuais, os alunos se repetem, porque o sistema só tem 200 alunos.
- Cada aluno baixa o comprovante no máximo 2 vezes. Com mais downloads por aluno, o gargalo apareceria antes.
- O p95 por patamar vem da janela móvel de 10 s do Locust e é aproximado. Os p95 da execução inteira são os do relatório final do Locust.
- Servidor de desenvolvimento do Flask, com servidor e gerador de carga na mesma máquina.

**Recomendações:**
1. Gerar o comprovante **uma vez, no momento da matrícula**, e guardar o resultado. Os downloads seguintes só devolvem o arquivo pronto.
2. Se a geração precisar continuar sob demanda, usar **vários geradores em paralelo** ou uma **fila assíncrona** ("comprovante em preparação").
3. Enquanto isso, **escalonar a abertura** por período ou curso. O estresse mostrou que, com os alunos entrando em levas de 50, o comprovante fica perto da meta.
4. Repetir os testes depois da mudança, para confirmar p95 ≤ 1,5 s com 100 e 200 alunos.
