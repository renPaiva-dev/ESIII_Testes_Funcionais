"""
Desafio B - consulta de minicursos.

GET /api/cursos (peso 7) e GET /api/cursos/1 (peso 3), conferindo o conteúdo.
Metas: com 20 usuários, p95 <= 500 ms e falhas <= 1%.
Proteção do guia: para sozinho se falhas > 20% ou p95 > 2000 ms por 10 s seguidos.
PERFIL=estresse_recuperacao roda 100 usuários e depois 20, sem reiniciar.

    python -m locust -f desafio_locust.py --host http://127.0.0.1:8000 --headless -u 20 -r 2 -t 90s
"""
import os
import time

import gevent
from locust import HttpUser, LoadTestShape, between, events, task
from locust.runners import STATE_CLEANUP, STATE_STOPPED, STATE_STOPPING, WorkerRunner

CURSOS_ESPERADOS = {1: "Python", 2: "Java", 3: "Testes de Software"}
LISTAGEM = "GET /api/cursos"
DETALHE = "GET /api/cursos/1"

# Proteção do guia: falhas > 20% ou p95 > 2000 ms, por 10 s seguidos
PROTECAO_FALHAS = 0.20
PROTECAO_P95_MS = 2000
PROTECAO_JANELA_S = 10


class Visitante(HttpUser):
    """Aluno consultando os minicursos (modelo fechado: repete as consultas)."""
    wait_time = between(0.2, 0.6)

    @task(7)
    def listar_cursos(self):
        with self.client.get("/api/cursos", name=LISTAGEM, catch_response=True, timeout=5) as r:
            if r.status_code != 200:
                r.failure(f"HTTP {r.status_code}")
                return
            try:
                dados = r.json()
                nomes = {c["id"]: c["nome"] for c in dados["itens"]}
                if dados["total"] != 3 or len(dados["itens"]) != 3:
                    r.failure(f"total = {dados['total']}, esperado 3")
                elif nomes != CURSOS_ESPERADOS:
                    r.failure(f"cursos inesperados: {nomes}")
            except (ValueError, KeyError, TypeError):
                r.failure("Resposta inválida")

    @task(3)
    def detalhar_curso(self):
        with self.client.get("/api/cursos/1", name=DETALHE, catch_response=True, timeout=5) as r:
            if r.status_code != 200:
                r.failure(f"HTTP {r.status_code}")
                return
            try:
                c = r.json()
                if (c["id"], c["nome"], c["vagas"]) != (1, "Python", 2):
                    r.failure(f"detalhe incoerente: {c}")
            except (ValueError, KeyError, TypeError):
                r.failure("Resposta inválida")


# proteção
estado = {"protecao_em": None}  # segundos desde o início em que a proteção disparou


def _vigiar(environment):
    """A cada segundo olha a janela corrente (últimos ~10 s) e conta segundos ruins seguidos."""
    runner = environment.runner
    inicio = time.time()
    ruins = 0
    while runner.state not in (STATE_STOPPING, STATE_STOPPED, STATE_CLEANUP):
        gevent.sleep(1)
        total = runner.stats.total
        rps = total.current_rps
        taxa_falhas = total.current_fail_per_sec / rps if rps else 0
        p95 = total.get_current_response_time_percentile(0.95) or 0
        ruins = ruins + 1 if (taxa_falhas > PROTECAO_FALHAS or p95 > PROTECAO_P95_MS) else 0
        if ruins >= PROTECAO_JANELA_S and estado["protecao_em"] is None:
            decorrido = time.time() - inicio
            estado["protecao_em"] = decorrido
            motivo = (f"falhas {taxa_falhas:.0%} (limite {PROTECAO_FALHAS:.0%})"
                      if taxa_falhas > PROTECAO_FALHAS else f"p95 {p95} ms (limite {PROTECAO_P95_MS} ms)")
            msg = f"PROTEÇÃO ACIONADA em {decorrido:.0f} s: {motivo} por {PROTECAO_JANELA_S} s seguidos"
            print(f"\n[PROTEÇÃO] {msg}", flush=True)
            prefixo = getattr(environment.parsed_options, "csv_prefix", None)
            if prefixo:
                with open(f"{prefixo}_protecao.txt", "w", encoding="utf-8") as f:
                    f.write(msg + "\n")
            if environment.shape_class is None:
                runner.quit()  # fase comum: encerra a execução
                return
            # perfil contínuo: o shape reduz a carga para 20 (ver EstresseRecuperacao)


@events.test_start.add_listener
def _iniciar_vigia(environment, **_):
    estado["protecao_em"] = None
    if not isinstance(environment.runner, WorkerRunner):
        gevent.spawn(_vigiar, environment)


@events.quitting.add_listener
def relatorio_final(environment, **_):
    total = environment.stats.total
    if total.num_requests == 0:
        return
    p95 = total.get_response_time_percentile(0.95)
    print(f"\n[META] agregado da execução: p95 = {p95:.0f} ms (meta 500) | "
          f"falhas = {total.fail_ratio:.2%} (meta 1%) | {total.num_requests} requisições")
    if estado["protecao_em"] is not None:
        if environment.shape_class is None:
            print("[META] execução INTERROMPIDA pela proteção")
        else:
            print("[META] proteção acionada: carga reduzida para 20 usuários (recuperação medida a partir daí)")


# perfil contínuo opcional
if os.getenv("PERFIL") == "estresse_recuperacao":
    class EstresseRecuperacao(LoadTestShape):
        """100 usuários por 90 s e depois 20 usuários por 90 s, sem reiniciar o Locust."""
        ESTRESSE_S = 90
        RECUPERACAO_S = 90

        def tick(self):
            t = self.get_run_time()
            queda = self.ESTRESSE_S
            if estado["protecao_em"] is not None:  # proteção: reduz a carga na hora
                queda = min(queda, estado["protecao_em"])
            if t < queda:
                return (100, 10)
            if t < queda + self.RECUPERACAO_S:
                return (20, 100)
            return None
