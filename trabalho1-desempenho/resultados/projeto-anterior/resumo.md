# Estoque Fácil – resultados por execução

p95 **exato da execução inteira** por operação (inclui a rampa), em ms. Metas: busca ≤ 300, consulta produto ≤ 300, consulta histórico ≤ 300, movimentação ≤ 500, relatório ≤ 2000, login ≤ 1000, erros técnicos ≤ 1%.

| Fase | Rep. | req/s | erros | busca | consulta produto | consulta histórico | movimentação | relatório | login | Decisão |
|---|---|---|---|---|---|---|---|---|---|---|
| verificacao1 | r1 | 0.6 | 0.00% | 10 | - | - | 19 | - | 92 | atende |
| verificacao1 | r2 | 0.9 | 0.00% | 9 | 7 | 7 | 4 | - | 80 | atende |
| verificacao1 | r3 | 0.8 | 0.00% | 9 | 8 | 4 | 23 | - | 82 | atende |
| referencia5 | r1 | 2.7 | 0.00% | 11 | 9 | 9 | 25 | 12 | 86 | atende |
| referencia5 | r2 | 2.7 | 0.00% | 9 | 8 | 6 | 25 | 16 | 99 | atende |
| referencia5 | r3 | 2.6 | 0.00% | 9 | 8 | 7 | 24 | 9 | 86 | atende |
| carga20 | r1 | 10.8 | 0.00% | 11 | 10 | 10 | 21 | 13 | 120 | atende |
| carga20 | r2 | 10.9 | 0.00% | 9 | 8 | 6 | 24 | 10 | 91 | atende |
| carga20 | r3 | 10.8 | 0.00% | 10 | 8 | 6 | 23 | 10 | 140 | atende |
| estresse200 | r1 | 107.4 | 0.00% | 16 | 15 | 14 | 22 | 51 | 280 | atende |
| estresse200 | r2 | 107.9 | 0.00% | 16 | 13 | 11 | 42 | 37 | 210 | atende |
| estresse200 | r3 | 108.8 | 0.00% | 14 | 13 | 10 | 42 | 29 | 210 | atende |
| estresse400 | r1 | 215.8 | 0.00% | 23 | 20 | 19 | 76 | 49 | 460 | atende |
| estresse400 | r2 | 216.1 | 0.00% | 35 | 28 | 28 | 53 | 53 | 370 | atende |
| estresse400 | r3 | 216.5 | 0.00% | 16 | 13 | 14 | 24 | 40 | 350 | atende |
| estresse800 | r1 | 422.6 | 0.00% | 110 | 130 | 72 | 540* | 63 | 590 | nao atende |
| estresse800 | r2 | 413.5 | 0.00% | 200 | 130 | 56 | 1200* | 150 | 1900* | nao atende |
| estresse800 | r3 | 424.5 | 0.00% | 100 | 100 | 86 | 420 | 96 | 640 | atende |
| estresse1200 | r1 | 610.2 | 0.00% | 210 | 250 | 150 | 930* | 190 | 1700* | nao atende |
| estresse1200 | r2 | 586.6 | 0.00% | 280 | 270 | 170 | 2500* | 200 | 1600* | nao atende (proteção) |
| estresse1200 | r3 | 593.1 | 0.00% | 280 | 250 | 170 | 1800* | 220 | 1900* | nao atende |
| recuperacao20 | r1 | 10.9 | 0.00% | 10 | 8 | 5 | 48 | 23 | 90 | atende |
| recuperacao20 | r2 | 10.6 | 0.00% | 9 | 8 | 6 | 23 | 20 | 94 | atende |
| recuperacao20 | r3 | 10.9 | 0.00% | 10 | 8 | 8 | 23 | 25 | 100 | atende |
| continuo1200para20 | r1 | 129.3 | 0.01% | 1500* | 1500* | 580* | 2200* | 1400 | 3100* | - (proteção) |
| continuo1200para20 | r2 | 325.4 | 0.00% | 220 | 200 | 150 | 1600* | 200 | 2200* | - |
| continuo1200para20 | r3 | 133.2 | 0.01% | 1300* | 1200* | 320* | 2300* | 1300 | 1900* | - (proteção) |

