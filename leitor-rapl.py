import os
import subprocess
import time
import string
import argparse
#cria contador para codecarbon
from codecarbon import OfflineEmissionsTracker


#configuração dos argumentos passados via terminal
parser = argparse.ArgumentParser(description="")
parser.add_argument("func1", type=str, help="codigo para chamar função 1 do stress ng")
parser.add_argument("freq", type=float, help="frequencia da amostragem do rapl (em segundos)")
parser.add_argument("caminhoOutput", type=str, help="nome do arquivo para salvar resultados")
args = parser.parse_args()

args.func1 = args.func1.split()

output = []


#retorna o valor do contador de microjoule de package como string
def leitorRapl():
    with open("/sys/class/powercap/intel-rapl/subsystem/intel-rapl:0/energy_uj", "r") as rapl:
        valor = rapl.readline().strip()
        return valor
    
def loopLeitorRapl(duracao, output, freq=args.freq): 
    tempoInicio = time.perf_counter()
    tempo = tempoInicio
    while (tempo - tempoInicio <= duracao): 
        leitura = [0] * 2

        leitura[0] = leitorRapl()
        leitura[1] = tempo
        time.sleep(args.freq)
        tempo = time.perf_counter()

        output.append(leitura)


#cria o arquivo de output
file = open("output/"+args.caminhoOutput, "w")

#--------------------- Inicio Medição ----------------------
 #10 segundos de testagem sem stress
loopLeitorRapl(10, output)

with OfflineEmissionsTracker(country_iso_code="BRA", measure_power_secs=args.freq, output_dir="output/", output_file=f"{args.nomeOutput}-codecarbon", log_level="error") as tracker:
    #inicia stressng
    stress = subprocess.Popen(args.func)
    while(stress.poll() == None):
        leitura = [0] * 2

        leitura[0] = leitorRapl()
        leitura[1] = time.perf_counter()

        output.append(leitura)
        time.sleep(args.freq)
        
#10 segundos de testagem sem stress
loopLeitorRapl(10, output)
#--------------------- Fim Medição -------------------------

#salva cada elemento em um arquivo de texto
with open("output/"+args.nomeOutput, "w") as fileOutput:
    for linha in output:
        for elem in linha:  
            fileOutput.write(str(elem) + " ")
        fileOutput.write("\n")