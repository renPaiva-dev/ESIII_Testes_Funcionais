# Desafio A – Abertura da matrícula (Trabalho 1)

Teste de desempenho do módulo **Matrícula Acadêmica** do sistema A (`http://127.0.0.1:5000`), feito com Locust (Python).

| Arquivo | Para que serve |
|---|---|
| `locustfile_matricula.py` | Jornada do aluno, verificações de conteúdo, perfis de carga, checagem do SLA e da integridade das vagas |
| `rodar.sh` | Roda um tipo de teste N vezes e guarda as evidências em `../../resultados/pacote-A-desafio/` |
| `analisar_patamares.py` | Resume o histórico por patamar de alunos e por endpoint (mostra qual piora primeiro) |
| `comparar_repeticoes.py` | Compara r1, r2 e r3 de cada tipo e grava `comparacao.md` (o `rodar.sh` chama sozinho no fim) |

## Como rodar

```sh
# terminal 1: sistema A
cd <kit>/02_Pacote_A_SaborExpress_Matricula/app
python app.py

# terminal 2: testes (venv com locust ativo)
cd trabalho1-desempenho/pacote-A/desafio
./rodar.sh verificacao      # 1 aluno por 15 s: confere o script

# versão curta da carga (40 s, 100 alunos), com a tabela ao vivo, para a apresentação:
TIPO_TESTE=demo python -m locust -f locustfile_matricula.py --host http://127.0.0.1:5000 --headless
./rodar.sh carga 3          # carga_r1, carga_r2, carga_r3
./rodar.sh pico 3
./rodar.sh estresse 3
```

O script zera o sistema (`POST /api/admin/reset`) no início de cada execução. Para desligar esse reset, use `RESET=0`.
Use sempre `127.0.0.1` e não `localhost`. No Linux, `localhost` tenta IPv6 primeiro e cada requisição perde cerca de 2 s, o que falsifica a medição (veja `resultados/pacote-A-exemplo/invalido-localhost-ipv6`).

Cada execução gera os arquivos abaixo:

| Arquivo | Conteúdo |
|---|---|
| `*_stats.csv`, `*.html` | Números finais por endpoint |
| `*_stats_history.csv` | Linha do tempo, por endpoint |
| `*_regras.csv` | SLA, respostas 409/422 e integridade das vagas |
| `*_patamares.md` | Tabela por patamar |
| `*.log` | Saída do terminal |

## 1. Plano (escrito antes da execução)

| Item | Decisão |
|---|---|
| Pergunta | Com 100 alunos por 2 min, a matrícula atende p95 geral ≤ 800 ms, p95 do comprovante ≤ 1,5 s e erros técnicos < 1%, sem vagas negativas? Até quantos alunos aguenta? |
| Operações | `GET /api/disciplinas`, `POST /api/matriculas`, `GET /api/matriculas/<id>/comprovante` |
| Jornada | Cada usuário virtual é **um aluno**. Ele consulta a oferta, se matricula e baixa o comprovante |
| Proporção | Pesos 5 / 3 / 2 (consultar / matricular / comprovante), com condições de jornada (justificativa abaixo) |
| Verificações | Oferta: 200, 7 disciplinas, `vagas` inteiro ≥ 0. Matrícula 201: `id`, mesmo aluno, mesmas disciplinas, comprovante `COMP-NNNNNN`. Comprovante: 200, mesmo `id`, formato `COMP-NNNNNN` |
| Regras de negócio | 409 e 422 são marcados como sucesso no Locust e contados à parte em `*_regras.csv` |
| Erro técnico | 5xx, timeout (> 10 s), 401 ou resposta incoerente |
| Think time | 1 a 4 s entre ações (leitura da oferta e escolha das disciplinas) |
| Massa de dados | Um aluno diferente por usuário virtual (20260001 a 20260200), 2 a 4 disciplinas sorteadas **entre as que têm vaga e sem choque de horário** |
| Carga | Rampa de 10 s até 100 alunos, depois 120 s com 100 |
| Pico | 0 → 200 alunos em 10 s, 60 s com 200, depois 30 s com 20 (recuperação) |
| Estresse | Degraus de +50 alunos a cada 30 s: 50, 100, …, 400 |
| Integridade | No fim, compara as vagas finais com `vagas iniciais − matrículas 201 recebidas`, para cada disciplina. Também confere se nenhum aluno recebeu duas matrículas (R6) |
| Critério de parada | Máquina instável ou erros técnicos acima de 20% por 10 s. Não é obrigatório derrubar o sistema |

### Justificativa da proporção

