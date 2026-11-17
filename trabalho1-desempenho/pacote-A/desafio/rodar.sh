#!/usr/bin/env bash
# Roda o Desafio A e guarda as evidências em ../../resultados/pacote-A-desafio/
#
# Uso:   ./rodar.sh <tipo> [repeticoes]
#        tipo = verificacao | carga | pico | estresse
# Ex.:   ./rodar.sh carga 3      -> carga_r1, carga_r2, carga_r3
#
# Antes: ative o venv com locust e suba o sistema A (python app.py, porta 5000).
# O locustfile zera o sistema sozinho no início de cada execução.
set -euo pipefail

TIPO=${1:?informe o tipo: verificacao, carga, pico ou estresse}
REPETICOES=${2:-1}
HOST=${HOST:-http://127.0.0.1:5000}
# Python com o locust instalado. Padrão: o do venv ativo ("python"); senão python3.
PYTHON=${PYTHON:-$(command -v python || command -v python3)}
"$PYTHON" -c "import locust" 2>/dev/null || { echo "Locust não encontrado em $PYTHON (ative o venv ou defina PYTHON=...)"; exit 1; }
PASTA="$(cd "$(dirname "$0")" && pwd)"
SAIDA="$PASTA/../../resultados/pacote-A-desafio"
mkdir -p "$SAIDA"

curl -sf "$HOST/health" > /dev/null || { echo "Sistema A fora do ar em $HOST"; exit 1; }

for i in $(seq 1 "$REPETICOES"); do
  PREFIXO="$SAIDA/${TIPO}_r$i"
  echo "=== $TIPO, repetição $i de $REPETICOES -> $PREFIXO"
  # Locust sai com código 1 quando o SLA não é atendido: isso é resultado, não erro do script.
  TIPO_TESTE=$TIPO "$PYTHON" -m locust -f "$PASTA/locustfile_matricula.py" --host "$HOST" \
    --headless --only-summary --csv "$PREFIXO" --csv-full-history --html "$PREFIXO.html" \
    2>&1 | tee "$PREFIXO.log" || true
  "$PYTHON" "$PASTA/analisar_patamares.py" "${PREFIXO}_stats_history.csv" | tee "${PREFIXO}_patamares.md"
done

# Atualiza a comparação entre as repetições de todos os tipos (comparacao.md)
"$PYTHON" "$PASTA/comparar_repeticoes.py" "$SAIDA" > /dev/null && echo "Comparação atualizada: $SAIDA/comparacao.md"
