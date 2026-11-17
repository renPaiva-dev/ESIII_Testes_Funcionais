"""Compara as repetições (r1, r2, r3...) do Desafio A e grava comparacao.md.

Uso:
    python comparar_repeticoes.py ../../resultados/pacote-A-desafio

Lê, para cada <tipo>_r<N>:
  - <prefixo>_stats.csv   p95 geral, p95 por endpoint, requisições e falhas
  - <prefixo>_regras.csv  SLA, regras de negócio (409/422) e integridade das vagas
"""
import csv
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

TIPOS = ["carga", "pico", "estresse"]
OFERTA = "GET /api/disciplinas"
MATRICULA = "POST /api/matriculas"
COMPROVANTE = "GET /api/matriculas/[id]/comprovante"


def ler(caminho):
    with open(caminho, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def analisar(prefixo):
    stats = {ln["Name"]: ln for ln in ler(f"{prefixo}_stats.csv")}
    agg = stats["Aggregated"]
    r = {
        "requisicoes": int(agg["Request Count"]),
        "falhas_pct": 100 * int(agg["Failure Count"]) / max(1, int(agg["Request Count"])),
        "p95_geral": num(agg["95%"]),
        "req_s": num(agg["Requests/s"]),
    }
    for nome, chave in ((OFERTA, "p95_oferta"), (MATRICULA, "p95_matricula"), (COMPROVANTE, "p95_comprovante")):
        r[chave] = num(stats[nome]["95%"]) if nome in stats else None
    regras = Path(f"{prefixo}_regras.csv")
    r["sla"], r["negocio"], r["integridade_ok"], r["efetivadas"] = {}, {}, True, None
    if regras.exists():
        for ln in ler(regras):
            if ln["categoria"] == "sla":
                r["sla"][ln["item"]] = ln["atendido"] == "sim"
            elif ln["categoria"] == "regra_negocio":
                r["negocio"][ln["item"]] = int(ln["valor"])
            elif ln["categoria"] == "matriculas":
                r["efetivadas"] = int(ln["valor"])
            elif ln["categoria"] in ("vagas", "integridade") and ln["atendido"] == "nao":
                r["integridade_ok"] = False
    r["sla_ok"] = bool(r["sla"]) and all(r["sla"].values())
    return r


def fmt(v, sufixo="", casas=0):
    return "-" if v is None else f"{v:.{casas}f}{sufixo}"


def serie(execs, chave, sufixo="", casas=0):
    return " / ".join(fmt(execs[rep][chave], sufixo, casas) for rep in sorted(execs))


def main(pasta):
    pasta = Path(pasta)
    dados = defaultdict(dict)
    for stats in pasta.glob("*_r*_stats.csv"):
        m = re.fullmatch(r"(\w+?)_r(\d+)_stats\.csv", stats.name)
        if m and m.group(1) in TIPOS:
            dados[m.group(1)][int(m.group(2))] = analisar(str(stats)[:-len("_stats.csv")])

    saida = ["# Desafio A – comparação das repetições\n"]
    saida.append("Valores na ordem r1 / r2 / r3. Metas: p95 geral ≤ 800 ms, p95 comprovante ≤ 1500 ms, "
                 "erros técnicos < 1%, vagas nunca negativas.\n")
    saida.append("| Teste | p95 geral | p95 comprovante | p95 oferta | p95 matrícula | Erros técnicos | "
                 "Matrículas 201 | Integridade | SLA |")
    saida.append("|---|---|---|---|---|---|---|---|---|")
    for tipo in TIPOS:
        execs = dados.get(tipo)
        if not execs:
            continue
        integ = "OK" if all(e["integridade_ok"] for e in execs.values()) else "PROBLEMA"
        slas = " / ".join("atendido" if execs[r]["sla_ok"] else "não atendido" for r in sorted(execs))
        saida.append(f"| {tipo} | {serie(execs, 'p95_geral', ' ms')} | {serie(execs, 'p95_comprovante', ' ms')} | "
                     f"{serie(execs, 'p95_oferta', ' ms')} | {serie(execs, 'p95_matricula', ' ms')} | "
                     f"{serie(execs, 'falhas_pct', '%', 2)} | {serie(execs, 'efetivadas')} | {integ} | {slas} |")

    saida.append("\n## Variação entre repetições (p95 do comprovante)\n")
    for tipo in TIPOS:
        execs = dados.get(tipo)
        if not execs:
            continue
        vals = [e["p95_comprovante"] for e in execs.values() if e["p95_comprovante"] is not None]
        if len(vals) >= 2:
            media = statistics.mean(vals)
            saida.append(f"- {tipo}: mínimo {min(vals):.0f} ms, máximo {max(vals):.0f} ms, média {media:.0f} ms, "
                         f"desvio padrão {statistics.stdev(vals):.0f} ms "
                         f"({100 * statistics.stdev(vals) / media:.0f}% da média); "
                         f"{sum(v > 1500 for v in vals)} de {len(vals)} acima da meta de 1500 ms")

    saida.append("\n## Regras de negócio por repetição (não contam como erro)\n")
    for tipo in TIPOS:
        for rep, e in sorted(dados.get(tipo, {}).items()):
            itens = ", ".join(f"{k}: {v}" for k, v in sorted(e["negocio"].items())) or "nenhuma"
            saida.append(f"- {tipo} r{rep}: {itens}")

    texto = "\n".join(saida) + "\n"
    (pasta / "comparacao.md").write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
