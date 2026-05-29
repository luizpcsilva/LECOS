import os
import subprocess
import time
import string
import argparse

#configuração dos argumentos passados via terminal
parser = argparse.ArgumentParser(description="")
parser.add_argument("func1", type=str, help="codigo para chamar função 2 do stress ng")
parser.add_argument("func2", type=str, help="codigo para chamar função 2 do stress ng")
parser.add_argument("freq", type=int, help="frequencia da amostragem do rapl (em segundos)")
parser.add_argument("nomeOutput", type=str, help="nome do arquivo para salvar resultados")
args = parser.parse_args()

args.func1 = args.func1.split()
args.func2 = args.func2.split()


TICK_POR_SEGUNDO = os.sysconf("SC_CLK_TCK")
output = []

def leitor_ticks(pid=-1):
    #se nao for passado nenhum pid, retorna os jiffies decorridos no intervalo 
    if pid == -1:
        with open("/proc/stat", "r") as file:
            text = file.readline().split()

            #soma todas as colunas da primeira linha, com exceção da primeira que contém uma string
            valor = 0
            for i in range (1, len(text)):
                valor += int(text[i])
            return valor
    
    # se for passado um pid
    else:
        with open("/proc/"+str(pid)+"/stat", "r") as file:
            text = file.readline().split()
            valor = int(text[13]) + int(text[14])
            return valor




def leitorRapl():
    with open("/sys/class/powercap/intel-rapl/subsystem/intel-rapl:0/energy_uj", "r") as rapl:
        valor = rapl.readline().strip()
        return valor
    
def loopLeitorRapl(duracao, output, freq=args.freq): 
    tempoInicio = time.perf_counter()
    tempo = tempoInicio
    while (tempo - tempoInicio <= duracao): 
        leitura = [0] * 5

        leitura[0] = leitorRapl()
        leitura[4] = tempo
        time.sleep(args.freq)
        tempo = time.perf_counter()

        output.append(leitura)



#--------------------- Inicio Medição ----------------------

#5 segundos de testagem sem stressng
loopLeitorRapl(5, output)

#inicializando os dois processos
tempoAnterior = time.perf_counter()
stress1 = subprocess.Popen(args.func1)
stress2 = subprocess.Popen(args.func2)
print(stress1.pid)
print(stress2.pid)


#iniciando medição
while(stress1.poll() == None or stress2.poll() == None):
    leitura = [0] * 5

    leitura[0] = leitorRapl()              #lê o gasto total da máquina
    leitura[1] = leitor_ticks(stress1.pid) #lê os ticks executados até o momento da funçao 1
    leitura[2] = leitor_ticks(stress2.pid) #lê os ticks executados até o momento da funçao 2
    leitura[3] = leitor_ticks()            #lê os ticks executados até o momento pelo processador
    leitura[4] = time.perf_counter()
    time.sleep(args.freq)

    output.append(leitura)
    
#5 segundos de testagem sem stressng
loopLeitorRapl(5, output)

#--------------------- Fim Medição -------------------------

#salva cada elemento em um arquivo de texto
with open("output/"+args.nomeOutput, "w") as fileOutput:
    for linha in output:
        for elem in linha:  
            fileOutput.write(str(elem) + " ")
        fileOutput.write("\n")
            

