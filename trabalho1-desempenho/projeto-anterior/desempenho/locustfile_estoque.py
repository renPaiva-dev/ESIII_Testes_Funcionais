"""
PROJETO ANTERIOR - Trabalho 1: desempenho do Estoque Fácil (Locust / Python)

Cenário: dia de movimento numa papelaria com cerca de 1.000 itens. Operadores consultam
produtos e registram entradas e saídas no balcão e no depósito, enquanto o gerente
acompanha o relatório do estoque.

Perfis de usuário (modelo fechado):
  Operador (90%)  entra no sistema uma vez (login pela tela) e depois repete:
                    buscar produto        peso 5   GET  /api/produtos?q=...
                    consultar produto     peso 2   GET  /api/produtos/<id> + /movimentacoes
                    registrar movimento   peso 3   POST /api/produtos/<id>/movimentacoes
  Gerente  (10%)  consulta o relatório     GET  /api/relatorio

Metas (justificativa no README):
  p95 busca <= 300 ms · p95 consulta <= 300 ms · p95 movimentação <= 500 ms
  p95 relatório <= 2000 ms · p95 login <= 1000 ms · erros técnicos < 1%
  integridade: saldo nunca negativo e saldo final = inicial + entradas - saídas aceitas

409 (estoque insuficiente) é regra de negócio: conta como sucesso e é contado à parte.
503 ("Banco de dados ocupado"), 5xx, timeout e conteúdo errado são erros técnicos.

Sistema: SEED_PRODUTOS=1000 python app.py --reset   (http://127.0.0.1:5001)
O script zera o sistema no início (POST /api/reset). Para manter o estado: RESET=0.
Proteção: encerra se erros > 20% ou p95 > 2000 ms por 10 s seguidos.
Perfil contínuo opcional: PERFIL=estresse_recuperacao USUARIOS_ESTRESSE=1200
  (estresse por 90 s -> 20 usuários por 90 s, sem reiniciar o Locust nem zerar o banco).
"""
import csv
import os
import random
import time
from collections import Counter

import gevent
import requests
from locust import HttpUser, LoadTestShape, between, events, task
from locust.runners import STATE_CLEANUP, STATE_STOPPED, STATE_STOPPING, WorkerRunner

METAS_MS = {
    "busca": 300,
    "consulta produto": 300,
    "consulta histórico": 300,
    "movimentação": 500,
    "relatório": 2000,
    "login": 1000,
}
META_ERROS = 0.01
NOMES = {  # nome no Locust -> chave da meta
    "GET /api/produtos?q=": "busca",
    "GET /api/produtos/[id]": "consulta produto",
    "GET /api/produtos/[id]/movimentacoes": "consulta histórico",
    "POST /api/produtos/[id]/movimentacoes": "movimentação",
    "GET /api/relatorio": "relatório",
    "POST /login": "login",
}
TERMOS = ["caneta", "caderno", "lápis", "borracha", "resma", "cola", "pasta",
          "genérico 00", "genérico 01", "genérico 05", "GEN-001", "GEN-0050", "CAN", "tesoura"]
SITUACAO = lambda q, m: "sem_estoque" if q == 0 else ("baixo" if q <= m else "normal")  # RN11

PROTECAO_ERROS, PROTECAO_P95_MS, PROTECAO_JANELA_S = 0.20, 2000, 10

# --------------------------------------------------------------------------- estado compartilhado
estado = {"total_produtos": 0, "protecao_em": None}
saldo_inicial = {}            # id -> quantidade no início
movimento_aceito = Counter()  # id -> soma (+entradas, -saídas) dos 201 recebidos
sem_resposta = {}             # id -> [deltas] de movimentações sem resposta (timeout): o servidor
                              # pode ter gravado sem o cliente saber
negocio = Counter()           # respostas de regra de negócio
saldos_negativos = []         # (id, saldo_apos) se algum 201 trouxer saldo < 0


