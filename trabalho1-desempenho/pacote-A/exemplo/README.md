# Exemplo resolvido A – Semana do Cliente (Trabalho 1)

Nossa execução do exemplo resolvido do pacote A. O teste é a lanchonete Sabor Express numa promoção, com 50 clientes simultâneos.

- `locustfile.py` é a solução do professor, **sem alterações**. É uma cópia de `02_Pacote_A_SaborExpress_Matricula/trabalho1-desempenho/solucao-professor/python/` do kit.
- As evidências (CSV e HTML) estão em [`../../resultados/pacote-A-exemplo/`](../../resultados/pacote-A-exemplo/).

## Como rodamos

```sh
# terminal 1: sistema A (kit do professor)
cd <kit>/02_Pacote_A_SaborExpress_Matricula/app
python app.py

# terminal 2: venv com locust ativo, nesta pasta
curl -X POST http://127.0.0.1:5000/api/admin/reset
TIPO_TESTE=carga    python -m locust -f locustfile.py --host http://127.0.0.1:5000 --headless --csv carga    --html carga.html
curl -X POST http://127.0.0.1:5000/api/admin/reset
TIPO_TESTE=estresse python -m locust -f locustfile.py --host http://127.0.0.1:5000 --headless --csv estresse --html estresse.html
```

Use `127.0.0.1`, e não `localhost`. Na primeira tentativa usamos `localhost`, e no Linux cada requisição ganhou cerca de 2 s, porque o sistema tenta IPv6 primeiro. Essa execução inválida foi guardada em `resultados/pacote-A-exemplo/invalido-localhost-ipv6/` como evidência e descartada.

## O que o script testa

| Item | Como está no script |
|---|---|
| Perfis | `ClienteApp` (peso 9, 90%): cardápio, fazer pedido e acompanhar pedido, com pesos 5/2/2. `Gerente` (peso 1, 10%): relatório de vendas |
| Think time | Cliente: 1 a 3 s. Gerente: 2 a 5 s |
| Tipos de teste | `LoadTestShape` lê `TIPO_TESTE`: carga (50 usuários por 2 min), estresse (+25 a cada 30 s até 250), pico (10 → 150 → 10) e resistência (40 por 15 min) |
| SLA | Geral: p95 ≤ 500 ms e erros ≤ 1%. Relatório de vendas: p95 ≤ 2000 ms. Conferido no evento `quitting`; se reprovar, o Locust sai com código 1 (útil em integração contínua) |

## Resultados: nossa execução e a referência do professor

p95 em ms. A referência vem de `resultados-exemplo/` do kit.

| Teste | Endpoint | Nossa execução | Referência | SLA |
|---|---|---|---|---|
| Carga (50) | Agregado | 69 ms · 23 req/s · 0% | 70 ms · 23 req/s · 0% | atende |
| | Relatório de vendas | 220 ms | 190 ms | atende |
| Estresse (até 250) | Agregado | **39 ms** · 63 req/s · 0% | 36 ms · 63 req/s · 0% | atende no agregado |
| | Relatório de vendas | **13.000 ms** (máximo 17 s) | 13.000 ms | **não atende** (meta 2 s) |
| | Cardápio / pedido | 20 / 42 ms | 16 / 36 ms | atende |

Nossa execução reproduziu a referência: os mesmos números de requisições, vazão e p95, com diferença de poucos milissegundos.

## O que aprendemos

1. **O agregado esconde o gargalo.** No estresse, o p95 geral foi de 39 ms, mas o **relatório de vendas** chegou a 13 s. O cardápio, rápido, domina o volume de requisições e puxa o agregado para baixo. Por isso, nos nossos testes, a meta é conferida **por endpoint**.
2. **O gargalo é o relatório de vendas.** Ele piora com o número de usuários, enquanto o cardápio e o pedido continuam estáveis.
3. Um script só pode rodar vários tipos de teste com `LoadTestShape` e uma variável de ambiente. Usamos esse padrão no Desafio A.
4. **O exemplo verifica pouco o conteúdo:** o cardápio confere só o status. Nos desafios, verificamos o conteúdo de todas as respostas, como o guia exige.
5. Um erro de ambiente (`localhost` → IPv6) pode parecer um problema de desempenho.
