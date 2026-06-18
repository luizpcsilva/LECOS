Esse código realiza a medição de energia **total** do domínio de energia package durante a execução de uma função qualquer da biblioteca stress-ng em ambiente **linux**.

Para executar os scripts adequadamente, o ambiente deve possuir:

* Sistema Operacional Linux com suporte ao subsistema `intel-rapl` via powercap (`/sys/class/powercap/`).
* Permissões adequadas para leitura dos sensores de energia e processos (`/proc/stat`).
* Ferramenta `stress-ng` instalada no sistema.
* Python 3 com as bibliotecas `matplotlib` e `numpy` instaladas para a geração dos gráficos.

Para diminuir o overhead da medição, o algoritmo foi separado em duas partes:
1. Medição de energia coletando o valor "bruto"dos contadores de energia do domínio de energia package via powercap. Arquivo `leitor-rapl.py`
2. Tratamento dos dados brutos por meio do cálculo do delta de energia e tempo durante duas medições. Conversão do valor para watts.
Abaixo, especificaremos a entrada e saída para cada um dos algoritmos acima

# Arquivo `leitor-rapl.py`
Este script é responsável por amostrar continuamente os contadores de energia do sistema e os *timestamps* correspondentes enquanto uma carga de estresse é executada. O script registra 10 segundos de ociosidade antes e depois do estresse para permitir a visualização do pico de consumo durante a medição. 

## **Argumentos de Entrada (via terminal):**

| Argumento    | Tipo   | Descrição                                                        |
| :----------- | :----- | :--------------------------------------------------------------- |
| `func1`      | String | Código/comando para chamar a função alvo do `stress-ng`.         |
| `freq`       | Float  | Frequência de amostragem das leituras do RAPL (em segundos).     |
| `nomeOutput` | String | Nome do arquivo de texto onde os resultados brutos serão salvos. |

## **Saída Gerada:**
Arquivo de texto (salvo no diretório `output/`) contendo o log bruto da execução. 
* **Formato:** `<energia_acumulada_microjoules> <timestamp_segundos>`


# Arquivo `tratar-dados.py`

Este script processa o log bruto gerado pela etapa anterior, calcula a potência média dissipada no intervalo e plota um gráfico indicando o período em que a carga de estresse esteve ativa.

## **Argumentos de Entrada (via terminal):**

| Argumento | Tipo | Descrição |
| :--- | :--- | :--- |
| `arquivoIn` | String | Caminho para o arquivo de texto contendo os dados brutos gerados pela coleta. |
| `arquivoOut` | String | Caminho para salvar o novo arquivo de texto com os dados tratados. |

## **Saídas Geradas:**
1. **Arquivo de Texto Tratado:** Contém as variações calculadas ao longo do tempo.
   * **Formato:** `<potencia_media_watts> <delta_tempo_segundos>`
2. **Gráfico (`output/grafico_energia.png`):** Uma visualização em linha da Variação de Potência Média (Watts) vs Tempo (Segundos), contendo marcações verticais indicando o início e fim da carga de estresse.


