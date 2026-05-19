import os
import subprocess
import time
import string

OUTPUT_NAME = "teste"
STRESS_FUNC = "stress-ng --matrix 0 -t 1m"
STRESS_FUNC = STRESS_FUNC.split()
TAXA_AMOSTRAGEM = 1

#retorna o valor do contador de microjoule de package como string
def leitor_rapl():
    rapl = open("/sys/class/powercap/intel-rapl/subsystem/intel-rapl:0/energy_uj", "r")
    texto = rapl.readline()
    rapl.close()
    return texto

#cria o arquivo de output
file = open("output/"+OUTPUT_NAME, "w")

# faremos uma medição de 10 segundos, iniciaremos a função do stressng
# por 1 minuto e, após o término, faremos mais 10 segundos de coleta

texto = ""

#10 segundos de testagem sem stress
tempoInicio = time.perf_counter()
tempo = tempoInicio
while (tempo - tempoInicio <= 10): 
    texto += leitor_rapl()
    time.sleep(TAXA_AMOSTRAGEM)
    tempo = time.perf_counter()
    
#inicia stressng
stress = subprocess.Popen(STRESS_FUNC)
while(stress.poll() == None):
    texto += leitor_rapl()
    time.sleep(TAXA_AMOSTRAGEM)
    tempo = time.perf_counter()

#10 segundos de testagem sem stress
tempoInicio = time.perf_counter()
tempo = tempoInicio
while (tempo - tempoInicio <= 10): 
    texto += leitor_rapl()
    time.sleep(TAXA_AMOSTRAGEM)
    tempo = time.perf_counter()

file.write(texto)
file.close()