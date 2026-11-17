"""
DESAFIO A - Trabalho 1: abertura da matrícula 2026.2 (Locust / Python)

Situação: às 19h a coordenação libera a matrícula e os 200 alunos entram no portal
quase juntos. Cada usuário virtual (VU) é UM aluno, que percorre a jornada real:

    consultar a oferta  ->  matricular-se  ->  baixar o comprovante

Metas da coordenação (SLA), verificadas automaticamente no fim da execução:
    - p95 geral                  <= 800 ms
    - p95 do comprovante         <= 1500 ms
    - erros técnicos (5xx, timeout, resposta incoerente) < 1%
    - nunca pode haver vagas negativas (integridade)
409 e 422 são REGRAS DE NEGÓCIO corretas: contam como sucesso no Locust e são
contadas à parte no arquivo <prefixo>_regras.csv.

Tipo de teste pela variável TIPO_TESTE:
    verificacao  1 aluno por 15 s (confere o script antes dos testes de verdade)
    carga        rampa de 10 s até 100 alunos + 120 s com 100 alunos
    pico         0 -> 200 alunos em 10 s, mantém 60 s, cai para 20 por 30 s (recuperação)
    estresse     degraus de +50 alunos a cada 30 s: 50, 100, ..., 400

Executar (sistema A no ar em http://127.0.0.1:5000):
    TIPO_TESTE=carga python -m locust -f locustfile_matricula.py --host http://127.0.0.1:5000 \
        --headless --csv ../../resultados/pacote-A-desafio/carga_r1 --csv-full-history \
        --html ../../resultados/pacote-A-desafio/carga_r1.html
    (ou use ./rodar.sh carga 1)

O script zera o sistema sozinho no início (POST /api/admin/reset). Para não zerar: RESET=0.
Use 127.0.0.1 e não "localhost": no Linux, localhost tenta IPv6 primeiro e cada
requisição perde ~2 s, o que falsifica a medição.
"""
import csv
import itertools
import os
import random
import re
from collections import Counter

import requests
from locust import HttpUser, LoadTestShape, between, events, task

# --------------------------------------------------------------------------- metas
SLA_P95_GERAL_MS = 800
SLA_P95_COMPROVANTE_MS = 1500
SLA_ERRO_TECNICO_MAX = 0.01      # 1 %

TOTAL_ALUNOS = 200               # 20260001 ... 20260200 existem no sistema
MAX_TENTATIVAS = 3               # vagas esgotadas: tenta de novo com a oferta atualizada
MAX_DOWNLOADS = 2                # cada aluno baixa o comprovante no máximo 2 vezes
TIMEOUT_S = 10                   # acima disso a requisição conta como timeout (erro técnico)

OFERTA = "GET /api/disciplinas"
MATRICULA = "POST /api/matriculas"
COMPROVANTE = "GET /api/matriculas/[id]/comprovante"
RE_COMPROVANTE = re.compile(r"COMP-\d{6}")

# --------------------------------------------------------------------------- estado compartilhado
# O Locust roda os VUs em greenlets (gevent) num único processo: estes dicionários
# são compartilhados entre todos os alunos virtuais.
_sequencia = itertools.count()
matricula_do_aluno = {}          # aluno -> id da matrícula (para baixar o comprovante)
regras = Counter()               # respostas de regra de negócio (409/422) e desistências
vagas_iniciais = {}              # codigo -> vagas logo após o reset
vagas_consumidas = Counter()     # codigo -> quantas matrículas 201 incluíram a disciplina
matriculas_por_aluno = Counter() # aluno -> quantos 201 recebeu (deve ser no máximo 1)
vagas_negativas_vistas = []      # (codigo, vagas) se alguma consulta mostrar vagas < 0
integridade = {}                 # preenchido no fim do teste


def _limpar_estado():
    for estrutura in (matricula_do_aluno, regras, vagas_iniciais, vagas_consumidas,
                      matriculas_por_aluno, integridade):
        estrutura.clear()
    vagas_negativas_vistas.clear()


