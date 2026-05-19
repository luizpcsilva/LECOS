import matplotlib.pyplot as plt

INPUT_PATH = "output/teste"
OUTPUT_PATH = "output/teste-tratado"
TAXA_AMOSTRAGEM = 1

arquivoIn = open(INPUT_PATH, "r")
arquivoOut = open(OUTPUT_PATH, "w")

#conversão dos valores
dados = []
for line in arquivoIn: 
    dados.append(int(line))

delta = []
#calculo do delta de energia, convertendo para watts. note que 1 uj = 0,000001 joules
for i in range(1, len(dados)):
    delta.append((dados[i] - dados[i - 1])*(10**-6))

#plotando com matplotlib

x = range(len(delta))

plt.figure(figsize=(10, 5)) # Deixa o gráfico mais larguinho
plt.plot(x, delta, linestyle='-', color='blue') # Cria a linha

# colocando os rótulos
plt.title("Variação de potência média ao longo do Experimento")
plt.xlabel("Segundos")
plt.ylabel("Potência Média (Watts)")
plt.grid(True) # Adiciona a grade de fundo

# Adicionando linhas verticais
plt.axvline(x=10, color='red', linestyle='--', label='Início do Estresse')
plt.axvline(x=70, color='red', linestyle='--', label='Fim do Estresse')

plt.savefig("output/grafico_energia.png", dpi=300) # Salva em alta resolução

# salvando a potencia média no output
with open(OUTPUT_PATH, "w") as arquivo_out:
    for valor in delta:
        # Escreve o valor convertido para string e pula uma linha
        arquivo_out.write(f"{valor}\n")

arquivoIn.close()