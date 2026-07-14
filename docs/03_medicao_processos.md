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

### Automatizando a Leitura
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
# Executando o Script de Medição

O script `scipts/energy-profiller-de-processos-cpu-time.py` realiza a medição da potência da máquina e métricas da CPU de dois processos diferentes, considerando também os processos filhos que podem ser criados por eles.

Abaixo, detalharemos a escolha dos algoritmos de estresse que utilizaremos para medir o consumo de energia

## Algoritmos de Estresse Utilizados

Ao invés de executar dois processos idênticos concorrentemente, vamos utilizar dois algoritmos de natureza diferentes para a medição de energia. Utilizaremos a ferramenta `stress-ng`.

* Processo 1: Multiplicação de Matrizes (`--matrix-method prod`), definida e utilizada nas etapas anteriores do minicurso.
* Processo 2: O cálculo contínuo da sequência de Fibonnaci (`--cpu-method fibonacci`). 

Abaixo, podemos visualizar uma versão simplificada do algoritmo de estresse de Fibonacci utilizado pela ferramenta `stress-ng`:
```c
void calcular_fibonacci() {
    uint64_t f1 = 0;
    uint64_t f2 = 1;
    uint64_t proximo;

    //Um laço de repetição que termina apenas ao acabar a duração do script informada.
    while (executando) {
        proximo = f1 + f2;
        f1 = f2;
        f2 = proximo;
    }
}
```

O código original do algoritmo de estresse de fibonacci do `stress-ng` pode ser visualizado no [repositório oficial da ferramenta](https://github.com/ColinIanKing/stress-ng/blob/master/stress-cpu.c#L1383).

## Loop de Medição Principal

Por fim, utilizaremos a função`leitor_ticks` para obter as métricas de tempo de CPU, `leitor_rapl` e `loop_leitor_RAPL`, definidas nas etapas anteriores, para obter o consumo de energia do processador e os dois algoritmos de estresse da ferramenta `stress-ng` (P1 e P2) como objeto de estudo.

O nosso script Python inicia o stress-ng e entra num laço de repetição (while). A cada iteração (controlada pela frequência de amostragem escolhida), ele constrói um vetor com os 5 dados fundamentais e o armazena em uma matriz. Ao fim da medição, armazenamos os elementos da matriz em um arquivo de texto.

Abaixo, podemos visualizar o loop principal do código de forma simplificada:
```python
#5 segundos de testagem inicial sem algoritmo de estresse
loopLeitorRapl(5, output)

#aqui é feita a inicialização dos processos de estresse

# enquanto os dois processos de estresse não tiverem terminado
while(stress1.poll() == None or stress2.poll() == None):
    leitura = [0] * 5

    leitura[0] = leitorRapl()              # 1. Contador de energia do processador (Powercap)
    leitura[1] = leitor_ticks(listaP1)     # 2. ticks acumulados do processo 1 (+ filhos)
    leitura[2] = leitor_ticks(listaP2)     # 3. ticks acumulados do processo 2 (+ filhos)
    leitura[3] = leitor_ticks()            # 4. Ticks ativos totais executados pela CPU
    leitura[4] = time.perf_counter()       # 5. Tempo da medição (timestamp)
    
    time.sleep(args.freq)
    output.append(leitura)

#5 segundos de testagem final sem algoritmo de estresse
loopLeitorRapl(5, output)
```

## Execute o Experimento!

Vamos programar para o Processo 1 (Multiplicação de Matrizes) durar 30 segundos e o Processo 2 (Fibonacci) durar 60 segundos. O stress-ng instanciará um subprocesso de cada tipo para cada núcleo do processador.

Siga os passos abaixo:
1. **Ative o ambiente virtual**:
Na raiz do repositório, digite:
```bash
source venv/bin/activate
``` 
2. Execute o comando abaixo:
```bash
#Sintaxe: python3 script.py <chamada_estressor 1> <chamada_estressor 2> <frequência de amostragem> <nome_arquivo_saida>
sudo python3 scripts/medicao-processos.py "stress-ng --matrix 0 --matrix-method prod -t 30s" "stress-ng --cpu 0 --cpu-method fibonacci -t 60s" 1 teste_processos.txt
```

O script será executado em aproximadamente 80 segundos. Ao fim do experimento , será gerado o arquivo `teste-processos.txt`. Imprima seu conteúdo com o seguinte comando no terminal:
```bash
cat teste-processos.txt
```
Diversas linhas e colunas serão impressos na tela:
```
...
142688331128 0 0 0 352466.701894422 
142691023442 0 0 0 352467.702212871 
142726054908 321 295 1329572 352469.242651642 
142787453066 930 879 1330772 352470.243246248 
...
```
Conforme definimos no [Loop Principal](#loop-de-medição-principal), cada linha representa uma medição realizada e cada coluna armazena um contador específico. As colunas possuem o seguinte significado:

* Coluna 1: Energia do processador (Powercap).
* Coluna 2: Ticks acumulados do processo 1 (+ filhos).
* Coluna 3: Ticks acumulados do processo 2 (+ filhos).
* Coluna 4: Ticks ativos totais executados pela CPU
* Coluna 5: Tempo da medição (timestamp)

Note que a coluna 2, 3 e 4 estão zeradas em algumas medições. Isso ocorre durante a leitura da função `loop_leitor_RAPL`, pois, nesse momento, não há algoritmo de estresse sendo executado pela CPU.

No próximo passo, utilizaremos os contadores acima para calcular o Delta entre as medições e fatiar o consumo de energia entre os dois algoritmos estressores.

---
## Navegação
[⬅️ Passo Anterior: Tratamento de Dados da Medição Total da Máquina](02_tratamento_de_dados_1.md) | [➡️ Passo Seguinte: Tratamento de Dados da Medição de Processos Concorrentes](04_tratamento_de_dados_2.md)

# Referências
[^1]: JAY, Mathilde et al. An experimental comparison of software-based power meters: focus on CPU and GPU. In: 2023 IEEE/ACM 23rd International Symposium on Cluster, Cloud and Internet Computing (CCGrid). IEEE, 2023. p. 106-118.
