import time
import argparse
import csv
import os
import re
import sys
from datetime import datetime
import subprocess
from urllib.request import urlopen

import pandas as pd

"""
Mede o consumo estimado (Ce) de DOIS estressores executados em paralelo, lendo o
endpoint /metrics do exportador prometheus do scaphandre.

Ao fim, imprime a media de Ce de P1 e de P2 (em watts) em linhas separadas, para
o protocolo.sh capturar com { read CE_P1; read CE_P2; }
"""

URL = "http://localhost:8080/metrics"
ESPERA = 2      #segundos ate os workers do stress-ng nascerem
DESCARTAR = 2   #o scaphandre devolve zero enquanto nao tem duas requisicoes
JANELA = 10     #amostras da janela usada no calculo da media
DUMP_BRUTO = 8  #quantas das primeiras amostras salvam o /metrics cru, pra depurar

METRICA_POTENCIA = "scaph_process_power_consumption_microwatts"
METRICA_CPU = "scaph_process_cpu_usage_percentage"
METRICA_HOST = "scaph_host_power_microwatts"
METRICA_ENERGIA = "scaph_host_energy_microjoules"

#o valor e sempre o ultimo campo da linha, entao o .* guloso vai ate a ultima
#chave; a ordem dos labels varia entre linhas e alguns vem vazios
LINHA_METRICA = re.compile(r"^(scaph_\w+)\{(.*)\}\s+([-+0-9.eE]+)$")
LINHA_HOST = re.compile(METRICA_HOST + r"(?:\{.*\})?\s+([-+0-9.eE]+)$")
LINHA_ENERGIA = re.compile(r"^" + METRICA_ENERGIA + r"\s+([-+0-9.eE]+)$", re.M)
LABEL_PID = re.compile(r'pid="(\d+)"')

