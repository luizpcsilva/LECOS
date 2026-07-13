O desafio agora é: como fatiar a energia total extraída dos contadores RAPL da CPU quando vários processos estão sendo executados concorrentemente?

Segundo [^1], existem dois métodos principais de modelagem do consumo de energia dos processos: **Baseadas Em Uso de CPU** e **Baseadas em Regressão Com Eventos de Performance**. Nessa etapa, utilizaremos a metodologia da Modelagem Baseada em Uso de CPU, implementada pela ferramenta Scaphandre e, para fins didáticos, iremos monitorar apenas dois processos em execução.

Para calcular o consumo de energia das aplicações, o Scaphandre coleta continuamente dados dos sensores de hardware e os associa ao tempo de CPU dessas aplicações. A premissa é simples: se dois processos estão dividindo a CPU, o processo que manteve os núcleos ocupados por mais tempo leva a maior fatia da conta de energia.

Assim, para fatiar o consumo em um intervalo, nós utilizamos a seguinte fórmula matemática de proporção:

$$P_{Processo} = P_{Total} \times \left( \frac{\Delta TempoCPU_{Processo}}{\Delta TempoCPU_{Total}} \right)$$
Sendo P = Potência (em Watts)

Abaixo, iremos detalhar as etapas para obtermos o Tempo de CPU total e de processos em ambiente Linux.   

## Tempo de CPU

No Linux, o Kernel armazena o tempo exato em ticks que um processo passa sendo executado. Um Tick equivale normalmente a 10ms, porém, esse valor pode variar de sistema para sistema.

Execute o comando abaixo no terminal para obter quantos ticks são executados em um segundo no seu sistema (padrão 100 na maioria dos sistemas):
```bash
getconf CLK_TCK
```

### Tempo de CPU de processos

Para obter quantos ticks um processo específico consumiu desde sua criação, precisamos acessar o sistema de arquivos virtuais do Kernel Linux (`/proc`). Siga os passos abaixo: 

