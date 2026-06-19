
Esta branch contém scripts em Python para realizar a medição de energia do domínio *package* e atribuir o consumo de energia de processos por meio do tempo de cpu, seguindo a metodologia adotada por ferramentas como o Scaphandre.

Assim, a  ferramenta cruza os dados de energia com o tempo de uso de CPU (*ticks* ou *jiffies*) extraídos do sistema operacional, permitindo estimar o consumo em Watts de cada carga de trabalho.

Para garantir o funcionamento adequado dos scripts, o ambiente deve possuir:

* Sistema Operacional Linux.
* Execução dos scripts com sudo
* Suporte ao subsistema `intel-rapl` ativo (`/sys/class/powercap/`).
* Ferramenta `stress-ng` instalada.
* Python 3 com as bibliotecas `matplotlib` e `numpy` instaladas.
* Um diretório chamado `output/` criado na raiz do projeto (onde os scripts estão localizados) para salvar os logs e gráficos gerados.

O fluxo de execução é dividido em dois algoritmos para reduzir o *overhead* durante as medições:

1. **Coleta de Dados Brutos:** Medição do consumo global via Powercap (`intel-rapl`) e do uso de CPU via `/proc/stat` e `/proc/<pid>/stat`. Apenas guardamos os dados "brutos" dos contadores (`energy-profiller-de-processos-cpu-time.py`)
2. **Tratamento e Visualização:** Cálculo dos deltas de tempo/energia, distribuição proporcional do consumo em Watts e geração de gráficos comparativos. (`tratar-dados.py`)

Abaixo, explicaremos a entrada e saída de cada algoritmo

# Arquivo `energy-profiller-de-processos-cpu-time.py`

Este script executa dois processos da biblioteca `stress-ng` simultaneamente. Durante a execução, ele mede periodicamente o contador global de energia e os *ticks* de CPU consumidos por toda a máquina e especificamente pelos processos criados (incluindo seus processos filhos ). O script também adiciona 5 segundos de ociosidade no início e no fim

**Argumentos de Entrada (via terminal):**

| Argumento    | Tipo    | Descrição                                                                               |
| :----------- | :------ | :-------------------------------------------------------------------------------------- |
| `func1`      | String  | Comando para chamar a primeira função do `stress-ng`.                                   |
| `func2`      | String  | Comando para chamar a segunda função do `stress-ng`.                                    |
| `freq`       | Inteiro | Frequência de amostragem das leituras (em segundos).                                    |
| `nomeOutput` | String  | Nome do arquivo de texto onde os resultados brutos serão salvos no diretório `output/`. |

**Saída Gerada:**
Arquivo de texto contendo o log bruto da execução.
* **Formato:** `<energia_acumulada_microjoules> <ticks_Processo1> <ticks_Processo2> <ticks_Total_Maquina> <timestamp_segundos>`

---

# Arquivo`tratar-dados.py`

Este script processa o log gerado na etapa anterior. Ele calcula a potência total dissipada na máquina (em Watts) no intervalo de tempo e, em seguida, utiliza a proporção de *ticks* para estimar quanto desse total pertence ao Processo 1 e ao Processo 2.

**Argumentos de Entrada (via terminal):**

| Argumento | Tipo | Descrição |
| :--- | :--- | :--- |
| `caminhoInput` | String | Caminho para o arquivo de texto contendo os dados brutos gerados pela coleta. |
| `nomeOutput` | String | Nome do arquivo de saída onde os dados já calculados e rateados em Watts serão salvos. |

**Saídas Geradas:**
1. **Arquivo de Texto Tratado:** Contém as potências estimadas de cada processo e o tempo percorrido.
   * **Formato:** `<watts_Processo1> <watts_Processo2> <watts_Total_Maquina> <tempo_medicao_acumulado_segundos>`
2. **Gráficos (Salvos no diretório `output/`):**
   * `grafico_energia_processos1.png`: Gráfico de barras agrupadas (lado a lado) mostrando o consumo de P1 e P2, sobreposto pela linha de consumo total da máquina.
   * `grafico_energia_processos2.png`: Gráfico de barras empilhadas (*stacked*) mostrando a composição somada de P1 e P2 em relação à linha de consumo total.

# Arquivo `calcular-metricas.py`

Este script é responsável por calcular a energia total (em Joules) consumida pelo sistema e por cada processo individualmente.

**Argumentos de Entrada (via terminal):**

| Argumento | Tipo | Descrição |
| :--- | :--- | :--- |
| `caminhoInput` | String | Caminho para o arquivo de texto contendo os dados tratados gerados pelo script `tratar-dados.py`. |

**Saída Gerada:**
Este script não gera novos arquivos. A saída é impressa diretamente no terminal
