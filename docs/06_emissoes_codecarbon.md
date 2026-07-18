# Calculando Emissões de Carbono
O [CodeCarbon](https://github.com/mlco2/codecarbon) é uma biblioteca em Python que permite estimar as emissões de carbono de uma aplicação. 

Para isso, o CodeCarbon considera que as emissões, expressas em quilogramas de CO2-equivalente **(CO2eq)**, são o produto de dois fatores principais:
- C = a **intensidade de carbono** da eletricidade utilizada para a computação; quantificada em g de CO2 emitida por quilowatt-hora de eletricidade; 
- E = **energia consumida** pela infraestrutura computacional: quantificada em quilowatthora. Para realizar as medições de consumo de energia, a biblioteca utiliza a interface RAPL.

As emissões de dióxido de carbono (CO2eq) são calculadas como o produto **C × E**.

## Intensidade de Carbono
A intensidade de carbono da eletricidade consumida (C) é calculada como a média ponderada das emissões de diferentes fontes de energia utilizadas para gerar eletricidade, incluindo combustíveis fósseis e renováveis.

Note que  uma rede elétrica local contém uma mistura de combustíveis fósseis e de fontes de energia de baixo carbono, chamada Matriz Energética. Com base na proporção de fontes de energia na rede local, a intensidade de carbono da eletricidade consumida pode ser calculada. Quando disponível, o CodeCarbon usa a intensidade de carbono da eletricidade por país (com dados do site Our World in Data).

# Script de Medição com CodeCarbon
Para avaliar o comportamento do CodeCarbon de forma isolada e limpa, utilizaremos o script `scripts/leitor-rapl-codecarbon.py`. Ele utiliza o gerenciador de contexto `OfflineEmissionsTracker` para criar uma janela de medição sobre a execução de um comando do `stress-ng`.

Abaixo, podemos visualizar a implementação configurada para a realidade da matriz energética brasileira (`country_iso_code="BRA"`):
```python


#configuração dos argumentos passados via terminal
parser = argparse.ArgumentParser(description="")
parser.add_argument("func1", type=str, help="codigo para chamar função 1 do stress ng")
parser.add_argument("freq", type=float, help="frequencia da amostragem do rapl (em segundos)")
parser.add_argument("caminhoOutput", type=str, help="nome do arquivo para salvar resultados")
args = parser.parse_args()

args.func1 = args.func1.split()

#--------------------- Inicio Medição ----------------------

with OfflineEmissionsTracker(country_iso_code="BRA", measure_power_secs=args.freq, output_dir=".", output_file=args.caminhoOutput, log_level="error") as tracker:
    #inicia stressng
    stress = subprocess.Popen(args.func1)
    while(stress.poll() == None):
        time.sleep(args.freq)

#--------------------- Fim Medição -------------------------
```
## Como Executar?
Siga os passos abaixo para E
1. **Ative o ambiente virtual**:
Na raiz do repositório, digite:
```bash
source venv/bin/activate
``` 

2. **Execute o script**:
```bash
# Sintaxe: sudo venv/bin/python scripts/leitor-rapl-codecarbon.py <"comando_estressor"> <frequência_amostragem> <nome_base_saida>
sudo venv/bin/python scripts/medicao-codecarbon.py "stress-ng --matrix 0 --matrix-method prod -t 30s" 1 medicao-codecarbon.csv
```

# Analisando a Saída:
Ao fim da execução, o CodeCarbon salvará os resultados no arquivo `emissoes.csv`. Precisamos extrair os valores de energia da CPU (`cpu_energy` e `cpu_power`). Além disso, também veremos a pegada de carbono da máquina durante a execução do script. 

Entretanto, para o cálculo das emissões de carbono, o CodeCarbon considera o gasto de outros componentes da máquina além da CPU, como a memória RAM. Para isso, são implementadas heurísticas que não serão abordadas no minicurso.

## O Script de Extração e Análise

O script `scripts/analisar-codecarbon.py`analisa o CSV gerado e imprime um painel com as informações da medição realizada.

Execute o script passando o log gerado pelo CodeCarbon como argumento:

```bash
# Sintaxe: python3 scripts/analisar-codecarbon.py <caminho_do_log_csv>
python3 scripts/analisar-codecarbon.py emissoes.csv
```

## Extra: Comparação de resultados
Podemos comparar a medição do consumo de energia da máquina via Powercap (realizada na etapa 1 do minicurso) com a ferramenta CodeCarbon. Execute novamente o comando abaixo e compare com a saída acima: 
1. **Ative o ambiente virtual**:
Na raiz do repositório, digite:
```bash
source venv/bin/activate
``` 

2. Execute o comando abaixo**:
```bash
# Sintaxe: python3 <caminho-do-script> <arquivo_entrada_tratado>
python3 scripts/consumo-total-powercap.py teste-powercap-tratado.txt
```
**Sintaxe:** python3 caminho-do-script [arquivo de entrada com os dados tratados]


## Navegação
[⬅️ Passo Anterior: Medicao de Processos com Scaphandre](05_medicao_scaphandre.md)