1. Abra o programa `Processos` ou utilize o comando `htop` em uma nova aba do terminal
2. Escolha um número do processo (PID) de uma aplicação que esteja executando (o seu navegador da internet, por exemplo). 
3. Em seguida, execute o comando abaixo, substituindo o {pid} pelo ID escolhido no passo acima ou então acesse o arquivo pelo Explorador de Arquivos:
```bash
cat /proc/{pid}/stat
```
O comando irá devolver uma saída contendo uma longa linha de texto e números, por exemplo:
```
16664 (firefox) S 5881 5881 5881 0 -1 4194560 3156113 22913 181 0 96298 30985 13 15 20 0 132 0 9611244 21714771968 232134 18446744073709551615 106241808391664 106241808852656 140732873936992 0 0 0 0 4096 85759 0 0 0 17 11 0 0 0 0 0 106241808866848 106241808869424 106242551881728 140732873945794 140732873945837 140732873945837 140732873953229 0
``` 
Nesse sentido, cada coluna contém uma métrica específica do processo. No contexto atual, estamos interessados em duas colunas:
* Coluna 14(`utime`): Contém o tempo de CPU do processo gasto em **modo Usuário**.
* Coluna 15(`stime`): Contém o tempo de CPU do processo gasto em **modo Kernel**.
Ao somar as duas colunas, obtemos o tempo total de CPU (em ticks) que o processo utilizou desde que foi inicializado. Mais detalhes sobre o arquivo `/proc/{pid}/stat` podem ser lidos na [documentação oficial do Kernel Linux](https://docs.kernel.org/filesystems/proc.html)

### Total de Ticks Executados

Entretanto, para fatiarmos a energia, além do tempo de CPU de cada processo, precisamos saber a quantidade de ticks totais executados por todos os núcleos da máquina até o momento. Para isso, precisamos acessar o arquivo `/proc/stat`. 

Execute o comando abaixo no terminal ou acesse via Explorador de Arquivos:
```bash
cat /proc/stat
```
O comando irá retornar uma enorme sequência de contadores da cpu, por exemplo:
```
cpu  733877 3812 277616 34179998 19424 0 43281 0 0 0
cpu0 46483 258 16687 2125623 1651 0 23093 0 0 0
cpu1 20687 75 8739 2168898 881 0 3449 0 0 0
...
```
Estamos interessados na primeira linha da saída (`cpu`). Ela agrupa o esforço de todos os núcleos. Para obter o total de ticks ativos, somamos as seguintes colunas:

* Coluna 2: Processos executando em user mode.
* Coluna 3: Processos com nice executando em user mode.
* Coluna 4: Processos executando em kernel mode.
* Coluna 10: Ticks de execução em sessão de convidado.
* Coluna 11: Tempo de execução em sessão de convidado com nice.

As colunas descartadas fornecem métricas de tempo em que a CPU não esteve ativa (como `idle` e `iowait`), logo, não devem ser consideradas para o fatiamento de energia. Mais informações sobre o arquivo `/proc/stat` podem ser lidas na [documentação oficial do Kernel Linux](https://man7.org/linux/man-pages/man5/proc_pid_stat.5.html).

### Código Python

Note que uma aplicação pode conter diversos processos filhos e os dados de cada PID devem ser agregados. A função abaixo automatiza toda a coleta de dados referente ao tempo de CPU. 

A entrada é uma lista de PIDs. Caso a lista esteja vazia, retorna o somatório das métricas relevantes da cpu (`/proc/stat`). Caso a lista contenha PIDs, então retorna o somatório de todas as métricas relevantes de cada processo (`proc/{pid}/stat`).

```python
def leitor_ticks(pids=[]):
    #se nao for passado nenhum pid, retorna os ticks ativos totais da CPU 
    if len(pids) == 0:
        with open("/proc/stat", "r") as file:
            text = file.readline().split()
            #soma todas as colunas da primeira linha, com exceção da primeira (string), iowait, idle, irq e softirq 
            valor = int(text[1]) + int(text[2]) + int(text[3]) + int(text[9]) + int(text[10]) 
            return valor
    
    # se for passado uma lista de pids
    else:
        cont = 0
        for pid in pids:
            try:
                with open("/proc/"+str(pid)+"/stat", "r") as file:
                    text = file.readline().split()
                    cont += int(text[13]) + int(text[14])
            except FileNotFoundError:
                # o processo já não existe mais, podemos apenas ignorar
                pass
        return cont
```

O script `scipts/energy-profiller-de-processos-cpu-time.py` utiliza a função `leitor_ticks` para obter as métricas de tempo de CPU e `leitor_rapl`/`loop_leitor_RAPL`, definidas nas etapas anteriores, para obter o consumo de energia do processador.

Abaixo, podemos visualizar o loop principal
Para estressar o sistema, utilizaremos dois métodos da ferramenta `stress-ng`. São eles:
1. Multiplicação de Matrizes (código descrito em em [01_medicao_bruta_rapl.md]).
2. Cálculo da Sequência da Fibonacci. Segue uma versão simplificada do algoritmo de estresse do `stress-ng`:
```c
void calcular_fibonacci() {
    uint64_t f1 = 0;
    uint64_t f2 = 1;
    uint64_t proximo;

    while (executando) {
        proximo = f1 + f2;
        f1 = f2;
        f2 = proximo;
    }
}
```
O código original do algoritmo de estresse de fibonacci do `stress-ng` pode ser visualizado no [repositório oficial da ferramenta](https://github.com/ColinIanKing/stress-ng/blob/master/stress-cpu.c#L1383).


# Referências
[^1]: JAY, Mathilde et al. An experimental comparison of software-based power meters: focus on CPU and GPU. In: 2023 IEEE/ACM 23rd International Symposium on Cluster, Cloud and Internet Computing (CCGrid). IEEE, 2023. p. 106-118.
