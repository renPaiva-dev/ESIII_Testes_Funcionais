# Desafio A – comparação das repetições

Valores na ordem r1 / r2 / r3. Metas: p95 geral ≤ 800 ms, p95 comprovante ≤ 1500 ms, erros técnicos < 1%, vagas nunca negativas.

| Teste | p95 geral | p95 comprovante | p95 oferta | p95 matrícula | Erros técnicos | Matrículas 201 | Integridade | SLA |
|---|---|---|---|---|---|---|---|---|
| carga | 55 ms / 55 ms / 55 ms | 4700 ms / 5000 ms / 5500 ms | 28 ms / 28 ms / 27 ms | 59 ms / 61 ms / 59 ms | 0.00% / 0.00% / 0.00% | 86 / 84 / 86 | OK | não atendido / não atendido / não atendido |
| pico | 55 ms / 57 ms / 55 ms | 7900 ms / 6800 ms / 5600 ms | 29 ms / 30 ms / 30 ms | 62 ms / 70 ms / 67 ms | 0.00% / 0.00% / 0.00% | 86 / 89 / 85 | OK | não atendido / não atendido / não atendido |
| estresse | 32 ms / 31 ms / 30 ms | 1400 ms / 1500 ms / 1100 ms | 29 ms / 29 ms / 28 ms | 71 ms / 69 ms / 66 ms | 0.00% / 0.00% / 0.00% | 84 / 84 / 85 | OK | atendido / atendido / atendido |

## Variação entre repetições (p95 do comprovante)

- carga: mínimo 4700 ms, máximo 5500 ms, média 5067 ms, desvio padrão 404 ms (8% da média); 3 de 3 acima da meta de 1500 ms
- pico: mínimo 5600 ms, máximo 7900 ms, média 6767 ms, desvio padrão 1150 ms (17% da média); 3 de 3 acima da meta de 1500 ms
- estresse: mínimo 1100 ms, máximo 1500 ms, média 1333 ms, desvio padrão 208 ms (16% da média); 0 de 3 acima da meta de 1500 ms

## Regras de negócio por repetição (não contam como erro)

- carga r1: 409 Vagas esgotadas: 32, desistiu: nenhuma disciplina com vaga na oferta: 13, desistiu: vagas esgotadas após 3 tentativas: 1
- carga r2: 409 Vagas esgotadas: 29, desistiu: nenhuma disciplina com vaga na oferta: 15, desistiu: vagas esgotadas após 3 tentativas: 1
- carga r3: 409 Vagas esgotadas: 32, desistiu: nenhuma disciplina com vaga na oferta: 14
- pico r1: 409 Vagas esgotadas: 70, desistiu: nenhuma disciplina com vaga na oferta: 114
- pico r2: 409 Vagas esgotadas: 91, desistiu: nenhuma disciplina com vaga na oferta: 111
- pico r3: 409 Vagas esgotadas: 73, desistiu: nenhuma disciplina com vaga na oferta: 114
- estresse r1: 409 Vagas esgotadas: 22, desistiu: nenhuma disciplina com vaga na oferta: 230, desistiu: vagas esgotadas após 3 tentativas: 1
- estresse r2: 409 Vagas esgotadas: 41, desistiu: nenhuma disciplina com vaga na oferta: 232
- estresse r3: 409 Vagas esgotadas: 34, desistiu: nenhuma disciplina com vaga na oferta: 228, desistiu: vagas esgotadas após 3 tentativas: 1
