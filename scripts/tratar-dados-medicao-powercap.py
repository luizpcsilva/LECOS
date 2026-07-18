import argparse
import matplotlib.pyplot as plt
import numpy as np

#configuração dos argumentos passados via terminal
parser = argparse.ArgumentParser(description="")
parser.add_argument("arquivoIn", type=str)
parser.add_argument("arquivoOut", type=str)
args = parser.parse_args()

leitura = []

arquivoIn = open(args.arquivoIn, "r")
arquivoOut = open(args.arquivoOut, "w")

with open(args.arquivoIn, "r") as inputFile:
    linhas = inputFile.readlines()
    linhaAnterior = linhas[0].split()
    tempoMedicao = 0
    tempo = []

    for i in range(1, len(linhas)):
        linha = linhas[i].split()
        
        timestamp = float(linha[1]) - float(linhaAnterior[1])

        deltaEnergia = (float(linha[0]) - float(linhaAnterior[0])) * (10**-6)/timestamp

        #populando matriz para criar graficos depois
        leitura.append([deltaEnergia, timestamp])
        arquivoOut.write(f"{deltaEnergia} {timestamp}\n")
        tempoMedicao += timestamp
        tempo.append(tempoMedicao)



        linhaAnterior = linha


#plotando com matplotlib
dados = np.array(leitura)

delta = dados[:, 0]

plt.figure(figsize=(10, 5))
plt.plot(tempo, delta, linestyle='-', color='blue') # Plota Potência x Segundos Reais

# colocando os rótulos
plt.title("Variação de potência média ao longo do Experimento")
plt.xlabel("Segundos")
plt.ylabel("Potência Média (Watts)")
plt.grid(True)

# Adicionando linhas verticais
plt.axvline(x=10, color='red', linestyle='--', label='Início do Estresse')
plt.axvline(x=70, color='red', linestyle='--', label='Fim do Estresse')

plt.savefig("output/grafico_powercap.png", dpi=300)

arquivoIn.close()