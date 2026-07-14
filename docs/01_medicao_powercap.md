# Medição de Energia via RAPL

A interface RAPL (Running Average Power Limit) é a referência para estimar o consumo de energia de processadores. A forma mais básica para acessar seus contadores de energia é por meio dos MSRs (Model Specific Registers). Trata-se de registradores de 32 ou 64 bits que são atualizados aproximadamente a cada 1 ms.

Em ambientes Linux é possível utilizar o **Powercap** (`sysfs powercap`). O Powercap é um framework do sistema operacional que provê uma interface de acesso no espaço de usuário via sistema de arquivos virtuais sysfs, organizando os componentes de forma hierárquica em diretórios. 

Utilize o comando abaixo no terminal para verificar se o powercap está disponível no seu sistema:
```bash
ls /sys/class/powercap/
```
Se aparecer um diretório chamado intel-rapl:0 ou semelhante, então está tudo certo. Caso contrário, tente carregar o driver com o comando abaixo e repita o comando acima.
```bash
sudo modprobe intel_rapl
```
Com o powercap funcionando corretamente, podemos realizar a leitura do contador de energia do domínio principal (`package`) no arquivo `energy_uj` localizado em `intel-rapl:0` via cat.
```bash
sudo cat /sys/class/powercap/intel-rapl:0/energy_uj
```
O número devolvido representa a energia acumulada em microjoules desde que o computador foi ligado. Utilizar o framework Powercap torna a medição de energia muito mais simples quando comparada com a leitura direta via instruções RDMSR, já que o trabalho complexo de mais baixo nível foi delegado ao Kernel do sistema operacional.

Ler o arquivo manualmente via terminal é interessante, mas, para automatizar esse processo, podemos delegar esse trabalho para um algoritmo. Em `scripts/leitor-powercap.py` preparamos um script que realiza a medição de energia. Abaixo, detalhamos os elementos centrais do código.

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
Para aumentarmos o gasto de energia durante a medição, utilizaremos um script de multiplicação de matrizes 512x512 da ferramenta open-source `stress-ng`, escrita em C. A ferramenta é especializada em gerar cargas de estresse na máquina.

Abaixo, podemos visualizar uma versão simplificada do algoritmo. O código original do algoritmo de estresse pode ser visualizado no [repositório oficial da ferramenta](https://github.com/ColinIanKing/stress-ng/blob/master/stress-matrix.c#L69)

```c
//versão simplificada da multiplicação de matrizes do stress-ng
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define N 512 

double a[N][N];
double b[N][N];
double r[N][N];

void inicializar_matrizes() {
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            a[i][j] = (double)(rand() % 100) / 10.0;
            b[i][j] = (double)(rand() % 100) / 10.0;
            r[i][j] = 0.0;
        }
    }
}

void multiplicar_matrizes() {
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            for (int k = 0; k < N; k++) {
                r[i][j] += a[i][k] * b[k][j];
            }
        }
    }
}

int main(int argc, char *argv[]) {
    int tempo_limite = atoi(argv[1]);
    inicializar_matrizes();

    time_t inicio = time(NULL);

    while (time(NULL) - inicio < tempo_limite) {
        multiplicar_matrizes();
    }

    return 0;
}
```

A ferramenta `stress-ng` criará uma instância do estressor para cada núcleo do processador. Enquanto isso, as funções `leitorRapl()` e `loopLeitorRapl()` registram o consumo de energia da máquina antes, durante e depois da carga de estresse em uma matriz e, posteriormente, em um arquivo de texto.

Siga os passos abaixo para executar a medição no seu ambiente:

**1. Instale a ferramenta stress-ng**.
```bash
sudo apt install stress-ng
```

**2. Execute o script de medição `leitor-powercap.py`:**
```bash
sudo python3 scripts/leitor-powercap.py "stress-ng --matrix 0 --matrix-method prod --matrix-size 512 -t 1m" 1 teste-powercap.txt
```

Entenda o que cada argumento acima significa:
- `"stress-ng --matrix 0 --matrix-method prod --matrix-size 512 -t 1m"`: É a string que contém a chamada da função estressora.
- `1`: É a frequência de amostragem. Define que o Python vai ler os contadores de energia Powercap de 1 em 1 segundo.
- `teste-powercap.txt`: É o nome do arquivo onde os dados brutos (microjoules e timestamps) serão gravados.

Ao fim da execução do programa (aproximadamente 80 segundos), abra o arquivo com os dados coletados na raiz do repositório via explorador de arquivos ou via terminal com o comando:
```bash
cat teste-powercap.txt
```
Você verá diversos números na tela, como, por exemplo:
```
99981016814 1646987.469997645 
100036646188 1646988.470136542 
100092236011 1646989.470343441
...
```
Cada linha é uma medição de energia realizada via Powercap. A primeira coluna representa o valor do contador de energia consultado naquele instante (em microjoules). Já a segunda coluna armazena o valor do contador de tempo (relógio) no momento da medição.

Avaliar o consumo de energia da máquina com essas amostras de dados não é amigável. Na próxima etapa, mostraremos como tratar esses dados e gerar um gráfico com a variação da potência da máquina ao longo do tempo.

[Voltar ao Menu Inicial](../README.md) | [Próximo Passo: Tratamento e Visualização de Dados](02_tratamento_de_dados.md)