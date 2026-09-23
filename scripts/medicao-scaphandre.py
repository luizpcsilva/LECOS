import time
import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import psutil

"""
Mede o consumo estimado (Ce) de DOIS estressores em paralelo, pelo exportador JSON
do scaphandre.

NAO aplica equacao nenhuma do protocolo: soma o que o scaphandre atribuiu a cada
arvore de pids, converte uW para W e reporta. Eq. 4 e Eq. 5 ficam para a analise.

Grava a serie em testes/scaphandre/*.csv e delega a reducao a escalar para o
calculo-melhor-janela-scaphandre.py.

Porques (exportador, flags, schema, armadilhas): references/scaphandre.md
"""

NOME_CONTAINER = "scaphandre_json"
MAX_CONSUMIDORES = 50   #o default de 10 corta workers do stress-ng
COM_RECURSOS = True     #flag --resources: habilita cpu_p1_pct/cpu_p2_pct
SALVAR_BRUTO = True     #arquiva o json cru DEPOIS da medicao, pra depurar
ESPERA = 2              #segundos ate os workers do stress-ng nascerem
TIMEOUT_PRONTO = 30     #segundos esperando as 2 primeiras amostras do scaphandre
TIMEOUT_PARADA = 30     #segundos esperando o container morrer apos o docker stop

#tmpfs: e ram, nao disco - nada e escrito em disco dentro da janela medida
CAMINHO_JSON = "/dev/shm/scaphandre-saida.json"
CAMINHO_ERRO = "/dev/shm/scaphandre-erro.log"

COLUNAS = [
    "epoch_s",        #host.timestamp do scaphandre
    "t_rel_s",        #segundos desde o inicio dos estressores
    "delta_t_s",      #espacamento ate a amostra anterior - detecta passo perdido
    "ce_p1_uw",
    "ce_p2_uw",
    "host_uw",        #host.consumption - base que o scaphandre rateia (psys se houver)
    "socket0_uw",     #sockets[id=0] - package, mesma base do rapl do lecos
    "soma_todos_uw",
    "cpu_p1_pct",
    "cpu_p2_pct",
    "n_pids_p1",
    "n_pids_p2",
]

#configuração dos argumentos passados via terminal
parser = argparse.ArgumentParser(description="")
parser.add_argument("freq", type=float, help="frequencia da amostragem (em segundos)")
parser.add_argument("estressor", type=str, help="estressor alvo P1")
parser.add_argument("estressor2", type=str, help="estressor alvo P2")

args = parser.parse_args()
nome_cenario = args.estressor + "-" + args.estressor2
args.estressor = args.estressor.split()
args.estressor2 = args.estressor2.split()


def descendentes(pid):
    """o proprio pid mais todos os descendentes, como um set"""
    return {pid} | {filho.pid for filho in psutil.Process(pid).children(recursive=True)}


def montar_comando():
    """chamada do container com o exportador json - flags explicadas em scaphandre.md"""
    comando = [
        "docker", "run", "--rm", "--name", NOME_CONTAINER, "--privileged",
        "-v", "/sys/class/powercap:/sys/class/powercap",
        "-v", "/proc:/proc",
        "hubblo/scaphandre", "json",
        "-s", str(max(1, int(args.freq))),
        "--max-top-consumers", str(MAX_CONSUMIDORES),
    ]
    if COM_RECURSOS:
        comando.append("--resources")
    return comando


def esperar_scaphandre(processo, minimo=2):
    """espera 'minimo' amostras ANTES de carregar a maquina - a primeira vem zerada"""
    limite = time.time() + TIMEOUT_PRONTO
    while time.time() < limite:
        if Path(CAMINHO_JSON).read_text().count('"host"') >= minimo:
            return
        if processo.poll() is not None:
            sys.exit(f"container do scaphandre encerrou com codigo {processo.returncode} "
                     f"antes de emitir {minimo} amostras; veja {CAMINHO_ERRO}")
        time.sleep(0.5)

    print(f"aviso: scaphandre nao emitiu {minimo} amostras em {TIMEOUT_PRONTO}s; "
          f"seguindo mesmo assim", file=sys.stderr)


def carregar_relatorios(texto):
    """array incremental: abre com '[', anexa objetos e fecha com ']' na saida normal.
    como paramos o container com sigterm, o ']' pode nao sair - ver scaphandre.md"""
    texto = texto[texto.find("["):] if "[" in texto else texto
    for candidato in (texto, texto + "]", texto[:texto.rfind("},") + 1] + "]"):
        try:
            relatorios = json.loads(candidato)
        except (json.JSONDecodeError, ValueError):
            continue
        if relatorios:
            return relatorios

    sys.exit("saida do scaphandre nao tem nenhuma amostra completa")


def valor(dicionario, chave):
    """le um numero tolerando chave ausente e None"""
    try:
        return float(dicionario.get(chave))
    except (TypeError, ValueError):
        return 0.0


def cpu_do_consumidor(consumidor):
    """resources_usage so existe com --resources, e cpu_usage vem como string"""
    recursos = consumidor.get("resources_usage") or {}
    return valor(recursos, "cpu_usage")


