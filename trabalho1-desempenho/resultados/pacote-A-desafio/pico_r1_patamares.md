Arquivo: pico_r1_stats_history.csv
p95 em ms (mediana da janela no patamar) | req/s | falhas/s   (* = acima da meta)

| Alunos | GET /api/disciplinas | GET /api/matriculas/[id]/comprovante | POST /api/matriculas | Aggregated |
|---|---|---|---|---|
| 20 | 27 \| 23.7 \| 0.0 | 250 \| 0.1 \| 0.0 | - | 27 \| 23.8 \| 0.0 |
| 100 | 28 \| 78.9 \| 0.0 | 260 \| 0.4 \| 0.0 | - | 28 \| 79.3 \| 0.0 |
| 200 | 27 \| 68.6 \| 0.0 | 5500* \| 2.8 \| 0.0 | 55 \| 1.3 \| 0.0 | 250 \| 72.7 \| 0.0 |
