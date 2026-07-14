import os
import subprocess
import time
import string
import argparse

#configuração dos argumentos passados via terminal
parser = argparse.ArgumentParser(description="")
parser.add_argument("func1", type=str, help="codigo para chamar função 2 do stress ng")
parser.add_argument("func2", type=str, help="codigo para chamar função 2 do stress ng")
parser.add_argument("nomeOutput", type=str, help="nome do arquivo para salvar resultados")
args = parser.parse_args()

args.func1 = args.func1.split()
args.func2 = args.func2.split()

cmd_scaphandre = [
    "sudo", "docker", "run", "--rm", "--name", "meu_scaphandre", "--privileged",
    "-v", "/sys/class/powercap:/sys/class/powercap",
    "-v", "/proc:/proc",
    "-v", f"{os.getcwd()}:/dados",
    "hubblo/scaphandre",
    "json", "-f", "/dados/scaphandre_saida.json", "-s", "1", "--process-regex", "stress-ng"
]
#--------------------- Inicio Medição ----------------------
processo_scaphandre = subprocess.Popen(cmd_scaphandre, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2)

#inicializando os dois processos
stress1 = subprocess.Popen(args.func1)
stress2 = subprocess.Popen(args.func2)
print(stress1.pid)
print(stress2.pid)

#coletando todos os processos filhos que podem ter sido criados
time.sleep(0.5)
listaP1 = (subprocess.run(["pgrep", "-P", str(stress1.pid)], capture_output=True, text=True)).stdout.split()
listaP1.append(stress1.pid)
print(listaP1)
listaP2 = (subprocess.run(["pgrep", "-P", str(stress2.pid)], capture_output=True, text=True)).stdout.split()
listaP2.append(stress2.pid)
print(listaP2)

#espera o processo acabar
stress1.wait()
stress2.wait()

subprocess.run(["sudo", "docker", "stop", "meu_scaphandre"], stdout=subprocess.DEVNULL)
#--------------------- Fim Medição -------------------------