- **Consultar a oferta (peso 5, a ação mais frequente).** Na abertura, o aluno entra no portal e atualiza a página para ver as vagas. Quem já se matriculou ou desistiu continua só consultando.
- **Matricular (peso 3).** Acontece **uma vez por aluno**. Se uma disciplina esgota entre a consulta e o envio, o aluno recebe 409, consulta de novo e tenta outra combinação, até 3 vezes. Depois disso, desiste.
- **Comprovante (peso 2).** Só existe depois da matrícula, e cada aluno baixa **no máximo 2 vezes**. Um aluno real baixa uma vez e, às vezes, de novo para conferir.

Quando a ação sorteada não faz sentido naquele momento (por exemplo, o comprovante antes da matrícula), o aluno consulta a oferta. Por isso, a proporção real medida não é exatamente 50/30/20: ela muda ao longo do teste, conforme os alunos avançam na jornada. A proporção medida está nos `*_stats.csv`.

### Acima de 200 alunos (estresse)

O sistema só tem 200 alunos. A partir do usuário virtual 201, o aluno se repete: representa o **mesmo aluno numa segunda aba ou aparelho**. Essa sessão extra não se matricula de novo (o aluno já está matriculado) e pode baixar o comprovante, que é exatamente o que um aluno ansioso faria.

## 2. Ambiente

| Item | Valor |
|---|---|
| Processador / memória | Intel Core i7-13620H (16 threads) / 15 GiB |
| Sistema operacional | Ubuntu 24.04.5 LTS (kernel 7.0.0) |
| Python / Flask / Locust | 3.12.3 / 3.1.3 / 2.47.0 |
| Servidor | Servidor de desenvolvimento do Flask (`threaded=True`), dados em memória |
| Servidor e gerador de carga na mesma máquina? | Sim (limitação: os dois disputam a CPU) |

## 3. Resultados (3 repetições, 17/11/2026)

Os dados brutos estão em `../../resultados/pacote-A-desafio/`:
- `comparacao.md` compara as repetições (gerado por `comparar_repeticoes.py`);
- `*_patamares.md` traz a tabela por patamar de cada execução;
- `*_regras.csv` traz o SLA, as respostas 409/422 e a integridade;
- `*_stats.csv`, `*_stats_history.csv`, `*.html` e `*.log` são de cada execução.

### 3.1 O que foi medido

Execução inteira, valores r1 / r2 / r3:

| Teste | p95 geral (≤ 800 ms) | p95 comprovante (≤ 1500 ms) | Erros técnicos (< 1%) | Integridade das vagas | SLA |
|---|---|---|---|---|---|
| Carga (100 alunos, 2 min) | 55 / 55 / 55 ms | **4700 / 5000 / 5500 ms** | 0% / 0% / 0% | OK nas 3 | **não atendido** (3 de 3) |
| Pico (0 → 200 em 10 s) | 55 / 57 / 55 ms | **7900 / 6800 / 5600 ms** | 0% / 0% / 0% | OK nas 3 | **não atendido** (3 de 3) |
| Estresse (50 → 400) | 32 / 31 / 30 ms | 1400 / 1500 / 1100 ms | 0% / 0% / 0% | OK nas 3 | atendido no agregado (3 de 3), no limite |

Outros endpoints, p95 nas 9 execuções: oferta entre 27 e 30 ms, matrícula entre 59 e 71 ms.

Pior p95 do comprovante (janela móvel de cerca de 10 s), por quantidade de alunos simultâneos, r1 / r2 / r3:

| Alunos | Carga (rampa de 10 s) | Pico (rampa de 10 s) | Estresse (degraus de 30 s) |
|---|---|---|---|
| 50 | 490 ms (r2) | – | 670 / 1200 / 1200 ms |
| 80–90 | 560 / 490 / 350 ms | – | – |
| **100** | **5000 / 5400 / 5900 ms** | 260 ms (ainda subindo) | 1200 / 1200 / 1100 ms |
| 180 | – | 670 / 660 / 840 ms | – |
| **200** | – | **8300 / 7600 / 5900 ms** | 260 / 440 / 260 ms |
| **250–300** | – | – | **2300 / 2300 / 2300 ms** (pior de 250 e 300) |
| 400 | – | – | 260 ms |

Integridade: nas 9 execuções, as vagas finais bateram exatamente com `inicial − matrículas 201` em todas as disciplinas. Nenhuma ficou negativa e nenhum aluno recebeu duas matrículas. Foram de 84 a 89 matrículas efetivadas por execução, antes de as 230 vagas acabarem.

