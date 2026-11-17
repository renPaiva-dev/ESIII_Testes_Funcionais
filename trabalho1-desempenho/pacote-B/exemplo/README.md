# Exemplo resolvido B – Catálogo da biblioteca (Trabalho 1)

Nossa execução do exemplo resolvido do pacote B: `GET /api/livros?q=software` com 20 leitores simultâneos.

- `locustfile.py` é o exemplo do kit, **sem alterações**. É uma cópia de `03_Pacote_B_Biblioteca_Minicursos/desempenho/`.
- As evidências (CSV e HTML) estão em [`../../resultados/pacote-B-exemplo/`](../../resultados/pacote-B-exemplo/).

## Como rodamos

```sh
# terminal 1: sistema B (kit do professor)
cd <kit>/03_Pacote_B_Biblioteca_Minicursos
python app.py

# terminal 2: venv com locust ativo, nesta pasta
curl -X POST http://127.0.0.1:8000/api/reset
python -m locust -f locustfile.py --host http://127.0.0.1:8000 --headless \
  -u 1 -r 1 -t 15s --stop-timeout 5s --csv verificacao --html verificacao.html
python -m locust -f locustfile.py --host http://127.0.0.1:8000 --headless \
  -u 20 -r 2 -t 90s --stop-timeout 5s --csv carga20_r1 --html carga20_r1.html
```

## O que o script testa

| Item | Como está no script |
|---|---|
| Perfil | `Leitor`, num modelo fechado: cada usuário repete a busca e espera entre uma e outra |
| Think time | `between(0.2, 0.6)` |
| Verificação de conteúdo | `catch_response=True`: exige HTTP 200, `total` ≥ 1 e lista `itens` não vazia. Uma resposta 200 com lista vazia conta como falha |
| Timeout | 5 s; acima disso, conta como falha |

## Resultados

| Execução | Usuários | Requisições | p50 | p95 | req/s | Falhas |
|---|---|---|---|---|---|---|
| `verificacao` | 1 (15 s) | 31 | 33 ms | 36 ms | 2,2 | 0% |
| `carga20_r1` | 20 (90 s) | 3.854 | 33 ms | 38 ms | 43 | 0% |

Com 20 leitores, o catálogo atende com folga uma meta de p95 ≤ 500 ms e falhas ≤ 1%.

## O que aprendemos

1. **Verificar o conteúdo, não só o tempo.** O `catch_response` permite marcar como falha uma resposta rápida, mas errada. No Desafio B, conferimos o conteúdo exato: `total` = 3, os nomes dos cursos e `vagas` = 2.
2. **O servidor limita de propósito a 4 consultas simultâneas** e responde 503 quando lota. Sob estresse, o 503 é evidência do limite, não erro do script. No Desafio B foi exatamente isso que apareceu com 100 usuários.
3. **Guardar a evidência de cada execução** com `--csv` e `--html`, com um nome por repetição (`carga20_r1`, `carga20_r2`…).
