import argparse
import json
import numpy as np
import matplotlib.pyplot as plt

def plotarGrafico(leitura):
    dados = np.array(leitura)

    p1_watts = dados[:, 0]
    p2_watts = dados[:, 1]
    total_watts = dados[:, 2]
    tempos = dados[:, 3]

    #calcula a taxa de amostragem das mediçoes
    taxaAmostragem = tempos[1] - tempos[0] if len(tempos) > 1 else 1.0

    #criando a figura e os eixos
    fig, ax = plt.subplots(figsize=(12, 6))

    #plotando as barras LADO A LADO
    #diminuímos a largura da barra para caberem duas no mesmo "segundo"
    largura_barra = taxaAmostragem / 2

    #barra do processo 1
    ax.bar(tempos - largura_barra/2, p1_watts, width=largura_barra, label='Processo 1', color='#1f77b4', alpha=0.8)

    #barra do processo 2
    ax.bar(tempos + largura_barra/2, p2_watts, width=largura_barra, label='Processo 2', color='#ff7f0e', alpha=0.8)

    #plotando a linha do consumo total
    ax.plot(tempos, total_watts, label='Gasto Total da Máquina', color='red', linewidth=2, marker='o', markersize=4)

    #configurações estéticas do gráfico
    ax.set_title('Consumo de Energia: Processos vs Máquina Total', fontsize=14, fontweight='bold')
    ax.set_xlabel('Tempo (Segundos)', fontsize=12)
    ax.set_ylabel('Potência (Watts)', fontsize=12)
    #adicionando grade no plano de fundo
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    #mostrando a legenda no canto superior direito
    ax.legend(loc='upper right')
    #ajustando as margens
    plt.tight_layout()

    #salva o grafico de barras lado a lado
    plt.savefig('grafico-scaphandre1.png', dpi=300)

    #criando novo grafico
    fig, ax = plt.subplots(figsize=(12, 6))

    #plotando as barras EMPILHADAS
    largura_barra = taxaAmostragem * 0.8

    #barra do processo 1
    ax.bar(tempos, p1_watts, width=largura_barra, label='Processo 1', color='#1f77b4', alpha=0.8)

    #barra do Processo 2 (em cima do processo 1)
    ax.bar(tempos, p2_watts, width=largura_barra, bottom=p1_watts, label='Processo 2', color='#ff7f0e', alpha=0.8)

    #plotando a linha do consumo total
    ax.plot(tempos, total_watts, label='Gasto Total da Máquina', color='red', linewidth=2, marker='o', markersize=4)

    #configurações estéticas do gráfico
    ax.set_title('Consumo de Energia: Processos vs Máquina Total', fontsize=14, fontweight='bold')
    ax.set_xlabel('Tempo (Segundos)', fontsize=12)
    ax.set_ylabel('Potência (Watts)', fontsize=12)
    #adicionando grade no fundo
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    #adicionando legenda
    ax.legend(loc='upper right')
    #ajustando as margens 
    plt.tight_layout()
    #salvando o gráfico
    plt.savefig('grafico-scaphandre2.png', dpi=300)

parser = argparse.ArgumentParser(description="Processa JSON do Scaphandre, analisa energia e gera gráfico.")
parser.add_argument("arquivoJson", type=str, help="Caminho para o JSON do Scaphandre")
parser.add_argument("arquivoTxtOut", type=str, help="Caminho para salvar os dados estruturados em TXT")
args = parser.parse_args()

with open(args.arquivoJson, 'r') as file:
    dados_json = json.load(file)

tempos_list = []
p1_watts_list = []
p2_watts_list = []
total_watts_list = []

for amostra in dados_json:
    #timestamp da medicao
    tempo_atual = amostra.get('host', {}).get('timestamp', 0)
    tempos_list.append(tempo_atual)
    
    #pega o consumo total da máquina
    total_w = amostra.get('host', {}).get('consumption', 0) / 1_000_000.0
    total_watts_list.append(total_w)
    
    #zera os contadores de watts
    watts_mat = 0.0
    watts_fib = 0.0
    
    #varre os processos ativos nessa medição
    for processo in amostra.get('consumers', []):
        #identifica o executavel e consumo do processo
        cmdline = processo.get('cmdline', '')
        consumo_w = processo.get('consumption', 0) * 10**(-6)
        
        #filtramos se é um processo da matriz ou do fibonacci. soma no contador se for
        if "stress-ng-matrix" in cmdline:
            watts_mat += consumo_w
        elif "stress-ng-cpu" in cmdline:
            watts_fib += consumo_w

    #guarda os valores na lista        
    p1_watts_list.append(watts_mat)
    p2_watts_list.append(watts_fib)

#calculando tempo
tempo_inicial = tempos_list[0]
tempos_list = [t - tempo_inicial for t in tempos_list]

#convertendo para numpy
p1_watts = np.array(p1_watts_list)
p2_watts = np.array(p2_watts_list)
total_watts = np.array(total_watts_list)
tempos = np.array(tempos_list)

#armazenando dados tratados em arquivo txt e matriz para o grafico
matriz_saida = np.column_stack((p1_watts, p2_watts, total_watts, tempos))
np.savetxt(args.arquivoTxtOut, matriz_saida, fmt="%.6f")

#gerando os gráficos
plotarGrafico(matriz_saida)