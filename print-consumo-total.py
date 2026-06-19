import argparse
import numpy as np

# configuração dos argumentos passados via terminal
parser = argparse.ArgumentParser(description="")
parser.add_argument("caminhoInput", type=str, help="caminho para o arquivo com dados tratados")
args = parser.parse_args()

dados = np.loadtxt(args.caminhoInput)

# 2. Separa as colunas da matriz
p1_watts = dados[:, 0]
p2_watts = dados[:, 1]
total_watts = dados[:, 2]
tempos = dados[:, 3]

#calcula o delta tempo das mediçoes. prepend=0 garante que a primeira linha use o tempo dela mesma.
delta_t = np.diff(tempos, prepend=0)

#cria valores booleanos para isolar os momentos em que os processos estavam ativos
ativos_p1 = p1_watts > 0
ativos_p2 = p2_watts > 0

tempo_total = tempos[-1]
tempo_ativo_p1 = np.sum(delta_t[ativos_p1])
tempo_ativo_p2 = np.sum(delta_t[ativos_p2])

energia_p1 = np.sum(p1_watts * delta_t)
energia_p2 = np.sum(p2_watts * delta_t)
energia_total = np.sum(total_watts * delta_t)

potencia_media_p1 = np.mean(p1_watts[ativos_p1])
potencia_media_p2 = np.mean(p2_watts[ativos_p2])
potencia_media_total = np.mean(total_watts)

print("="*50)
print(" RESULTADOS FINAIS DO PROFILING DE ENERGIA")
print("="*50)
print(f"Tempo Total do Experimento: {tempo_total} segundos")
print(f"Amostras analisadas:        {len(dados)}\n")

print("--- Tempo Ativo  ---")
print(f"Processo 1:      {tempo_ativo_p1} s")
print(f"Processo 2:      {tempo_ativo_p2} s\n")

print("--- Potência Média (Watts) ---")
print(f"Processo 1:      {potencia_media_p1} W")
print(f"Processo 2:      {potencia_media_p2} W")
print(f"Máquina Total:   {potencia_media_total} W\n")

print("--- Consumo de Energia Total (Joules) ---")
print(f"Processo 1:      {energia_p1} J")
print(f"Processo 2:      {energia_p2} J")
print(f"Máquina Total:   {energia_total} J")
print("="*50)