def escolher_disciplinas(oferta):
    """Sorteia de 2 a 4 disciplinas COM vaga e SEM choque de horário."""
    disponiveis = [d for d in oferta if d.get("vagas", 0) > 0]
    random.shuffle(disponiveis)
    quantidade = random.randint(2, 4)
    escolha, horarios = [], set()
    for d in disponiveis:
        if d["horario"] not in horarios:
            escolha.append(d["codigo"])
            horarios.add(d["horario"])
        if len(escolha) == quantidade:
            break
    return escolha


class Aluno(HttpUser):
    """Um aluno na abertura da matrícula.

    Pesos 5/3/2 enquanto o aluno está ativo (justificativa no README):
      - consultar a oferta é o mais comum: o aluno abre o portal e atualiza a página
        para acompanhar as vagas;
      - matricular acontece uma vez por aluno (ou até 3 tentativas se a vaga acabar);
      - o comprovante só existe depois da matrícula e é baixado no máximo 2 vezes.
    Quando a ação sorteada não faz sentido para o aluno naquele momento (ex.: comprovante
    antes de se matricular), ele consulta a oferta, como faria uma pessoa real.
    """
    wait_time = between(1, 4)    # tempo de leitura/decisão entre uma ação e outra

    def on_start(self):
        n = next(_sequencia)
        # VU 1 -> 20260001 ... VU 200 -> 20260200. Acima de 200 VUs (estresse) o aluno se
        # repete: representa o mesmo aluno numa segunda aba/aparelho.
        self.aluno = f"2026{n % TOTAL_ALUNOS + 1:04d}"
        self.oferta = []
        self.tentativas = 0
        self.downloads = 0
        self.desistiu = False

    # ------------------------------------------------------------------ jornada
    @task(5)
    def consultar_oferta(self):
        with self.client.get("/api/disciplinas", name=OFERTA, catch_response=True,
                             timeout=TIMEOUT_S) as r:
            if r.status_code != 200:
                r.failure(f"HTTP {r.status_code}")
                return
            try:
                oferta = r.json()
                negativas = [(d["codigo"], d["vagas"]) for d in oferta if d["vagas"] < 0]
                ok = len(oferta) == 7 and all(isinstance(d["vagas"], int) for d in oferta)
            except (ValueError, KeyError, TypeError):
                r.failure("Resposta inválida")
                return
            if negativas:
                vagas_negativas_vistas.extend(negativas)
                r.failure(f"Vagas negativas: {negativas}")
            elif not ok:
                r.failure("Oferta incompleta ou incoerente")
            else:
                self.oferta = oferta

    @task(3)
    def matricular(self):
        if self.aluno in matricula_do_aluno or self.desistiu:
            return self.consultar_oferta()          # já resolveu a matrícula
        if not self.oferta:
            self.consultar_oferta()
        disciplinas = escolher_disciplinas(self.oferta)
        if not disciplinas:
            regras["desistiu: nenhuma disciplina com vaga na oferta"] += 1
            self.desistiu = True
            return

        corpo = {"aluno": self.aluno, "disciplinas": disciplinas}
        with self.client.post("/api/matriculas", json=corpo, name=MATRICULA,
                              catch_response=True, timeout=TIMEOUT_S) as r:
            if r.status_code == 201:
                self._registrar_sucesso(r, disciplinas)
            elif r.status_code in (409, 422):
                r.success()                          # regra de negócio, não é erro técnico
                self._registrar_regra(r)
            else:
                r.failure(f"HTTP {r.status_code}")  # 5xx, 401, timeout (status 0)...

    @task(2)
    def baixar_comprovante(self):
        mid = matricula_do_aluno.get(self.aluno)
        if mid is None or self.downloads >= MAX_DOWNLOADS:
            return self.consultar_oferta()
        self.downloads += 1
        with self.client.get(f"/api/matriculas/{mid}/comprovante", name=COMPROVANTE,
                             catch_response=True, timeout=TIMEOUT_S) as r:
            if r.status_code != 200:
                r.failure(f"HTTP {r.status_code}")
                return
            try:
                dados = r.json()
                if dados["id"] != mid or not RE_COMPROVANTE.fullmatch(dados["comprovante"]):
                    r.failure("Comprovante incoerente")
            except (ValueError, KeyError, TypeError):
                r.failure("Resposta inválida")

    # ------------------------------------------------------------------ apoio
    def _registrar_sucesso(self, r, disciplinas):
        try:
            dados = r.json()
            ok = (isinstance(dados["id"], int) and dados["aluno"] == self.aluno
                  and dados["disciplinas"] == disciplinas
                  and RE_COMPROVANTE.fullmatch(dados["comprovante"]))
        except (ValueError, KeyError, TypeError):
            ok = False
        if not ok:
            r.failure("201 com corpo incoerente")
            return
        matricula_do_aluno[self.aluno] = dados["id"]
        matriculas_por_aluno[self.aluno] += 1
        for codigo in disciplinas:
            vagas_consumidas[codigo] += 1

    def _registrar_regra(self, r):
        try:
            mensagem = r.json().get("erro", "")
        except ValueError:
            mensagem = ""
        if mensagem.startswith("Vagas esgotadas"):
            regras["409 Vagas esgotadas"] += 1
            self.tentativas += 1
            self.oferta = []                        # força consultar a oferta atualizada
            if self.tentativas >= MAX_TENTATIVAS:
                regras["desistiu: vagas esgotadas após 3 tentativas"] += 1
                self.desistiu = True
        elif "já possui matrícula" in mensagem:
            regras["409 Aluno já possui matrícula"] += 1
            self.desistiu = self.aluno not in matricula_do_aluno
        else:
            regras[f"{r.status_code} {mensagem}"] += 1


