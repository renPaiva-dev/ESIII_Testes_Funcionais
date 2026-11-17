"""Analisa as execuções de desempenho do Estoque Fácil e gera resumo e registro.

Uso:
    python analisar_fases.py ../../resultados/projeto-anterior

Para cada execução <fase>_r<N>:
  - agregado da execução inteira (inclui a rampa): <prefixo>_stats.csv
  - patamar (depois da rampa): <prefixo>_stats_history.csv
      * requisições, req/s e % de erros técnicos: diferença dos contadores acumulados (exatos)
      * p95 de cada operação: mediana do p95 da janela móvel de 10 s, descartando os
        10 s iniciais do patamar (aproximação: o Locust não guarda as amostras)
  - metas por operação e integridade dos saldos: <prefixo>_metas.csv
  - proteção acionada: <prefixo>_protecao.txt
Decisão da fase: atende se, na EXECUÇÃO INTEIRA (p95 exato do stats.csv, inclui a chegada
dos usuários), toda operação ficou dentro da sua meta de p95, erros técnicos <= 1%, a
integridade dos saldos foi mantida e a proteção não disparou. O patamar (mediana e pior
janela) é mostrado à parte: a mediana sozinha escondia as rajadas lentas.

Recuperação: primeiro instante a partir do qual TODAS as janelas seguintes atendem
(p95 de cada operação dentro da meta e erros <= 1%).
"""
import csv
import re
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