Na execução exploratória anterior às repetições, o estresse deu 2300 ms no p95 agregado do comprovante, acima da meta. Ela foi substituída pela r1 atual, mas mostra a mesma instabilidade.

### 3.2 Análise (interpretação)

**O SLA foi atendido?**
- **Carga e pico: não**, nas 3 repetições, sempre por causa do comprovante, que levou de 4,7 a 7,9 s.
- **Estresse: atendido no agregado**, mas no limite (1,1 a 1,5 s). A execução exploratória deu 2,3 s, e em todas as repetições houve momentos de 2,3 s nos degraus de 250 e 300 alunos. Não dá para afirmar que o estresse atende com segurança: o resultado depende de quantos comprovantes chegam juntos.
- O p95 geral (cerca de 55 ms) e a taxa de erros (0%) passaram com folga em tudo. Mais de 90% das requisições são consultas rápidas à oferta, então **o agregado esconde o gargalo**.

**Qual endpoint piora primeiro e a partir de quantos alunos?**
- **O comprovante.** A piora não depende do total de alunos conectados, e sim de **quantos se matriculam ao mesmo tempo**:
  - Na carga, os 100 alunos entram em 10 s e se matriculam quase juntos. O p95 do comprovante sobe de cerca de 500 ms (com 80–90 alunos) para **5 a 6 s ao chegar a 100**.
  - No estresse, os alunos entram em degraus de 50. A rajada é menor e o comprovante fica em cerca de 1,2 s. Ele só volta a estourar (2,3 s) com 250–300 sessões, quando as "segundas abas" pedem comprovantes em massa.
  - Com 200 sessões ou com 400, ele fica em 260 ms, porque nesses momentos quase ninguém está pedindo comprovante.
- **Resposta direta:** o comprovante deixa de atender a meta quando **entre 50 e 100 alunos se matriculam juntos**. Com 50 entrando ao mesmo tempo ele fica perto de 1,2 s; com 100, passa de 5 s.
- **Hipótese para a causa**, coerente com todos os números: o comprovante leva cerca de 250 ms e parece ser gerado **um de cada vez**. Isso limita a vazão a uns 4 comprovantes por segundo, com 1 ou com 400 alunos conectados. Acima disso, forma-se fila e cada aluno espera os anteriores.
- A oferta (cerca de 28 ms até 400 alunos, com vazão crescendo de 16 para 156 req/s) e a matrícula (cerca de 60 ms) não degradaram.

**Que melhoria recomendamos?**
1. Gerar o comprovante **uma vez, no momento da matrícula**, e guardar o resultado. Os downloads seguintes só devolvem o arquivo pronto, já que o comprovante não muda depois de emitido.
2. Se a geração precisar continuar sob demanda, usar **vários geradores em paralelo** ou uma **fila assíncrona**, que responde "comprovante em preparação" e avisa quando ficar pronto.
3. Como medida operacional enquanto isso, **escalonar a abertura**: por exemplo, liberar por período ou curso em janelas de alguns minutos. O estresse mostrou que, com os alunos entrando em levas de 50, o comprovante fica perto da meta.
4. Repetir os testes depois da mudança para confirmar p95 ≤ 1,5 s com 100 e 200 alunos.

**As repetições foram parecidas?**
- **Oferta, matrícula, erros e integridade:** praticamente idênticos nas três.
- **Comprovante:** variou entre 8% (carga) e 17% (pico e estresse) da média. Isso é esperado, porque o tamanho da fila depende de quantos alunos, por sorteio, se matriculam no mesmo segundo.
- A conclusão "carga e pico não atendem" se manteve em 3 de 3. No estresse, a variação é justamente o que torna o resultado inconclusivo.

### 3.3 Limitações

- **As vagas acabam no primeiro minuto.** São 230 vagas e cada aluno escolhe de 2 a 4 disciplinas, então só de 84 a 89 alunos se matriculam. Depois disso, a carga vira quase só consulta à oferta. Por isso o estresse não mostra até quantos alunos o POST de matrícula aguentaria com mais vagas.
- Acima de 200 usuários virtuais os alunos se repetem (segunda aba), porque o sistema só tem 200 alunos.
- Cada aluno baixa o comprovante no máximo 2 vezes. Com mais downloads por aluno, o gargalo apareceria antes.
- O p95 por patamar vem da janela móvel de 10 s do Locust, que é aproximada. Os p95 da execução inteira são os do relatório final.
- Servidor de desenvolvimento do Flask, com servidor e gerador de carga na mesma máquina.
