import os
import subprocess
import time
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

#--------------------- Inicio Medição ----------------------

with OfflineEmissionsTracker(country_iso_code="BRA", measure_power_secs=args.freq, output_dir=".", output_file=args.caminhoOutput, log_level="error") as tracker:
    #inicia stressng
    stress = subprocess.Popen(args.func1)
    while(stress.poll() == None):
        time.sleep(args.freq)