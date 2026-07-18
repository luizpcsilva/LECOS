O [Scaphandre](github.com/hubblo-org/scaphandre) é um agente de monitoramento escrito na linguagem Rust que permite obter o consumo de energia por processo, por máquina virtual ou por contêiner em execução em uma CPU.

Para fatiar o consumo de energia da máquina entre os processos em execução, a ferramenta utiliza a metodologia de **Modelagem de Energia Baseada em Tempo de CPU**. Nas etapas anteriores, explicamos o passo a passo para implementar essa técnica e, agora, iremos comparar a nossa implementação com a do Scaphandre.

O Scaphandre permite que a sua execução seja feita via Docker. Porém, para permitir seu funcionamento, precisamos fornecer permissões de acesso ao diretório `/proc` e `/sys/class/powercap`, responsáveis por armazenar as métricas de tempo do processo e o framework powercap, respectivamente.

Além disso, o Scaphandre foi pensado em ser extensível, basicamente se limitando a duas tarefas: **coletar/pré-computar** as métricas de consumo energético e **exporta-lás**. Para visualizar os resultados, exportaremos os resultados para o terminal (`stdout`) e para um arquivo json. Note que outros exportadores podem ser utilizados, como o Prometheus e Grafana.`

# Execução com saída no terminal

O comando abaixo executa o Scaphandre por 15 segundos, imprimindo a sua saída no terminal (stdout) a cada um segundo.
```bash
sudo docker run --privileged -v /sys/class/powercap:/sys/class/powercap -v /proc:/proc -ti hubblo/scaphandre stdout -t 15 -s 1
```
Explicação dos Argumentos:

*  `sudo docker run`: Executa o Docker como root.

*  `--privileged`: Por padrão, o Docker não possui restrições de acesso a pastas em `/proc` ou `/sys`. Esta flag desativa essas barreiras.

* `-v /sys/class/powercap:/sys/class/powercap` e -v `/proc:/proc` : Com as barreiras desativadas (argumento acima), a flag -v fornece acesso aos diretórios contendo as métricas de processos e a interface powercap.

* -ti: Uma combinação de duas flags (-t e -i). Elas alocam um terminal para o contêiner, garantindo que o output seja impresso diretamente na nossa tela.

* hubblo/scaphandre: É o nome oficial da imagem da ferramenta hospedada no repositório Docker Hub. O Docker fará o download e executará o código a partir desta imagem.

* stdout: É o tipo do exportador de dados. Nesse caso, a linha de comando (terminal).

* -t 15 (--timeout): Indica que a medição dura 15 segundos

* -s 1 (--step): Define a frequência de amostragem como 1 segundo

Durante sua execução, será possível ver o gasto dos 10 processos que mais consomem energia da máquina em cada intervalo de medição

# Execução com saída em JSON

O exportador `stdout` é ótimo para visualização rápida, porém, não nos fornece os dados de forma estruturada para realizarmos análises e experimentação. Portanto, utilizaremos o exportador JSON.

Para isso, faremos algumas alterações no comando do Docker:

1. Adicionamos permissão de acesso no diretório atual (`pwd`) com `-v $(pwd):/dados`, permitindo que a ferramenta crie e preencha o arquivo json. O diretório `/dados` se torna uma pasta virtual dentro do contêiner.

1. Mudaremos o exportador de `stdout` para `json -f /dados/scaphandre_saida.json`, sendo -f a flag que determina o caminho em que o arquivo será salvo

2. Adicionamos a flag `--process-regex "stress-ng"`. Com isso, o Scaphandre irá monitorar apenas os processos que possuam a string `"stress-ng"` em sua chamada na linha de comando, reduzindo a quantidade de "lixo" nos dados.

4. Retiramos a duração da medição (-t). Queremos monitorar o consumo de energia da máquina até que os processos estressores terminem sua execução.

Por fim, o comando responsável por executar o scaphandre ficará da seguinte forma:
```bash
sudo docker run --rm --name meu_scaphandre --privileged \
    -v /sys/class/powercap:/sys/class/powercap \
    -v /proc:/proc \
    -v $(pwd):/dados \
    hubblo/scaphandre \
    json -f /dados/scaphandre_saida.json -s 1 --process-regex stress-ng