class Operador(HttpUser):
    weight = 9
    wait_time = between(1, 3)    # tempo de olhar a tela, pegar o produto, digitar

    def on_start(self):
        usuario, senha = random.choice([("admin", "admin123"), ("operador", "oper123")])
        with self.client.post("/login", data={"usuario": usuario, "senha": senha}, name="POST /login",
                              allow_redirects=False, catch_response=True, timeout=10) as r:
            if r.status_code != 302 or not r.headers.get("Location", "").endswith("/produtos"):
                r.failure(f"login: HTTP {r.status_code}")

    @task(5)
    def buscar(self):
        termo = random.choice(TERMOS)
        baixo = random.random() < 0.2          # 20% das buscas usam o filtro "só estoque baixo"
        params = {"q": termo, **({"baixo": "1"} if baixo else {})}
        with self.client.get("/api/produtos", params=params, name="GET /api/produtos?q=",
                             catch_response=True, timeout=10) as r:
            if r.status_code != 200:
                r.failure(f"HTTP {r.status_code}")
                return
            try:
                d = r.json()
                itens = d["itens"]
                problema = None
                if len(itens) > 20 or d["pagina"] != 1 or d["total"] < len(itens):
                    problema = "paginação incoerente"
                for p in itens:
                    if termo.casefold() not in (p["nome"] + " " + p["sku"]).casefold():
                        problema = f"item fora da busca: {p['sku']}"
                    elif baixo and p["quantidade"] > p["estoque_minimo"]:
                        problema = f"item fora do filtro de baixa: {p['sku']}"
                    elif p["situacao"] != SITUACAO(p["quantidade"], p["estoque_minimo"]):
                        problema = f"situação errada: {p['sku']}"
                if problema:
                    r.failure(problema)
            except (ValueError, KeyError, TypeError):
                r.failure("Resposta inválida")

    @task(2)
    def consultar_produto(self):
        pid = random.randint(1, estado["total_produtos"] or 10)
        with self.client.get(f"/api/produtos/{pid}", name="GET /api/produtos/[id]",
                             catch_response=True, timeout=10) as r:
            if r.status_code != 200:
                r.failure(f"HTTP {r.status_code}")
                return
            try:
                p = r.json()
                if p["id"] != pid or p["quantidade"] < 0 or \
                        p["situacao"] != SITUACAO(p["quantidade"], p["estoque_minimo"]):
                    r.failure("produto incoerente")
            except (ValueError, KeyError, TypeError):
                r.failure("Resposta inválida")
        with self.client.get(f"/api/produtos/{pid}/movimentacoes", name="GET /api/produtos/[id]/movimentacoes",
                             catch_response=True, timeout=10) as r:
            if r.status_code != 200:
                r.failure(f"HTTP {r.status_code}")
                return
            try:
                hist = r.json()
                ids = [m["id"] for m in hist]
                if len(hist) > 50 or ids != sorted(ids, reverse=True) or any(m["saldo_apos"] < 0 for m in hist):
                    r.failure("histórico incoerente")
            except (ValueError, KeyError, TypeError):
                r.failure("Resposta inválida")

    @task(3)
    def movimentar(self):
        pid = random.randint(1, estado["total_produtos"] or 10)
        tipo = random.choice(["entrada", "saida"])   # metade de cada: o estoque fica estável
        qtd = random.randint(1, 10)
        corpo = {"tipo": tipo, "quantidade": qtd, "observacao": "teste de carga", "usuario": "locust"}
        with self.client.post(f"/api/produtos/{pid}/movimentacoes", json=corpo,
                              name="POST /api/produtos/[id]/movimentacoes", catch_response=True, timeout=10) as r:
            if r.status_code == 201:
                try:
                    m = r.json()
                    if m["produto_id"] != pid or m["tipo"] != tipo or m["quantidade"] != qtd:
                        r.failure("movimentação incoerente")
                        return
                    if m["saldo_apos"] < 0:
                        saldos_negativos.append((pid, m["saldo_apos"]))
                        r.failure("saldo negativo!")
                        return
                    movimento_aceito[pid] += qtd if tipo == "entrada" else -qtd
                except (ValueError, KeyError, TypeError):
                    r.failure("Resposta inválida")
            elif r.status_code == 409:
                r.success()                                        # regra de negócio
                negocio["409 Estoque insuficiente"] += 1
            else:
                if r.status_code == 0:                             # sem resposta (timeout/conexão)
                    sem_resposta.setdefault(pid, []).append(qtd if tipo == "entrada" else -qtd)
                r.failure(f"HTTP {r.status_code}")                 # 503 banco ocupado, 5xx, timeout...


