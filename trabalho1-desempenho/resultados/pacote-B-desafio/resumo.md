# Desafio B – resultados por execução

| Fase | Rep. | Agregado: req · p50 · p95 · req/s · falhas | Patamar: req/s · falhas · p95 (mediana / máx. da janela) | Decisão |
|---|---|---|---|---|
| verificacao1 | r1 | 33 · 35 · 36 ms · 2.4 · 0.00% | 2.3 · 0.00% · 36 / 36 ms | atende |
| verificacao1 | r2 | 33 · 36 · 37 ms · 2.4 · 0.00% | 2.3 · 0.00% · 37 / 37 ms | atende |
| verificacao1 | r3 | 33 · 34 · 35 ms · 2.4 · 0.00% | 2.4 · 0.00% · 35 / 35 ms | atende |
| referencia5 | r1 | 999 · 35 · 36 ms · 11.2 · 0.00% | 11.3 · 0.00% · 36 / 36 ms | atende |
| referencia5 | r2 | 1013 · 36 · 37 ms · 11.3 · 0.00% | 11.6 · 0.00% · 37 / 37 ms | atende |
| referencia5 | r3 | 1014 · 34 · 36 ms · 11.4 · 0.00% | 11.6 · 0.00% · 36 / 37 ms | atende |
| carga20 | r1 | 3908 · 34 · 36 ms · 43.8 · 0.00% | 46.1 · 0.00% · 36 / 41 ms | atende |
| carga20 | r2 | 3864 · 35 · 37 ms · 43.3 · 0.00% | 45.7 · 0.00% · 37 / 38 ms | atende |
| carga20 | r3 | 3909 · 33 · 36 ms · 43.9 · 0.00% | 46.2 · 0.00% · 36 / 39 ms | atende |
| estresse50 | r1 | 9559 · 39 · 71 ms · 107.2 · 0.02% | 112.8 · 0.02% · 72 / 81 ms | atende |
| estresse50 | r2 | 9515 · 39 · 71 ms · 106.7 · 0.01% | 112.2 · 0.01% · 70 / 85 ms | atende |
| estresse50 | r3 | 9533 · 39 · 70 ms · 106.9 · 0.02% | 111.0 · 0.02% · 69 / 78 ms | atende |
| estresse100 | r1 | 3876 · 110 · 130 ms · 161.3 · 26.88% | 195.3 · 32.63% · 130 / 130 ms | nao atende (proteção) |
| estresse100 | r2 | 4023 · 110 · 130 ms · 160.6 · 26.22% | 193.4 · 32.09% · 130 / 130 ms | nao atende (proteção) |
| estresse100 | r3 | 3883 · 110 · 130 ms · 161.5 · 26.96% | 196.0 · 32.94% · 130 / 130 ms | nao atende (proteção) |
| recuperacao20 | r1 | 3897 · 34 · 37 ms · 43.7 · 0.00% | 45.9 · 0.00% · 37 / 39 ms | atende |
| recuperacao20 | r2 | 3901 · 34 · 37 ms · 43.8 · 0.00% | 46.1 · 0.00% · 37 / 39 ms | atende |
| recuperacao20 | r3 | 3935 · 34 · 37 ms · 44.2 · 0.00% | 46.5 · 0.00% · 37 / 40 ms | atende |
| continuo100para20 | r1 | 8175 · 37 · 130 ms · 71.5 · 13.52% | - · -% · - / - ms | - (proteção) |
| continuo100para20 | r2 | 8410 · 37 · 130 ms · 72.9 · 13.95% | - · -% · - / - ms | - (proteção) |
| continuo100para20 | r3 | 8171 · 36 · 130 ms · 71.5 · 13.18% | - · -% · - / - ms | - (proteção) |

**Mistura medida na carga de 20 usuários (todas as repetições):** GET /api/cursos 69.7%, GET /api/cursos/1 30.3%

## Primeiro patamar que viola a meta

- referencia5: atende, atende, atende
- carga20: atende, atende, atende
- estresse50: atende, atende, atende
- estresse100: nao atende, nao atende, nao atende

**Resultado:** o primeiro patamar que viola a meta (na maioria das repetições) é **estresse100**.

## Recuperação (meta: voltar a p95 <= 500 ms e falhas <= 1% em até 30 s, com 20 usuários)

- recuperacao20 r1: atendeu às metas após 4 s desde o início da execução → dentro da meta
- recuperacao20 r2: atendeu às metas após 3 s desde o início da execução → dentro da meta
- recuperacao20 r3: atendeu às metas após 3 s desde o início da execução → dentro da meta
- continuo100para20 r1: atendeu às metas após 12 s desde a queda para 20 usuários (queda em t=26 s) → dentro da meta
- continuo100para20 r2: atendeu às metas após 12 s desde a queda para 20 usuários (queda em t=27 s) → dentro da meta
- continuo100para20 r3: atendeu às metas após 12 s desde a queda para 20 usuários (queda em t=26 s) → dentro da meta

_Registro gravado em registro_resultados.csv_
