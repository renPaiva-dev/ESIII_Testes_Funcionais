"""Analisa as execuções do Desafio B e gera o resumo e o registro de resultados.

Uso:
    python analisar_fases.py ../../resultados/pacote-B-desafio

Para cada execução <fase>_r<N> lê:
  - <prefixo>_stats.csv          agregado da execução inteira (inclui a rampa)
  - <prefixo>_stats_history.csv  linha do tempo: mede o PATAMAR, depois da rampa
  - <prefixo>_protecao.txt       existe se a proteção interrompeu a execução

Patamar (o que decide "atende / não atende"):
  - requisições, req/s e % de falhas: diferença dos contadores acumulados entre o instante
    em que todos os usuários estão ativos e o fim (valores exatos);
  - p95: o Locust só registra o p95 de uma janela móvel de 10 s. Usamos a mediana e o
    máximo dessa janela, descartando os 10 s iniciais do patamar (janela ainda com rampa).
Decisão: atende se falhas do patamar <= 1% e mediana do p95 <= 500 ms.

Recuperação: primeiro instante a partir do qual TODAS as janelas seguintes atendem
(p95 <= 500 ms e falhas <= 1%). A janela de 10 s faz a medida ser conservadora.

Também grava registro_resultados.csv no formato de 04_Modelos/Modelo_Registro_Resultados_Desempenho.csv.
"""
import csv
import re
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

META_P95_MS = 500
META_FALHAS = 0.01
META_RECUPERACAO_S = 30
JANELA_S = 10

