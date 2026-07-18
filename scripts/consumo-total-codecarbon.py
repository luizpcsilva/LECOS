import csv
import argparse

parser = argparse.ArgumentParser(description="Lê os dados isolados de CPU do CSV gerado pelo CodeCarbon.")
parser.add_argument("arquivo_csv", type=str, help="Caminho para o arquivo CSV do CodeCarbon")
args = parser.parse_args()

try:
    with open(args.arquivo_csv, mode='r', encoding='utf-8') as f:
        leitor = csv.DictReader(f)
        linhas = list(leitor)
        
        if len(linhas) == 0:
            print("o arquivo CSV está vazio.")
            exit(1)
            
        ultima_linha = linhas[-1]

        #extração das variáveis da última linha
        emissoes_kg = float(ultima_linha['emissions'])
        cpu_energy_kwh = float(ultima_linha['cpu_energy'])
        cpu_power_w = float(ultima_linha['cpu_power'])
        duracao_s = float(ultima_linha['duration'])

        #convertendo unidades de medida
        emissoes_g = emissoes_kg * 1000 
        cpu_energy_joules = cpu_energy_kwh * 3_600_000 

        print("="*50)
        print(f" RESULTADOS FINAIS DO CODECARBON (Apenas CPU)")
        print("="*50)
        print(f"Tempo Total do Experimento: {duracao_s} segundos")
        
        print("--- Potência Média (Watts) ---")
        print(f"CPU Isolada:     {cpu_power_w} W\n")
        
        print("--- Consumo de Energia Total (Joules) ---")
        print(f"CPU Isolada:     {cpu_energy_joules} J ({cpu_energy_kwh} kWh)\n")

        print("--- Impacto Ambiental ---")
        print(f"Pegada de Carbono: {emissoes_g} gCO2eq")
        print("="*50)
        
except FileNotFoundError:
    print(f"o arquivo '{args.arquivo_csv}' não foi encontrado")