# --------------------------------------------------------------------------- perfis de carga
class Perfil(LoadTestShape):
    """Curva de alunos simultâneos conforme TIPO_TESTE. Retorna (alunos, alunos criados/s)."""
    tipo = os.getenv("TIPO_TESTE", "carga")

    def tick(self):
        t = self.get_run_time()
        if self.tipo == "verificacao":
            return (1, 1) if t < 15 else None
        if self.tipo == "demo":
            return (100, 10) if t < 40 else None           # versão curta da carga, para apresentar ao vivo
        if self.tipo == "carga":
            return (100, 10) if t < 130 else None          # 10 s de rampa + 2 min com 100
        if self.tipo == "pico":
            if t < 70:
                return (200, 20)                            # 0 -> 200 em 10 s, mantém 60 s
            if t < 100:
                return (20, 100)                            # volta a 20: observa a recuperação
            return None
        if self.tipo == "estresse":
            alunos = 50 * (int(t // 30) + 1)                # 50, 100, ..., 400
            return (alunos, 50) if alunos <= 400 else None
        raise ValueError(f"TIPO_TESTE desconhecido: {self.tipo}")


# --------------------------------------------------------------------------- início e fim
@events.test_start.add_listener
def preparar(environment, **_):
    _limpar_estado()
    host = environment.host
    if os.getenv("RESET", "1") == "1":
        requests.post(f"{host}/api/admin/reset", timeout=10).raise_for_status()
    for d in requests.get(f"{host}/api/disciplinas", timeout=10).json():
        vagas_iniciais[d["codigo"]] = d["vagas"]


@events.test_stop.add_listener
def verificar_integridade(environment, **_):
    """Compara as vagas finais com as matrículas 201 que o próprio teste recebeu."""
    finais = {d["codigo"]: d["vagas"]
              for d in requests.get(f"{environment.host}/api/disciplinas", timeout=30).json()}
    integridade["vagas"] = []
    integridade["problemas"] = []
    for codigo, inicial in vagas_iniciais.items():
        final = finais.get(codigo)
        esperado = inicial - vagas_consumidas[codigo]
        integridade["vagas"].append((codigo, inicial, vagas_consumidas[codigo], final, esperado))
        if final is None or final < 0:
            integridade["problemas"].append(f"{codigo}: vagas finais = {final} (negativas!)")
        elif final != esperado:
            integridade["problemas"].append(f"{codigo}: final {final} != esperado {esperado}")
    duplicadas = sorted(a for a, n in matriculas_por_aluno.items() if n > 1)
    if duplicadas:
        integridade["problemas"].append(
            f"{len(duplicadas)} aluno(s) com mais de uma matrícula (R6 violada): {duplicadas[:5]}")
    if vagas_negativas_vistas:
        integridade["problemas"].append(f"consultas viram vagas negativas: {vagas_negativas_vistas[:5]}")


@events.quitting.add_listener
def relatorio_final(environment, **_):
    stats = environment.stats
    total = stats.total
    if total.num_requests == 0:
        return
    p95_geral = total.get_response_time_percentile(0.95)
    comp = stats.entries.get((COMPROVANTE, "GET"))
    p95_comp = comp.get_response_time_percentile(0.95) if comp and comp.num_requests else 0
    taxa_erro = total.fail_ratio

    criterios = [
        ("p95 geral", f"{p95_geral:.0f} ms", f"<= {SLA_P95_GERAL_MS} ms", p95_geral <= SLA_P95_GERAL_MS),
        ("p95 comprovante", f"{p95_comp:.0f} ms", f"<= {SLA_P95_COMPROVANTE_MS} ms",
         p95_comp <= SLA_P95_COMPROVANTE_MS),
        ("erros técnicos", f"{taxa_erro:.2%}", f"< {SLA_ERRO_TECNICO_MAX:.0%}", taxa_erro < SLA_ERRO_TECNICO_MAX),
        ("integridade das vagas", f"{len(integridade.get('problemas', []))} problema(s)", "0",
         not integridade.get("problemas")),
    ]
    print("\n================ DESAFIO A - abertura da matrícula ================")
    print(f"Tipo de teste: {Perfil.tipo}")
    for nome, obtido, meta, ok in criterios:
        print(f"[SLA] {nome:22} {obtido:>12}  (meta {meta:>9})  {'OK' if ok else 'NÃO ATENDIDO'}")
    print(f"Matrículas efetivadas (201): {sum(matriculas_por_aluno.values())} "
          f"({len(matriculas_por_aluno)} alunos distintos de {TOTAL_ALUNOS})")
    print("Regras de negócio (não contam como erro):")
    for chave, qtd in sorted(regras.items()):
        print(f"   {qtd:6}  {chave}")
    print("Vagas por disciplina: inicial / consumidas pelo teste / final / esperado")
    for codigo, inicial, consumidas, final, esperado in integridade.get("vagas", []):
        print(f"   {codigo}: {inicial:3} / {consumidas:3} / {final:3} / {esperado:3}")
    for problema in integridade.get("problemas", []):
        print(f"   PROBLEMA DE INTEGRIDADE: {problema}")
    aprovado = all(ok for *_, ok in criterios)
    print("[SLA] APROVADO" if aprovado else "[SLA] REPROVADO")

    prefixo = getattr(environment.parsed_options, "csv_prefix", None)
    if prefixo:
        with open(f"{prefixo}_regras.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["categoria", "item", "valor", "meta", "atendido"])
            for nome, obtido, meta, ok in criterios:
                w.writerow(["sla", nome, obtido, meta, "sim" if ok else "nao"])
            w.writerow(["matriculas", "efetivadas (201)", sum(matriculas_por_aluno.values()), "", ""])
            for chave, qtd in sorted(regras.items()):
                w.writerow(["regra_negocio", chave, qtd, "", ""])
            for codigo, inicial, consumidas, final, esperado in integridade.get("vagas", []):
                w.writerow(["vagas", codigo, f"inicial={inicial} consumidas={consumidas} final={final}",
                            f"esperado={esperado}", "sim" if final == esperado and final >= 0 else "nao"])
            for problema in integridade.get("problemas", []):
                w.writerow(["integridade", "problema", problema, "", "nao"])
    if not aprovado:
        environment.process_exit_code = 1