COLUNAS = [
    "timestamp_s",
    "epoch_s",
    "ce_p1_uw",
    "ce_p2_uw",
    "host_uw",
    "soma_todos_uw",
    "cpu_p1_pct",
    "cpu_p2_pct",
    "viu_host",
    "viu_processo",
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

output = []


def descendentes(pid):
    """retorna o proprio pid e todos os seus descendentes, como um set"""
    encontrados = {pid}
    pilha = [pid]
    while pilha:
        atual = pilha.pop()
        for tid in os.listdir(f"/proc/{atual}/task"):
            with open(f"/proc/{atual}/task/{tid}/children") as children:
                for filho in map(int, children.read().split()):
                    if filho not in encontrados:
                        encontrados.add(filho)
                        pilha.append(filho)
    return encontrados


def esperar_scaphandre_pronto(timeout=30):
    """espera scaph_host_energy_microjoules avancar pelo menos uma vez, confirmando
    que o sensor RAPL do scaphandre completou um ciclo de leitura. sem isso, um
    container recem-criado pode ficar com o contador congelado indefinidamente sob
    carga pesada - achado de 2026-09-22, energia parada em 50079407746 por 8s"""
    inicio = time.time()
    primeiro_valor = None
    while time.time() - inicio < timeout:
        with urlopen(URL) as resposta:
            texto = resposta.read().decode()
        achado = LINHA_ENERGIA.search(texto)
        if achado:
            valor = float(achado.group(1))
            if primeiro_valor is None:
                primeiro_valor = valor
            elif valor != primeiro_valor:
                return   # contador avancou - sensor esta vivo
        time.sleep(1)

    sys.exit(f"scaphandre nao avancou {METRICA_ENERGIA} em {timeout}s; "
              f"confira 'docker logs scaphandre' antes de prosseguir")


def leitorScaphandre(pids_p1, pids_p2, caminho_bruto=None):
    """faz uma requisicao ao /metrics e soma os valores por conjunto de pid.

    se caminho_bruto for dado, salva o texto cru da resposta antes de parsear -
    usado nas primeiras amostras pra depurar se o scaphandre ja esta emitindo
    as metricas de processo/host ou se elas ainda nao apareceram no payload"""
    with urlopen(URL) as resposta:
        texto = resposta.read().decode()

    if caminho_bruto:
        with open(caminho_bruto, "w") as bruto:
            bruto.write(texto)

    ce_p1 = ce_p2 = host = soma_todos = cpu_p1 = cpu_p2 = 0.0
    viu_host = viu_processo = False

    for linha in texto.splitlines():
        if linha.startswith(METRICA_HOST):
            achado_host = LINHA_HOST.match(linha)
            if achado_host is None:
                continue   # cobre formatos inesperados (ex.: "NaN") sem quebrar
            host = float(achado_host.group(1))
            viu_host = True
            continue

        achado = LINHA_METRICA.match(linha)
        if achado is None:
            continue

        rotulo = LABEL_PID.search(achado.group(2))
        if rotulo is None:
            continue

        metrica = achado.group(1)
        valor = float(achado.group(3))
        pid = int(rotulo.group(1))

        if metrica == METRICA_POTENCIA:
            viu_processo = True
            soma_todos += valor
            if pid in pids_p1:
                ce_p1 += valor
            elif pid in pids_p2:
                ce_p2 += valor
        elif metrica == METRICA_CPU:
            if pid in pids_p1:
                cpu_p1 += valor
            elif pid in pids_p2:
                cpu_p2 += valor

    return [ce_p1, ce_p2, host, soma_todos, cpu_p1, cpu_p2, viu_host, viu_processo]


#--------------------- Inicio Medição ----------------------
#garante que o sensor do scaphandre ja completou um ciclo ANTES de carregar a
#maquina - sem isso, um container recem-criado pode nunca sair do zero
esperar_scaphandre_pronto()

carimbo_execucao = datetime.now().strftime("%Y%m%d_%H%M%S")
os.makedirs("testes/scaphandre/bruto", exist_ok=True)

processo_estressor = subprocess.Popen(args.estressor, stdout=subprocess.DEVNULL)
processo_estressor2 = subprocess.Popen(args.estressor2, stdout=subprocess.DEVNULL)

#espera os workers nascerem e enumera a arvore de cada estressor uma unica vez
time.sleep(ESPERA)
pids_p1 = descendentes(processo_estressor.pid)
pids_p2 = descendentes(processo_estressor2.pid)

n_amostra = 0
while (processo_estressor.poll() is None) or (processo_estressor2.poll() is None):
    #salva o /metrics cru das primeiras DUMP_BRUTO amostras pra depurar se as
    #linhas de host/processo demoram a aparecer num container recem-criado
    caminho_bruto = None
    if n_amostra < DUMP_BRUTO:
        caminho_bruto = f"testes/scaphandre/bruto/{carimbo_execucao}-amostra{n_amostra:02d}.txt"

    leitura = leitorScaphandre(pids_p1, pids_p2, caminho_bruto)
    n_amostra += 1

    #as primeiras requisicoes nao tem janela anterior e devolvem zero
    if n_amostra > DESCARTAR:
        output.append([time.perf_counter(), time.time()] + leitura)

    time.sleep(args.freq)
#--------------------- Fim Medição -------------------------

#criando output em csv do experimento
nome_csv = (
    nome_cenario.replace(" ", "-") + "-" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
)
caminho_csv = "testes/scaphandre/" + nome_csv
os.makedirs("testes/scaphandre", exist_ok=True)
with open(caminho_csv, mode="w") as arquivo_csv:
    escritor = csv.writer(arquivo_csv)
    escritor.writerow(COLUNAS)
    escritor.writerows(output)

#calcula a melhor media
df = pd.DataFrame(output, columns=COLUNAS)
df["frac_p1"] = df["ce_p1_uw"] / (df["ce_p1_uw"] + df["ce_p2_uw"])

desvio_padrao_janela = df["frac_p1"].rolling(window=JANELA).std()
indice_melhor_janela = desvio_padrao_janela.idxmin()

media_p1 = df["ce_p1_uw"].rolling(window=JANELA).mean().loc[indice_melhor_janela]
media_p2 = df["ce_p2_uw"].rolling(window=JANELA).mean().loc[indice_melhor_janela]
desvio_padrao = desvio_padrao_janela.loc[indice_melhor_janela]

#converte p watts
ce_p1 = media_p1 / 10**6
ce_p2 = media_p2 / 10**6

#anexando valores finais no log de testes
with open("log.csv", mode="a") as log_csv:
    escritor = csv.writer(log_csv)
    escritor.writerow(["scaphandreP1-" + nome_csv, ce_p1, desvio_padrao])
    escritor.writerow(["scaphandreP2-" + nome_csv, ce_p2, desvio_padrao])

#imprimindo para protocolo.sh
print(ce_p1)
print(ce_p2)