`*` = acima da meta da operação.

## Patamar (depois da rampa): p95 da janela de 10 s, mediana / pior janela, em ms

Mostra o regime estável e as rajadas lentas; não decide a fase.

| Fase | Rep. | req/s | busca | movimentação | relatório |
|---|---|---|---|---|---|
| referencia5 | r1 | 2.7 | 11 / 23 | 21 / 42 | 9 / 12 |
| referencia5 | r2 | 2.6 | 10 / 16 | 23 / 100 | 9 / 16 |
| referencia5 | r3 | 2.5 | 9 / 22 | 23 / 38 | 9 / 9 |
| carga20 | r1 | 11.2 | 11 / 28 | 21 / 28 | 11 / 13 |
| carga20 | r2 | 11.3 | 9 / 11 | 23 / 25 | 9 / 11 |
| carga20 | r3 | 11.1 | 9 / 11 | 23 / 28 | 9 / 11 |
| estresse200 | r1 | 110.5 | 14 / 17 | 18 / 22 | 19 / 30 |
| estresse200 | r2 | 109.4 | 13 / 26 | 19 / 69 | 18 / 28 |
| estresse200 | r3 | 110.6 | 11 / 23 | 19 / 82 | 13 / 29 |
| estresse400 | r1 | 222.8 | 12 / 25 | 18 / 240 | 18 / 65 |
| estresse400 | r2 | 223.1 | 24 / 34 | 32 / 54 | 36 / 51 |
| estresse400 | r3 | 223.0 | 12 / 14 | 16 / 18 | 16 / 18 |
| estresse800 | r1 | 440.8 | 22 / 34 | 44 / 2900* | 33 / 44 |
| estresse800 | r2 | 429.5 | 21 / 480* | 46 / 3200* | 33 / 310 |
| estresse800 | r3 | 440.8 | 38 / 85 | 72 / 1000* | 74 / 110 |
| estresse1200 | r1 | 646.8 | 37 / 1300* | 240 / 3300* | 56 / 1200 |
| estresse1200 | r2 | 633.1 | 42 / 1200* | 250 / 7300* | 60 / 1500 |
| estresse1200 | r3 | 640.6 | 110 / 2200* | 1050 / 3500* | 150 / 2100* |
| recuperacao20 | r1 | 11.1 | 10 / 13 | 24 / 91 | 22 / 23 |
| recuperacao20 | r2 | 10.8 | 9 / 10 | 23 / 48 | 18 / 21 |
| recuperacao20 | r3 | 11.2 | 9 / 10 | 22 / 89 | 21 / 29 |

## Primeiro patamar que viola as metas

- referencia5: r1 atende, r2 atende, r3 atende
- carga20: r1 atende, r2 atende, r3 atende
- estresse200: r1 atende, r2 atende, r3 atende
- estresse400: r1 atende, r2 atende, r3 atende
- estresse800: r1 nao atende, r2 nao atende, r3 atende
- estresse1200: r1 nao atende, r2 nao atende, r3 nao atende

**Resultado:** primeiro patamar que viola as metas (maioria das repetições): **estresse800**.

## Recuperação (voltar às metas com 20 usuários)

- recuperacao20 r1: metas atendidas 3 s depois do início da execução (banco mantido do estresse)
- recuperacao20 r2: metas atendidas 4 s depois do início da execução (banco mantido do estresse)
- recuperacao20 r3: metas atendidas 3 s depois do início da execução (banco mantido do estresse)
- continuo1200para20 r1: metas atendidas 4 s depois do início da redução para 20 usuários (t=23 s)
- continuo1200para20 r2: metas atendidas 0 s depois do início da redução para 20 usuários (t=92 s)
- continuo1200para20 r3: metas atendidas 4 s depois do início da redução para 20 usuários (t=24 s)

_Registro gravado em ../../resultados/projeto-anterior/registro_resultados.csv_
