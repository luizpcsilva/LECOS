import time
import argparse
import csv
from datetime import datetime
import subprocess

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

#criando output em csv do experimento
nome_csv = "idle_" + datetime.now().strftime('%Y%m%d_%H%M%S') + ".csv"
caminho_csv = "testes/idle/" + nome_csv
with open(caminho_csv, mode="w") as arquivo_csv:
    escritor = csv.writer(arquivo_csv)
    escritor.writerow(["energia_uj", "timestamp_s"])
    escritor.writerows(output)

resultado = subprocess.run(
    ["venv/bin/python", "scripts/calculo-melhor-media-e-std.py", nome_csv, caminho_csv],
    capture_output=True,
    text=True
)

print(resultado.stdout)
print(resultado.stderr)