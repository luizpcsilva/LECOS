import pandas as pd
import numpy as np
import argparse
import csv

"""
O seguinte algoritmo calcula a melhor média amostral
de uma série de registros de energia e de tempo, utilizando pandas.

O critério utilizado é selecionar o melhor intervalo de medição de 10 segundos
em que os valores de energia desse intervalo tenham o menor desvio padrão.

Ao fim da execução, os valores são salvos no arquivo log.txt, com o identi
ficador do experimento na coluna nome (entrada desse código)
"""


#configuração dos argumentos passados via terminal
parser = argparse.ArgumentParser(description="")
parser.add_argument("nome_csv", type=str, help="nome do arquivo que será salvo")
parser.add_argument("caminho_csv", type=str, help="caminho do arquivo para calcular a media")

args = parser.parse_args()

#calcula a melhor media do idle com pandas(intervalo de 10 segundos com menor desvio padrao)
df = pd.read_csv(args.caminho_csv)

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
with open("../log.csv", mode="a") as log_csv:
    escritor = csv.writer(log_csv)
    escritor.writerow([args.nome_csv, potencia_media, desvio_padrao])

#imprimindo para protocolo.sh
print(potencia_media)