```
Para fins de precisão, não iremos executar esse comando no terminal. Criamos o script `/scripts/medicao-scaphandre.py` que executa automaticamente o comando acima e instancia os processos do `stress-ng`. Segue abaixo um trecho desse código:

```python
cmd_scaphandre = [
    "sudo", "docker", "run", "--rm", "--name", "meu_scaphandre", "--privileged",
    "-v", "/sys/class/powercap:/sys/class/powercap",
    "-v", "/proc:/proc",
    "-v", f"{os.getcwd()}:/dados",
    "hubblo/scaphandre",
    "json", "-f", "/dados/scaphandre_saida.json", "-s", "1", "--process-regex", "stress-ng"
]
#--------------------- Inicio Medição ----------------------
#inicializa scaphandre
processo_scaphandre = subprocess.Popen(cmd_scaphandre, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(5)

#inicializando os dois processos estressores
stress1 = subprocess.Popen(args.func1)
stress2 = subprocess.Popen(args.func2)
print(stress1.pid)
print(stress2.pid)

#espera o processo acabar
stress1.wait()
stress2.wait()

time.sleep(5)

#finaliza o scaphandre
subprocess.run(["sudo", "docker", "stop", "meu_scaphandre"], stdout=subprocess.DEVNULL)
#--------------------- Fim Medição -------------------------
```
Ao término da execução, um novo arquivo chamado `scaphandre_saida.json` será gerado na raiz do repositório.

## Como executar?

Para exexutar, siga os passos abaixo:

1. **Ative o ambiente virtual**:
Na raiz do repositório, digite:
```bash
source venv/bin/activate
``` 
2. **Execute o código:** 
```bash
# Sintaxe: python3 <caminho-do-script> <"chamada_estressor_1"> <"chamada_estressor_2">
python3 scripts/medicao-scaphandre.py "stress-ng --matrix 0 --matrix-method prod -t 30s" "stress-ng --cpu 0 --cpu-method fibonacci -t 60s"
```
Note que estamos utilizando as mesmas funções do stress-ng das etapas anteriores, pelo mesmo tempo de execução.

# Estrutura do JSON e Tratamento de Dados
A estrutura do JSON é dividida em amostras de medição. Para cada amostra, ele gera uma árvore contendo:

* **`host`**: Traz o `timestamp` exato em que a amostra foi registrada pelo sistema.
* **`sockets`**: Representa o gasto energético do processador (equivalente ao domínio `package` que lemos manualmente no powercap). Extrair a energia total desta chave (em vez do consumo global do *host*) garante que o nosso script funcione em qualquer hardware, visto que nem todas as placas-mãe possuem sensores para medir a energia do sistema inteiro.
* **`consumers`**: Contém a lista de processos que foram monitorados. Nela, o Scaphandre já realizou toda aquela matemática de fatiamento por tempo de CPU que fizemos no passo anterior, entregando o consumo de energia isolado do processo pronto na chave `consumption`.

## Lógica do Algoritmo

Para automatizar a extração dessas métricas e a geração do gráfico, o script `scripts/tratar-dados-scaphandre.py` realiza duas tarefas principais. Ele percorre o arquivo JSON, buscando especificamente o consumo do domínio de energia `package` e coleta os consumos do processos que contenham as strings `"stress-ng-matrix"` e  `"stress-ng-cpu"` no campo `cmdline`, agrupando-os.

Ao fim de sua execução, geramos uma matriz com a mesma estrutura da etapa anterior: `[watts_P1, watts_P2, watts_Total, momento_final_intervalo]`. Posteriormente, a matriz é  convertida para um arquivo de texto e utilizada para gerar os gráficos `grafico-scaphandre1.png`e `grafico-scaphandre2.png`, com a mesma lógica da etapa anterior.

Abaixo, podemos visualizar o loop principal do código:

```python
for amostra in dados_json:
    #timestamp da medicao
    tempo_atual = amostra.get('host', {}).get('timestamp', 0)
    tempos_list.append(tempo_atual)
    
    #pega o consumo total da máquina (expecificamente o dominio package -> id = 0)
    lista_sockets = amostra.get('sockets', [])
    consumo_socket_0 = next((s.get('consumption', 0) for s in lista_sockets if s.get('id') == 0), 0)
    total_w = consumo_socket_0 / 1_000_000.0
    total_watts_list.append(total_w)

    #zera os contadores de watts
    watts_mat = 0.0
    watts_fib = 0.0
    
    #varre os processos ativos nessa medição
    for processo in amostra.get('consumers', []):
        #identifica o executavel e consumo do processo
        cmdline = processo.get('cmdline', '')
        consumo_w = processo.get('consumption', 0) * 10**(-6)
        
        #filtramos se é um processo da matriz ou do fibonacci. soma no contador se for
        if "stress-ng-matrix" in cmdline:
            watts_mat += consumo_w
        elif "stress-ng-cpu" in cmdline:
            watts_fib += consumo_w

    #guarda os valores na lista        
    p1_watts_list.append(watts_mat)
    p2_watts_list.append(watts_fib)

#calculando tempo
tempo_inicial = tempos_list[0]
tempos_list = [t - tempo_inicial for t in tempos_list]

#convertendo para numpy
p1_watts = np.array(p1_watts_list)
p2_watts = np.array(p2_watts_list)
total_watts = np.array(total_watts_list)
tempos = np.array(tempos_list)

#armazenando dados tratados em arquivo txt e matriz para o grafico
matriz_saida = np.column_stack((p1_watts, p2_watts, total_watts, tempos))
np.savetxt(args.arquivoTxtOut, matriz_saida, fmt="%.6f")

#gerando os gráficos
plotarGrafico(matriz_saida)
```
## Como executar?

Para executar a limpeza de dados e geração do gráfico, siga os passos a seguir:
1. **Ative o ambiente virtual** (caso ainda não esteja ativo):
Na raiz do repositório, digite:
```bash
source venv/bin/activate
```

2. **Execute o comando abaixo:**
```bash
# Sintaxe: python3 <caminho-do-script> <arquivo_json_entrada> <arquivo_txt_saida>
python3 scripts/tratar-dados-scaphandre.py scaphandre_saida.json teste-scaphandre-tratado.txt
```
Os gráficos e arquivos de texto serão gerados instantaneamente na raiz do repositório.

# Extra: Comparando as medições.
Agora, podemos comparar a medição realizada na etapa anterior com a ferramenta Scaphandre e verificar se os números retornados são semelhantes.

Execute os comandos abaixo no terminal:
```python
# Sintaxe: python3 <caminho-do-script> <arquivo_entrada_tratado>
python3 scripts/consumo-total-processos.py teste-processos-tratado.txt
python3 scripts/consumo-total-processos.py teste-scaphandre-tratado.txt
```

Compare o resultado. **Os valores são iguais?**

Em seguida, utilizaremos a ferramenta codecarbon para calcular as emissões de carbono das medições realizadas.

## Navegação
[⬅️ Passo Anterior: Tratamento de Dados da Medição de Processos Concorrentes](04_tratamento_de_dados_2.md) | [➡️ Passo Seguinte: Medição de Emissoões de Carbono](06_emissoes_codecarbon.md)
