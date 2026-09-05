import time
import argparse
import csv
from datetime import datetime
import subprocess

#configuração dos argumentos passados via terminal
parser = argparse.ArgumentParser(description="")
parser.add_argument("freq", type=float, help="frequencia da amostragem do rapl (em segundos)")
parser.add_argument("estressor", type=str, help="estressor alvo para se medir o consumo")

args = parser.parse_args()
nome_estressor = args.estressor
args.estressor = args.estressor.split()

output = []

def leitorRapl():
    with open("/sys/class/powercap/intel-rapl/subsystem/intel-rapl:0/energy_uj", "r") as rapl:
        valor = rapl.readline().strip()
        return valor
    
#--------------------- Inicio Medição ----------------------
processo_estressor = subprocess.Popen(args.estressor, stdout=subprocess.DEVNULL)
while(processo_estressor.poll() == None):
    leitura = [0] * 2

    leitura[0] = leitorRapl()
    leitura[1] = time.perf_counter()

    output.append(leitura)
    time.sleep(args.freq)
#--------------------- Fim Medição -------------------------

#criando output em csv do experimento
nome_csv = nome_estressor + datetime.now().strftime('%Y%m%d_%H%M%S') + ".csv"
caminho_csv = "testes/estressores/" + nome_csv
with open(caminho_csv, mode="w") as arquivo_csv:
    escritor = csv.writer(arquivo_csv)
    escritor.writerow(["energia_uj", "timestamp_s"])
    escritor.writerows(output)

#calcula a melhor media da medicao com pandas(intervalo de 10 segundos com menor desvio padrao)
resultado = subprocess.run(
    ["venv/bin/python", "scripts/calculo-melhor-media-e-std.py", nome_csv, caminho_csv],
    capture_output=True,
    text=True
)

print(resultado.stdout)
print(resultado.stderr)