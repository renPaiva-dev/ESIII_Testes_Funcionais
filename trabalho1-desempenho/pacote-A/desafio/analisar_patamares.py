"""Resume um <prefixo>_stats_history.csv do Locust por patamar de alunos e por endpoint.

Responde "qual endpoint piora primeiro e a partir de quantos alunos".
Requer que o teste tenha rodado com --csv-full-history (o rodar.sh já faz isso).

Uso:
    python analisar_patamares.py ../../resultados/pacote-A-desafio/estresse_r1_stats_history.csv

Para cada patamar (número de alunos simultâneos), mostra a mediana do p95 "corrente"
(janela móvel do Locust) e a vazão média. Os primeiros 5 s de cada patamar são
descartados, para não misturar a transição entre um patamar e outro.
"""
import csv
import os
import statistics
import sys
from collections import defaultdict

DESCARTE_S = 5
METAS_MS = {"Aggregated": 800, "GET /api/matriculas/[id]/comprovante": 1500}


def numero(texto):
    try:
        return float(texto)
    except (TypeError, ValueError):
        return None


def main(caminho):
    linhas = list(csv.DictReader(open(caminho, encoding="utf-8")))
    inicio_patamar = {}
    for ln in linhas:  # primeiro instante em que cada contagem de alunos aparece
        u = int(ln["User Count"])
        inicio_patamar.setdefault(u, int(ln["Timestamp"]))

    p95 = defaultdict(list)
    rps = defaultdict(list)
    falhas = defaultdict(list)
    for ln in linhas:
        u = int(ln["User Count"])
        if u == 0 or int(ln["Timestamp"]) - inicio_patamar[u] < DESCARTE_S:
            continue
        chave = (u, ln["Name"])
        if (v := numero(ln["95%"])) is not None and v > 0:
            p95[chave].append(v)
        if (v := numero(ln["Requests/s"])) is not None:
            rps[chave].append(v)
        if (v := numero(ln["Failures/s"])) is not None:
            falhas[chave].append(v)

    nomes = sorted({n for _, n in p95}, key=lambda n: (n == "Aggregated", n))
    patamares = sorted({u for u, _ in p95})
    print(f"Arquivo: {os.path.basename(caminho)}")
    print("p95 em ms (mediana da janela no patamar) | req/s | falhas/s   (* = acima da meta)\n")
    cab = "| Alunos | " + " | ".join(nomes) + " |"
    print(cab)
    print("|" + "---|" * (len(nomes) + 1))
    for u in patamares:
        celulas = []
        for n in nomes:
            vals = p95.get((u, n))
            if not vals:
                celulas.append("-")
                continue
            med = statistics.median(vals)
            meta = METAS_MS.get(n)
            marca = "*" if meta and med > meta else ""
            r = statistics.mean(rps[(u, n)]) if rps.get((u, n)) else 0
            f = statistics.mean(falhas[(u, n)]) if falhas.get((u, n)) else 0
            celulas.append(f"{med:.0f}{marca} \\| {r:.1f} \\| {f:.1f}")
        print(f"| {u} | " + " | ".join(celulas) + " |")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