class Gerente(HttpUser):
    weight = 1
    wait_time = between(3, 8)    # o gerente atualiza o relatório de tempos em tempos

    @task
    def relatorio(self):
        with self.client.get("/api/relatorio", name="GET /api/relatorio", catch_response=True, timeout=10) as r:
            if r.status_code != 200:
                r.failure(f"HTTP {r.status_code}")
                return
            try:
                d = r.json()
                if d["total_produtos"] != estado["total_produtos"] or d["total_unidades"] < 0 \
                        or d["valor_total"] < 0 or len(d["mais_saidas"]) > 5:
                    r.failure("relatório incoerente")
            except (ValueError, KeyError, TypeError):
                r.failure("Resposta inválida")


# --------------------------------------------------------------------------- preparação e integridade
def _todos_os_saldos(host):
    saldos, pagina = {}, 1
    while True:
        d = requests.get(f"{host}/api/produtos", params={"pagina": pagina}, timeout=30).json()
        saldos.update({p["id"]: p["quantidade"] for p in d["itens"]})
        if pagina >= d["paginas"]:
            return saldos, d["total"]
        pagina += 1


@events.test_start.add_listener
def preparar(environment, **_):
    for estrutura in (saldo_inicial, movimento_aceito, negocio, sem_resposta):
        estrutura.clear()
    saldos_negativos.clear()
    estado["protecao_em"] = None
    if os.getenv("RESET", "1") == "1":
        requests.post(f"{environment.host}/api/reset", timeout=60).raise_for_status()
    saldos, total = _todos_os_saldos(environment.host)
    saldo_inicial.update(saldos)
    estado["total_produtos"] = total
    if not isinstance(environment.runner, WorkerRunner):
        gevent.spawn(_vigiar, environment)


def _vigiar(environment):
    """Proteção: erros > 20% ou p95 > 2000 ms por 10 s seguidos."""
    runner, inicio, ruins = environment.runner, time.time(), 0
    while runner.state not in (STATE_STOPPING, STATE_STOPPED, STATE_CLEANUP):
        gevent.sleep(1)
        total = runner.stats.total
        rps = total.current_rps
        erros = total.current_fail_per_sec / rps if rps else 0
        p95 = total.get_current_response_time_percentile(0.95) or 0
        ruins = ruins + 1 if (erros > PROTECAO_ERROS or p95 > PROTECAO_P95_MS) else 0
        if ruins >= PROTECAO_JANELA_S and estado["protecao_em"] is None:
            estado["protecao_em"] = time.time() - inicio
            motivo = f"erros {erros:.0%}" if erros > PROTECAO_ERROS else f"p95 {p95} ms"
            msg = f"PROTEÇÃO ACIONADA em {estado['protecao_em']:.0f} s: {motivo} por {PROTECAO_JANELA_S} s seguidos"
            print(f"\n[PROTEÇÃO] {msg}", flush=True)
            prefixo = getattr(environment.parsed_options, "csv_prefix", None)
            if prefixo:
                with open(f"{prefixo}_protecao.txt", "w", encoding="utf-8") as f:
                    f.write(msg + "\n")
            if environment.shape_class is None:
                runner.quit()
                return


