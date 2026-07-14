import os
import subprocess
import time
import string
import argparse

#configuração dos argumentos passados via terminal
parser = argparse.ArgumentParser(description="")
parser.add_argument("func", type=str, help="codigo para chamar função do stress ng")
parser.add_argument("freq", type=float, help="frequencia da amostragem do rapl (em segundos)")
parser.add_argument("caminhoOutput", type=str, help="nome do arquivo para salvar resultados")
args = parser.parse_args()
args.caminhoOutput += "-sem-codecarbon"

args.func = args.func.split()

output = []
QTD_INSTANCIAS_ESTRESSOR = 50
estressores = []

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

def algum_processo_ativo(lista_processos):
    for p in lista_processos:
        if p.poll() is None:
            return True
    return False

#--------------------- Inicio Medição ----------------------

#10 segundos de testagem sem estresse
loopLeitorRapl(10, output)

#inicia estressores
for i in range(QTD_INSTANCIAS_ESTRESSOR):
    processo = subprocess.Popen(args.func)
    estressores.append(processo)

while(algum_processo_ativo(estressores)):
    leitura = [0] * 2

    leitura[0] = leitorRapl()
    leitura[1] = time.perf_counter()

    output.append(leitura)
    time.sleep(args.freq)
    

#10 segundos de testagem sem stress
loopLeitorRapl(10, output)

#--------------------- Fim Medição -------------------------

#salva cada elemento em um arquivo de texto
with open("output/"+args.caminhoOutput, "w") as fileOutput:
    for linha in output:
        for elem in linha:  
            fileOutput.write(str(elem) + " ")
        fileOutput.write("\n")