METAS_MS = {
    "GET /api/produtos?q=": ("busca", 300),
    "GET /api/produtos/[id]": ("consulta produto", 300),
    "GET /api/produtos/[id]/movimentacoes": ("consulta histórico", 300),
    "POST /api/produtos/[id]/movimentacoes": ("movimentação", 500),
    "GET /api/relatorio": ("relatório", 2000),
    "POST /login": ("login", 1000),
}
META_ERROS = 0.01
JANELA_S = 10
FASES = {  # nome: (usuários, ritmo, duração s, tipo)
    "verificacao1": (1, 1, 15, "verificacao"),
    "referencia5": (5, 1, 90, "referencia"),
    "carga20": (20, 2, 90, "carga"),
    "estresse200": (200, 20, 90, "estresse"),
    "estresse400": (400, 40, 90, "estresse"),
    "estresse800": (800, 80, 90, "estresse"),
    "estresse1200": (1200, 100, 90, "estresse"),
    "recuperacao20": (20, 2, 90, "recuperacao"),
    "continuo1200para20": (1200, 100, 180, "estresse+recuperacao"),
}
ORDEM_LIMITE = ["referencia5", "carga20", "estresse200", "estresse400", "estresse800", "estresse1200"]
CURTO = {n: c for n, (c, _) in METAS_MS.items()}


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def ler(caminho):
    with open(caminho, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def janelas_por_instante(historico):
    """{timestamp: {nome: linha}} com as linhas do histórico completo."""
    por_t = defaultdict(dict)
    for ln in historico:
        por_t[int(ln["Timestamp"])][ln["Name"]] = ln
    return dict(sorted(por_t.items()))


def instante_ok(linhas):
    agg = linhas.get("Aggregated")
    if not agg or not num(agg["Requests/s"]):
        return None
    if (num(agg["Failures/s"]) or 0) / num(agg["Requests/s"]) > META_ERROS:
        return False
    for nome, (_, meta) in METAS_MS.items():
        ln = linhas.get(nome)
        if ln and num(ln["Requests/s"]) and (num(ln["95%"]) or 0) > meta:
            return False
    return True


def tempo_ate_atender(por_t, t0):
    instantes = [(t, instante_ok(l)) for t, l in por_t.items() if t >= t0]
    instantes = [(t, ok) for t, ok in instantes if ok is not None]
    for i, (t, _) in enumerate(instantes):
        if all(ok for _, ok in instantes[i:]):
            return t - t0
    return None


def analisar(prefixo, nome):
    usuarios = FASES[nome][0]
    stats = {ln["Name"]: ln for ln in ler(f"{prefixo}_stats.csv")}
    historico = ler(f"{prefixo}_stats_history.csv")
    por_t = janelas_por_instante(historico)
    agg_hist = [ln for ln in historico if ln["Name"] == "Aggregated"]
    protecao = Path(f"{prefixo}_protecao.txt")
    metas_csv = Path(f"{prefixo}_metas.csv")
    integridade_ok = True
    if metas_csv.exists():
        integridade_ok = all(ln["atendido"] == "sim" for ln in ler(metas_csv) if ln["categoria"] == "integridade")
    agg = stats["Aggregated"]
    r = {
        "nome": nome, "usuarios": usuarios, "ritmo": FASES[nome][1], "duracao": FASES[nome][2],
        "tipo": FASES[nome][3], "inicio": int(agg_hist[0]["Timestamp"]) if agg_hist else 0,
        "requisicoes": int(agg["Request Count"]), "p50": num(agg["50%"]), "p95": num(agg["95%"]),
        "req_s": num(agg["Requests/s"]),
        "erros_pct": 100 * int(agg["Failure Count"]) / max(1, int(agg["Request Count"])),
        "p95_op": {n: num(stats[n]["95%"]) for n in METAS_MS if n in stats},
        "protecao": protecao.read_text(encoding="utf-8").strip() if protecao.exists() else "",
        "integridade_ok": integridade_ok,
    }
    no_alvo = [ln for ln in agg_hist if int(ln["User Count"]) == usuarios]
    if no_alvo and not nome.startswith("continuo"):
        a, b = no_alvo[0], no_alvo[-1]
        t_a = int(a["Timestamp"])
        dt = max(1, int(b["Timestamp"]) - t_a)
        req = int(b["Total Request Count"]) - int(a["Total Request Count"])
        err = int(b["Total Failure Count"]) - int(a["Total Failure Count"])
        r.update(pat_req_s=req / dt, pat_erros_pct=100 * err / max(1, req), pat_p95={}, pat_p95_max={})
        for n in METAS_MS:
            vals = [num(l[n]["95%"]) for t, l in por_t.items()
                    if t >= t_a + JANELA_S and n in l and int(l[n]["User Count"]) == usuarios
                    and num(l[n]["95%"]) and num(l[n]["Requests/s"])]
            if vals:
                r["pat_p95"][n] = statistics.median(vals)
                r["pat_p95_max"][n] = max(vals)
    if nome == "recuperacao20":
        r["recuperou_em"] = tempo_ate_atender(por_t, r["inicio"])
    if nome.startswith("continuo"):
        # A queda começa quando a contagem de usuários passa a DIMINUIR depois de chegar ao
        # máximo (o Locust leva ~12 s para encerrar 1180 usuários a 100/s).
        queda = None
        maximo = max((int(ln["User Count"]) for ln in agg_hist), default=0)
        visto_max = False
        for ln in agg_hist:
            u = int(ln["User Count"])
            visto_max = visto_max or u == maximo
            if visto_max and u < maximo:
                queda = int(ln["Timestamp"])
                break
        r["queda_em"] = queda - r["inicio"] if queda else None
        r["recuperou_em"] = tempo_ate_atender(por_t, queda) if queda else None
    return r


def decidir(r):
    """Decide pelo p95 EXATO da execução inteira (stats.csv), que inclui a chegada dos usuários
    e as rajadas lentas. A mediana das janelas do patamar escondia essas rajadas, por isso
    é mostrada só como apoio à interpretação."""
    if r["protecao"]:
        return "nao atende", f"interrompido pela proteção ({r['protecao']})"
    if not r["p95_op"]:
        return "inconclusivo", "sem dados"
    estouros = [f"{CURTO[n]} {v:.0f} ms > {METAS_MS[n][1]}" for n, v in r["p95_op"].items()
                if v is not None and v > METAS_MS[n][1]]
    if r["erros_pct"] > 100 * META_ERROS:
        estouros.append(f"erros {r['erros_pct']:.2f}%")
    if not r["integridade_ok"]:
        estouros.append("integridade dos saldos")
    if estouros:
        return "nao atende", "; ".join(estouros)
    return "atende", f"todas as operações dentro da meta; erros {r['erros_pct']:.2f}%"


def fmt(v, casas=0):
    return "-" if v is None else f"{v:.{casas}f}"


def main(pasta):
    pasta = Path(pasta)
    execs = defaultdict(dict)
    for st in sorted(pasta.glob("*_r*_stats.csv")):
        m = re.fullmatch(r"(.+)_r(\d+)_stats\.csv", st.name)
        if m and m.group(1) in FASES:
            execs[m.group(1)][int(m.group(2))] = analisar(str(st)[:-len("_stats.csv")], m.group(1))

    ops = list(METAS_MS)
    print("# Estoque Fácil – resultados por execução\n")
    print("p95 **exato da execução inteira** por operação (inclui a rampa), em ms. Metas: "
          + ", ".join(f"{c} ≤ {m}" for c, m in METAS_MS.values()) + ", erros técnicos ≤ 1%.\n")
    print("| Fase | Rep. | req/s | erros | " + " | ".join(CURTO[o] for o in ops) + " | Decisão |")
    print("|---|---|---|---|" + "---|" * len(ops) + "---|")
    registro = []
    for nome in FASES:
        for rep, r in sorted(execs.get(nome, {}).items()):
            if nome.startswith("continuo"):
                r["decisao"], just = "-", "perfil contínuo (ver recuperação)"
            else:
                r["decisao"], just = decidir(r)
            celulas = []
            for o in ops:
                v = r["p95_op"].get(o)
                celulas.append("-" if v is None else f"{v:.0f}{'*' if v > METAS_MS[o][1] else ''}")
            print(f"| {nome} | r{rep} | {fmt(r['req_s'], 1)} | {r['erros_pct']:.2f}% | "
                  + " | ".join(celulas) + f" | {r['decisao']}{' (proteção)' if r['protecao'] else ''} |")
            data = datetime.fromtimestamp(r["inicio"]).strftime("%Y-%m-%d") if r["inicio"] else ""
            registro.append(["Projeto anterior - Estoque Fácil", f"r{rep}", data, f"{r['tipo']} ({nome})",
                             r["usuarios"], r["ritmo"], r["duracao"], r["requisicoes"], fmt(r["p50"]),
                             fmt(r["p95"]), fmt(r["req_s"], 1), f"{r['erros_pct']:.2f}", r["decisao"], just])
    print("\n`*` = acima da meta da operação.\n")

    print("## Patamar (depois da rampa): p95 da janela de 10 s, mediana / pior janela, em ms\n")
    print("Mostra o regime estável e as rajadas lentas; não decide a fase.\n")
    chave = ["GET /api/produtos?q=", "POST /api/produtos/[id]/movimentacoes", "GET /api/relatorio"]
    print("| Fase | Rep. | req/s | " + " | ".join(CURTO[o] for o in chave) + " |")
    print("|---|---|---|" + "---|" * len(chave))
    for nome in FASES:
        if nome.startswith("continuo") or nome == "verificacao1":
            continue
        for rep, r in sorted(execs.get(nome, {}).items()):
            cel = []
            for o in chave:
                med, pior = r.get("pat_p95", {}).get(o), r.get("pat_p95_max", {}).get(o)
                cel.append("-" if med is None else f"{med:.0f} / {pior:.0f}{'*' if pior > METAS_MS[o][1] else ''}")
            print(f"| {nome} | r{rep} | {fmt(r.get('pat_req_s'), 1)} | " + " | ".join(cel) + " |")
    print()

    print("## Primeiro patamar que viola as metas\n")
    for nome in ORDEM_LIMITE:
        reps = execs.get(nome, {})
        if reps:
            print(f"- {nome}: " + ", ".join(f"r{k} {r['decisao']}" for k, r in sorted(reps.items())))
    primeiro = next((n for n in ORDEM_LIMITE
                     if sum(r["decisao"] == "nao atende" for r in execs.get(n, {}).values())
                     > len(execs.get(n, {})) / 2), None)
    print("\n**Resultado:** " + (f"primeiro patamar que viola as metas (maioria das repetições): **{primeiro}**."
                                 if primeiro else "as metas não foram violadas nos patamares testados."))

    print("\n## Recuperação (voltar às metas com 20 usuários)\n")
    for nome in ("recuperacao20", "continuo1200para20"):
        for rep, r in sorted(execs.get(nome, {}).items()):
            t = r.get("recuperou_em")
            ref = "do início da execução (banco mantido do estresse)" if nome == "recuperacao20" else \
                f"do início da redução para 20 usuários (t={fmt(r.get('queda_em'))} s)"
            print(f"- {nome} r{rep}: metas atendidas {fmt(t)} s depois {ref}"
                  + ("" if t is not None else " → não recuperou dentro da execução"))

    with open(pasta / "registro_resultados.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cenario", "execucao", "data", "tipo_teste", "usuarios", "ritmo_r", "duracao_s", "requisicoes",
                    "p50_ms", "p95_ms", "req_s", "falhas_pct", "decisao", "justificativa"])
        w.writerows(registro)
    print("\n_Registro gravado em registro_resultados.csv_")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