@events.quitting.add_listener
def relatorio_final(environment, **_):
    stats = environment.stats
    if stats.total.num_requests == 0:
        return
    finais, _ = _todos_os_saldos(environment.host)
    divergentes, explicadas = [], []
    for pid in saldo_inicial:
        esperado = saldo_inicial[pid] + movimento_aceito[pid]
        if finais.get(pid) == esperado:
            continue
        diferenca = (finais.get(pid) or 0) - esperado
        if _soma_de_subconjunto(sem_resposta.get(pid, []), diferenca):
            # o servidor gravou movimentação(ões) cuja resposta o cliente não recebeu
            explicadas.append((pid, saldo_inicial[pid], movimento_aceito[pid], finais.get(pid), diferenca))
        else:
            divergentes.append((pid, saldo_inicial[pid], movimento_aceito[pid], finais.get(pid)))
    negativos_finais = [pid for pid, q in finais.items() if q < 0]

    linhas = []
    print("\n================ ESTOQUE FÁCIL - projeto anterior ================")
    for nome, chave in NOMES.items():
        e = stats.entries.get((nome, nome.split(" ", 1)[0]))   # chave = (nome, método)
        if e and e.num_requests:
            p95 = e.get_response_time_percentile(0.95)
            ok = p95 <= METAS_MS[chave]
            linhas.append(("sla", f"p95 {chave}", f"{p95:.0f} ms", f"<= {METAS_MS[chave]} ms", ok))
    taxa = stats.total.fail_ratio
    linhas.append(("sla", "erros técnicos", f"{taxa:.2%}", "< 1%", taxa < META_ERROS))
    integro = not divergentes and not negativos_finais and not saldos_negativos
    linhas.append(("integridade", "saldos (inicial + aceitos = final, nunca < 0)",
                   f"{len(divergentes)} divergente(s), {len(negativos_finais) + len(saldos_negativos)} negativo(s)",
                   "0", integro))
    for cat, item, valor, meta, ok in linhas:
        print(f"[{cat.upper()}] {item:48} {valor:>14}  (meta {meta:>10})  {'OK' if ok else 'NÃO ATENDIDO'}")
    print(f"Movimentações aceitas em {len(movimento_aceito)} produtos; regras de negócio: {dict(negocio) or 'nenhuma'}")
    for d in divergentes[:5]:
        print(f"   DIVERGÊNCIA produto {d[0]}: inicial {d[1]} + aceitos {d[2]} != final {d[3]}")
    for d in explicadas:
        print(f"   GRAVADA SEM CONFIRMAÇÃO produto {d[0]}: inicial {d[1]} + aceitos {d[2]} = "
              f"{d[1] + d[2]}, final {d[3]} ({d[4]:+d}): movimentação sem resposta ao cliente foi gravada")
    total_sem_resposta = sum(len(v) for v in sem_resposta.values())
    if total_sem_resposta:
        print(f"Movimentações sem resposta (timeout): {total_sem_resposta}; "
              f"gravadas sem confirmação: {len(explicadas)} produto(s)")
    if estado["protecao_em"] is not None:
        print("[PROTEÇÃO] acionada nesta execução")

    prefixo = getattr(environment.parsed_options, "csv_prefix", None)
    if prefixo:
        with open(f"{prefixo}_metas.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["categoria", "item", "valor", "meta", "atendido"])
            for cat, item, valor, meta, ok in linhas:
                w.writerow([cat, item, valor, meta, "sim" if ok else "nao"])
            for k, v in negocio.items():
                w.writerow(["regra_negocio", k, v, "", ""])
            w.writerow(["risco", "movimentações sem resposta (timeout)",
                        sum(len(v) for v in sem_resposta.values()), "", ""])
            for pid, ini, ac, fin, dif in explicadas:
                w.writerow(["risco", f"produto {pid} gravado sem confirmação",
                            f"inicial {ini} + aceitos {ac} != final {fin} ({dif:+d})", "", "atencao"])


def _soma_de_subconjunto(valores, alvo):
    """True se algum subconjunto não vazio de 'valores' soma 'alvo' (poucos itens: força bruta)."""
    from itertools import combinations
    return any(sum(c) == alvo for n in range(1, len(valores) + 1) for c in combinations(valores, n))


# --------------------------------------------------------------------------- perfil contínuo opcional
if os.getenv("PERFIL") == "estresse_recuperacao":
    class EstresseRecuperacao(LoadTestShape):
        """Estresse com USUARIOS_ESTRESSE (padrão 200) por 90 s e, sem parar, 20 usuários por 90 s."""
        ESTRESSE = int(os.getenv("USUARIOS_ESTRESSE", "200"))

        def tick(self):
            t = self.get_run_time()
            queda = 90 if estado["protecao_em"] is None else min(90, estado["protecao_em"])
            if t < queda:
                return (self.ESTRESSE, min(100, max(1, self.ESTRESSE // 10)))
            if t < queda + 90:
                return (20, 100)
            return None