FASES = {  # nome: (usuários, ritmo -r, duração em s, tipo)
    "verificacao1": (1, 1, 15, "verificacao"),
    "referencia5": (5, 1, 90, "referencia"),
    "carga20": (20, 2, 90, "carga"),
    "estresse50": (50, 5, 90, "estresse"),
    "estresse100": (100, 10, 90, "estresse"),
    "recuperacao20": (20, 2, 90, "recuperacao"),
    "continuo100para20": (100, 10, 180, "estresse+recuperacao"),
}
ORDEM_LIMITE = ["referencia5", "carga20", "estresse50", "estresse100"]


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def ler_csv(caminho):
    with open(caminho, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def linhas_agregadas(historico):
    return [ln for ln in historico if ln["Name"] == "Aggregated"]


def janela_ok(ln):
    rps, fps, p95 = num(ln["Requests/s"]), num(ln["Failures/s"]), num(ln["95%"])
    if not rps or p95 is None:
        return None                    # janela sem dados
    return p95 <= META_P95_MS and (fps or 0) / rps <= META_FALHAS


def tempo_ate_atender(linhas, t0):
    """Segundos desde t0 até a primeira janela a partir da qual todas atendem."""
    candidatas = [ln for ln in linhas if int(ln["Timestamp"]) >= t0 and janela_ok(ln) is not None]
    for i, ln in enumerate(candidatas):
        if all(janela_ok(x) for x in candidatas[i:]):
            return int(ln["Timestamp"]) - t0
    return None


def analisar_execucao(prefixo, nome):
    usuarios, ritmo, duracao, tipo = FASES[nome]
    agregado = next(ln for ln in ler_csv(f"{prefixo}_stats.csv") if ln["Name"] == "Aggregated")
    por_endpoint = {ln["Name"]: ln for ln in ler_csv(f"{prefixo}_stats.csv") if ln["Name"] != "Aggregated"}
    linhas = linhas_agregadas(ler_csv(f"{prefixo}_stats_history.csv"))
    protecao = Path(f"{prefixo}_protecao.txt")
    r = {
        "nome": nome, "tipo": tipo, "usuarios": usuarios, "ritmo": ritmo, "duracao": duracao,
        "requisicoes": int(agregado["Request Count"]),
        "p50": num(agregado["50%"]), "p95": num(agregado["95%"]),
        "req_s": num(agregado["Requests/s"]),
        "falhas_pct": 100 * int(agregado["Failure Count"]) / max(1, int(agregado["Request Count"])),
        "protecao": protecao.read_text(encoding="utf-8").strip() if protecao.exists() else "",
        "endpoints": {n: (int(e["Request Count"]), num(e["95%"]), int(e["Failure Count"]))
                      for n, e in por_endpoint.items()},
        "inicio": int(linhas[0]["Timestamp"]) if linhas else 0,
    }

    # Patamar: a partir do primeiro instante com todos os usuários ativos
    no_alvo = [ln for ln in linhas if int(ln["User Count"]) == usuarios]
    if no_alvo and nome != "continuo100para20":
        a, b = no_alvo[0], no_alvo[-1]
        dt = max(1, int(b["Timestamp"]) - int(a["Timestamp"]))
        req = int(b["Total Request Count"]) - int(a["Total Request Count"])
        fal = int(b["Total Failure Count"]) - int(a["Total Failure Count"])
        jan = [num(ln["95%"]) for ln in no_alvo
               if int(ln["Timestamp"]) >= int(a["Timestamp"]) + JANELA_S and num(ln["95%"])]
        r.update(pat_s=dt, pat_req=req, pat_req_s=req / dt, pat_falhas_pct=100 * fal / max(1, req),
                 pat_p95_med=statistics.median(jan) if jan else None, pat_p95_max=max(jan) if jan else None)
    if nome == "recuperacao20":
        r["recuperou_em"] = tempo_ate_atender(linhas, r["inicio"])
    if nome == "continuo100para20":
        queda = next((int(ln["Timestamp"]) for ln in linhas
                      if int(ln["User Count"]) <= 20 and any(int(x["User Count"]) > 20 for x in linhas
                                                             if int(x["Timestamp"]) < int(ln["Timestamp"]))), None)
        r["queda_em"] = queda - r["inicio"] if queda else None
        r["recuperou_em"] = tempo_ate_atender(linhas, queda) if queda else None
    return r


def decidir(r):
    if r["protecao"]:
        return "nao atende", f"interrompido pela proteção ({r['protecao']})"
    if r.get("pat_p95_med") is None:
        return "inconclusivo", "patamar sem dados suficientes"
    ok_p95 = r["pat_p95_med"] <= META_P95_MS
    ok_fal = r["pat_falhas_pct"] <= 100 * META_FALHAS
    just = f"patamar: p95 {r['pat_p95_med']:.0f} ms, falhas {r['pat_falhas_pct']:.2f}%"
    return ("atende" if ok_p95 and ok_fal else "nao atende"), just


def fmt(v, casas=0):
    return "-" if v is None else f"{v:.{casas}f}"


def main(pasta):
    pasta = Path(pasta)
    execucoes = defaultdict(dict)   # nome -> {rep: resultado}
    for stats in sorted(pasta.glob("*_r*_stats.csv")):
        m = re.fullmatch(r"(.+)_r(\d+)_stats\.csv", stats.name)
        if m and m.group(1) in FASES:
            execucoes[m.group(1)][int(m.group(2))] = analisar_execucao(str(stats)[:-len("_stats.csv")], m.group(1))

    print("# Desafio B – resultados por execução\n")
    print("| Fase | Rep. | Agregado: req · p50 · p95 · req/s · falhas | Patamar: req/s · falhas · p95 (mediana / máx. da janela) | Decisão |")
    print("|---|---|---|---|---|")
    registro = []
    for nome in FASES:
        for rep, r in sorted(execucoes.get(nome, {}).items()):
            decisao, just = decidir(r) if r["tipo"] not in ("estresse+recuperacao",) else ("-", "")
            r["decisao"] = decisao
            pat = (f"{fmt(r.get('pat_req_s'), 1)} · {fmt(r.get('pat_falhas_pct'), 2)}% · "
                   f"{fmt(r.get('pat_p95_med'))} / {fmt(r.get('pat_p95_max'))} ms")
            print(f"| {nome} | r{rep} | {r['requisicoes']} · {fmt(r['p50'])} · {fmt(r['p95'])} ms · "
                  f"{fmt(r['req_s'], 1)} · {r['falhas_pct']:.2f}% | {pat} | {decisao}"
                  f"{' (proteção)' if r['protecao'] else ''} |")
            data = datetime.fromtimestamp(r["inicio"]).strftime("%Y-%m-%d") if r["inicio"] else ""
            registro.append(["Desafio B - minicursos", f"r{rep}", data, f"{r['tipo']} ({nome})", r["usuarios"],
                             r["ritmo"], r["duracao"], r["requisicoes"], fmt(r["p50"]), fmt(r["p95"]),
                             fmt(r["req_s"], 1), f"{r['falhas_pct']:.2f}", decisao, just])

    # Mistura 70/30 (soma das execuções de carga20)
    tot = defaultdict(int)
    for r in execucoes.get("carga20", {}).values():
        for n, (qtd, _, _) in r["endpoints"].items():
            tot[n] += qtd
    if tot:
        soma = sum(tot.values())
        print("\n**Mistura medida na carga de 20 usuários (todas as repetições):** " +
              ", ".join(f"{n} {100 * q / soma:.1f}%" for n, q in sorted(tot.items())))

    print("\n## Primeiro patamar que viola a meta\n")
    for nome in ORDEM_LIMITE:
        reps = execucoes.get(nome, {})
        decisoes = [r["decisao"] for _, r in sorted(reps.items())]
        print(f"- {nome}: {', '.join(decisoes) if decisoes else 'sem execuções'}")
    primeiro = next((n for n in ORDEM_LIMITE
                     if sum(r["decisao"] == "nao atende" for r in execucoes.get(n, {}).values())
                     > len(execucoes.get(n, {})) / 2), None)
    print(f"\n**Resultado:** " + (f"o primeiro patamar que viola a meta (na maioria das repetições) é **{primeiro}**."
                                 if primeiro else "a meta não foi violada até 100 usuários."))

    print("\n## Recuperação (meta: voltar a p95 <= 500 ms e falhas <= 1% em até 30 s, com 20 usuários)\n")
    for nome in ("recuperacao20", "continuo100para20"):
        for rep, r in sorted(execucoes.get(nome, {}).items()):
            t = r.get("recuperou_em")
            onde = "desde o início da execução" if nome == "recuperacao20" else \
                f"desde a queda para 20 usuários (queda em t={fmt(r.get('queda_em'))} s)"
            veredito = "não recuperou" if t is None else \
                ("dentro da meta" if t <= META_RECUPERACAO_S else "fora da meta")
            print(f"- {nome} r{rep}: atendeu às metas após {fmt(t)} s {onde} → {veredito}")

    with open(pasta / "registro_resultados.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cenario", "execucao", "data", "tipo_teste", "usuarios", "ritmo_r", "duracao_s",
                    "requisicoes", "p50_ms", "p95_ms", "req_s", "falhas_pct", "decisao", "justificativa"])
        w.writerows(registro)
    print(f"\n_Registro gravado em {pasta / 'registro_resultados.csv'}_")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
