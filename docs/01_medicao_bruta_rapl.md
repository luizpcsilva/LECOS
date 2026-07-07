# Medição de Energia via RAPL

A interface RAPL (Running Average Power Limit) é a referência para estimar o consumo de energia de processadores. A forma mais básica para acessar seus contadores de energia é por meio dos MSRs (Model Specific Registers). Trata-se de registradores de 32 ou 64 bits que são atualizados aproximadamente a cada 1 ms.

## Acesso via MSR
Abaixo, descrevemos um trecho de código que realiza o acesso direto a esses registradores via instruções RDMSR.

*TODO: CÓDIGO E DIFICULDADES*

## Acesso via Powercap
Em ambientes Linux é possível utilizar o **Powercap** (`sysfs powercap`). O Powercap é um framework do sistema operacional que provê uma interface de acesso no espaço de usuário via sistema de arquivos virtuais sysfs, organizando os componentes de forma hierárquica em diretórios. 

Utilize o comando abaixo no terminal para verificar se o powercap está disponível no seu sistema:
```bash
ls /sys/class/powercap/
```
Se aparecer um diretório chamado intel-rapl:0 ou semelhante, então está tudo certo. Caso contrário, tente carregar o driver com o comando abaixo e repita o comando acima.
```bash
sudo modprobe intel_rapl
```
Com o powercap funcionando corretamente, podemos realizar a leitura do contador de energia do domínio de energia package no arquivo `energy_uj`  localizado em `intel-rapl:0` via cat.
```bash
sudo cat /sys/class/powercap/intel-rapl:0/energy_uj
```
O número devolvido representa a energia acumulada em microjoules desde que o computador foi ligado. Utilizar o framework Powercap torna a medição de energia muito mais simples quando comparada com a leitura direta via instruções RDMSR, já que o trabalho complexo de mais baixo nível foi delegado ao Kernel do sistema operacional.

Ler o arquivo manualmente via terminal é interessante, mas, para automatizar esse processo, podemos delegar esse trabalho para um algoritmo. Em `scripts/leitor-rapl.py` preparamos um script que realiza medição de energia durante a execução de um programa de teste para estressar a CPU. Abaixo, iremos passar pelos elementos centrais desse código.

A função `leitorRapl()` realiza uma leitura de energia via Powercap em Python.
```python
#retorna o valor do contador de microjoule de package como string
def leitorRapl():
    with open("/sys/class/powercap/intel-rapl/subsystem/intel-rapl:0/energy_uj", "r") as rapl:
        valor = rapl.readline().strip()
        return valor
```

Entretanto, para monitorarmos uma aplicação computacional, precisamos de amostragem contínua por meio de um laço de repetição.
A função `loopLeitorRapl()` realiza a leitura do consumo de energia do package continuamente com frequência e duração definidas e armazena os resultados em um array `output`.
```python
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
```
