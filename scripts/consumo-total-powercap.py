import argparse
import numpy as np

# configuração dos argumentos passados via terminal
parser = argparse.ArgumentParser(description="")
parser.add_argument("caminhoInput", type=str, help="caminho para o arquivo com dados tratados")
args = parser.parse_args()

dados = np.loadtxt(args.caminhoInput)

#separa coluna da matriz
watts = dados[:, 0]
delta_t = dados[:, 1]

#obtem as colunas em que o computador esteve ativo
tempo_acumulado = np.cumsum(delta_t) 
mascara_estresse = (tempo_acumulado >= 10.0) & (tempo_acumulado <= 70.0)

watts_estresse = watts[mascara_estresse]
delta_t_estresse = delta_t[mascara_estresse]

tempo_total = delta_t_estresse.sum()
energia_total = np.sum(watts_estresse * delta_t_estresse)
potencia_media_total = np.mean(watts_estresse)

print("="*50)
print(" RESULTADOS FINAIS")
print("="*50)
print(f"Tempo Total do Experimento: {tempo_total} segundos")
print(f"Amostras analisadas:        {len(delta_t_estresse)}\n")

print("--- Potência Média (Watts) ---")

print(f"Máquina Total:   {potencia_media_total} W\n")

print("--- Consumo de Energia Total (Joules) ---")
print(f"Máquina Total:   {energia_total} J")
print("="*50)