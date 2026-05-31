import argparse
import matplotlib.pyplot as plt
import numpy as np

def plotarGrafico(leitura):
    taxaAmostragem = leitura[0][3]
    dados = np.array(leitura)

    p1_watts = dados[:, 0]
    p2_watts = dados[:, 1]
    total_watts = dados[:, 2]
    tempos = dados[:, 3]

    # Criando a figura e os eixos
    fig, ax = plt.subplots(figsize=(12, 6))

    # 1. Plotando as barras LADO A LADO
    # Diminuímos a largura da barra para caberem duas no mesmo "segundo"
    largura_barra = taxaAmostragem/2

    # Barra do Processo 1 (Deslocada meia largura para a esquerda)
    ax.bar(tempos - largura_barra/2, p1_watts, width=largura_barra, label='Processo 1', color='#1f77b4', alpha=0.8)

    # Barra do Processo 2 (Deslocada meia largura para a direita)
    ax.bar(tempos + largura_barra/2, p2_watts, width=largura_barra, label='Processo 2', color='#ff7f0e', alpha=0.8)

    # 2. Plotando a linha do consumo total (Centralizada no tempo exato)
    ax.plot(tempos, total_watts, label='Gasto Total da Máquina', color='red', linewidth=2, marker='o', markersize=4)

    # 3. Configurações estéticas do gráfico
    ax.set_title('Consumo de Energia: Processos vs Máquina Total', fontsize=14, fontweight='bold')
    ax.set_xlabel('Tempo (Segundos)', fontsize=12)
    ax.set_ylabel('Potência (Watts)', fontsize=12)

    # Adicionando uma grade sutil para facilitar a leitura
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    # Mostrando a legenda no canto superior direito
    ax.legend(loc='upper right')

    # Ajustando as margens para não cortar nenhum rótulo
    plt.tight_layout()

    plt.savefig('grafico_energia_processos.png', dpi=300)

#configuração dos argumentos passados via terminal
parser = argparse.ArgumentParser(description="")
parser.add_argument("caminhoInput", type=str, help="caminho para o arquivo com dados brutos")
parser.add_argument("nomeOutput", type=str, help="nome para o arquivo de saida com os dados tratados")
args = parser.parse_args()

outputFile = open(args.nomeOutput, "w")
leitura= []
tempoMediçao = 0

with open(args.caminhoInput, "r") as inputFile:
    linhas = inputFile.readlines()
    linhaAnterior = linhas[0].split()
    
    for i in range(1, len(linhas)):
        linha = linhas[i].split()
        wP1, wP2 = 0, 0

        timestamp = float(linha[4]) - float(linhaAnterior[4])
        tempoMediçao += timestamp
        wTotal = ((float(linha[0]) - float(linhaAnterior[0])) *(10**-6)) /timestamp
        
        if(int(linhaAnterior[3]) != 0 and int(linha[3]) != 0):
            tickTotal = float(linha[3]) - float(linhaAnterior[3]) 
            tickP1 = float(linha[1]) - float(linhaAnterior[1])
            tickP2 = float(linha[2]) - float(linhaAnterior[2])

            #calcula o consumo em watts de P1 e P2 com uma proporção entre tickP e wTotal
            wP1 = (tickP1 * wTotal)/tickTotal
            wP2 = (tickP2 * wTotal)/tickTotal

        #populando matriz para criar graficos depois
        leitura.append([wP1, wP2, wTotal, tempoMediçao])
        outputFile.write(f"{wP1} {wP2} {wTotal} {tempoMediçao} \n")

        linhaAnterior = linha

plotarGrafico(leitura)
outputFile.close()
        