def agregar(relatorios, pids_p1, pids_p2, epoch_inicio, epoch_abertura, epoch_fim):
    """soma o consumo por conjunto de pid em cada amostra dentro da janela.
    a separacao e por arvore de pids, nao por label - ver scaphandre.md secao 4"""
    linhas = []
    epoch_anterior = None

    for amostra in relatorios:
        host = amostra.get("host") or {}
        epoch = valor(host, "timestamp")

        #so o intervalo em que os dois rodavam com a arvore de pids ja enumerada
        if not (epoch_abertura <= epoch <= epoch_fim):
            continue

        socket0_uw = next((valor(socket, "consumption")
                           for socket in amostra.get("sockets") or []
                           if socket.get("id") == 0), 0.0)

        ce_p1 = ce_p2 = soma_todos = cpu_p1 = cpu_p2 = 0.0
        n_p1 = n_p2 = 0

        for consumidor in amostra.get("consumers") or []:
            pid = consumidor.get("pid")
            potencia = valor(consumidor, "consumption")
            soma_todos += potencia
            if pid in pids_p1:
                ce_p1 += potencia
                cpu_p1 += cpu_do_consumidor(consumidor)
                n_p1 += 1
            elif pid in pids_p2:
                ce_p2 += potencia
                cpu_p2 += cpu_do_consumidor(consumidor)
                n_p2 += 1

        delta_t = epoch - epoch_anterior if epoch_anterior is not None else 0.0
        epoch_anterior = epoch

        linhas.append([epoch, epoch - epoch_inicio, delta_t, ce_p1, ce_p2,
                       valor(host, "consumption"), socket0_uw, soma_todos,
                       cpu_p1, cpu_p2, n_p1, n_p2])

    return linhas


#--------------------- Inicio Medição ----------------------
#stdout do container direto num arquivo em tmpfs: sem pipe, sem buffer para estourar
with open(CAMINHO_JSON, "w") as saida, open(CAMINHO_ERRO, "w") as erro:
    processo_scaphandre = subprocess.Popen(montar_comando(), stdout=saida, stderr=erro)

processo_estressor = processo_estressor2 = None

try:
    esperar_scaphandre(processo_scaphandre)

    epoch_inicio = time.time()
    processo_estressor = subprocess.Popen(args.estressor, stdout=subprocess.DEVNULL)
    processo_estressor2 = subprocess.Popen(args.estressor2, stdout=subprocess.DEVNULL)

    #espera os workers nascerem e enumera a arvore de cada estressor uma unica vez
    time.sleep(ESPERA)
    pids_p1 = descendentes(processo_estressor.pid)
    pids_p2 = descendentes(processo_estressor2.pid)
    epoch_abertura = time.time()

    processo_estressor.wait()
    processo_estressor2.wait()
    epoch_fim = time.time()
finally:
    #estressor sobrevivente queimaria cpu e contaminaria a rodada seguinte
    for processo in (processo_estressor, processo_estressor2):
        if processo is not None and processo.poll() is None:
            processo.kill()
            processo.wait()

    #o rm -f garante que nao sobra container para a proxima das 165 rodadas
    for comando in (["docker", "stop", NOME_CONTAINER],
                    ["docker", "rm", "-f", NOME_CONTAINER]):
        subprocess.run(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        processo_scaphandre.wait(timeout=TIMEOUT_PARADA)
    except subprocess.TimeoutExpired:
        processo_scaphandre.kill()
        processo_scaphandre.wait()
#--------------------- Fim Medição -------------------------

texto_json = Path(CAMINHO_JSON).read_text()

carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
os.makedirs("testes/scaphandre", exist_ok=True)

#arquiva o json cru so agora, depois do fim da medicao
if SALVAR_BRUTO:
    os.makedirs("testes/scaphandre/bruto", exist_ok=True)
    shutil.copy(CAMINHO_JSON, f"testes/scaphandre/bruto/{carimbo}.json")

for caminho in (CAMINHO_JSON, CAMINHO_ERRO):
    os.remove(caminho)

relatorios = carregar_relatorios(texto_json)
output = agregar(relatorios, pids_p1, pids_p2, epoch_inicio, epoch_abertura, epoch_fim)

if not output:
    sys.exit(f"nenhuma das {len(relatorios)} amostras do scaphandre caiu na janela "
             f"dos estressores; confira o passo (-s) e a duracao (-t)")

#criando output em csv do experimento
nome_csv = nome_cenario.replace(" ", "-") + "-" + carimbo + ".csv"
caminho_csv = "testes/scaphandre/" + nome_csv
with open(caminho_csv, mode="w") as arquivo_csv:
    escritor = csv.writer(arquivo_csv)
    escritor.writerow(COLUNAS)
    escritor.writerows(output)

#reduz a serie a dois escalares (janela de 10 amostras mais estavel)
resultado = subprocess.run(
    ["venv/bin/python", "scripts/calculo-melhor-janela-scaphandre.py", nome_csv, caminho_csv],
    capture_output=True,
    text=True
)

print(resultado.stdout, end="")

#repassa o stderr do redutor SEMPRE, nao so em caso de erro: o aviso de "poucas
#amostras" sinaliza medicao degradada e nao pode sumir no meio de uma bateria
if resultado.stderr:
    print(resultado.stderr, file=sys.stderr, end="")
if resultado.returncode != 0:
    sys.exit(resultado.returncode)
