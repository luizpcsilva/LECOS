import time
import argparse
import csv
from datetime import datetime
import pandas as pd
import numpy as np

#configuração dos argumentos passados via terminal
parser = argparse.ArgumentParser(description="")
parser.add_argument("duracao", type=float, help="duracao da medicao em idle")
parser.add_argument("freq", type=float, help="frequencia da amostragem do rapl (em segundos)")

args = parser.parse_args()

output = []

#retorna o valor do contador de microjoule de package como string
def leitorRapl():
    with open("/sys/class/powercap/intel-rapl/subsystem/intel-rapl:0/energy_uj", "r") as rapl:
        valor = rapl.readline().strip()
        return valor
    
def loopLeitorRapl(duracao, output, freq): 
    tempoInicio = time.perf_counter()
    tempo = tempoInicio
    while (tempo - tempoInicio <= duracao): 
        leitura = [0] * 2
        leitura[0] = leitorRapl()
        leitura[1] = tempo
        time.sleep(args.freq)
        tempo = time.perf_counter()

        output.append(leitura)

#--------------------- Inicio Medição ----------------------
loopLeitorRapl(args.duracao, output, args.freq)
#--------------------- Fim Medição -------------------------

#anexando output em csv do experimento
nome_csv = "idle_" + str(datetime.now()) + ".csv"
with open("testes/idle/"+nome_csv, mode="w") as arquivo_csv:
    escritor = csv.writer(arquivo_csv)
    escritor.writerow(["energia_uj", "timestamp_s"])
    escritor.writerows(output)

#calcula a melhor media do idle com pandas(intervalo de 10 segundos com menor desvio padrao)
df = pd.read_csv(nome_csv)

#calcula os deltas de tempo e energia
df['delta_t'] = df['timestamp_s'].diff()
df['delta_e'] = df['energia_uj'].diff()
df = df.dropna() #exclui a primeira linha

#converte para watts:
df['potencia_w'] = (df['delta_e'] * (10**-6)) / df['delta_t']

#obtem a melhor janela amostral
tamanho_janela = 10
df['desvio_padrao_janela'] = df['potencia_w'].rolling(window=tamanho_janela).std()
df['media_janela'] = df['potencia_w'].rolling(window=tamanho_janela).mean()

indice_melhor_janela = df['desvio_padrao_janela'].idxmin()

potencia_media = df.loc[indice_melhor_janela, 'media_janela']
desvio_padrao = df.loc[indice_melhor_janela, 'desvio_padrao_janela']

#anexando valor final no log de testes
with open("log.csv", mode="a") as log_csv:
    escritor = csv.writer(log_csv)
    escritor.writerow([nome_csv, potencia_media, desvio_padrao])