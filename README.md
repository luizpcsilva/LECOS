# LECOS
> Laboratório de Eficiência Energética e Computação Sustentável



**TODO**

# Introdução

O seguinte texto apresenta um levantamento da pesquisa inicial do projeto **Computação Sustentável e Energeticamente Eficiente**. Nessa primeira etapa, investigamos técnicas e ferramentas existentes para a medição do gasto energético de aplicações computacionais e estimativas para o cálculo das emissões de carbono geradas por elas.

# Sumário
**TODO**
# Motivação
**TODO**
explicar pq a pesquisa foi feita (citar artigos que falam do impacto energético das aplicações com uso intensivo de dados)

# Medição Energética 

Abaixo, vamos apresentar alguns dos métodos existentes para medição energética de computadores. A categorização foi proposta por [^5].

## Dispositivos Externos[^5]

Também chamados de medidores de potência, são equipamentos externos posicionados entre a tomada e a fonte de alimentação do sistema de computação. Fornecem dados do consumo total do computador, sem a possibilidade de dividir o gasto entre os componentes de hardware. A performance da medição é alta, mas vai depender da qualidade do equipamento.

## Dispositivos Intra-Nó[^5]

São equipamentos instalados dentro de computadores, geralmente entre a placa-mãe e dispositivos de hardware. Eles podem fornecer o gasto individual de componentes, porém, requer investimento e são pouco amigáveis para o usuário.

## Sensores de Hardware e Interfaces de Software[^5]

Atualmente, os sistemas de computação incorporam sensores digitais e circuitos integrados em componentes de hardware com o objetivo de medir o consumo de energia em um intervalo de tempo. Essa medição abrange o sistema inteiro, processador, memória ou placa de vídeo integrada, a depender da tecnologia de fabricação do computador.

Nesse relatório, abordaremos a interface RAPL, NVML e IPMI. Destinaremos algumas seções mais abaixo para tratar desse assunto.

## Modelagem de Potência e Energia[^5]

Em muitos casos, as medições acima não são suficientes, principalmente quando não se tem acesso às interfaces de software ou quando se deseja obter o consumo energético a nível de aplicação. Nesses casos, podem ser utilizados modelos matemáticos para aproximar o consumo de energia real. Abaixo, vamos descrever alguns métodos envolvendo esses modelos.

### Modelagem Baseada em Uso

Esses modelos se baseiam na utilização de recursos de sistema, como o uso de CPU. Alguns modelos são lineares e assumem que o consumo de energia aumenta linearmente conforme o uso de CPU aumenta. Entretanto, já se sabe que essa relação nem sempre é linear, fazendo com que outros modelos adicionassem não linearidade com o objetivo de diminuir erros de estimativa.

Alguns modelos consideram o *Thermal Design Power* (TDP) de um processador para calcular seu consumo total de potência, realizando o produto entre o TDP, a média do uso da CPU  e o tempo total de execução.

### Modelagem a nível de processo

Nesse tipo de modelagem, é estimado o consumo energético de cada processo, com base em métricas de energia de componentes do sistema inteiro. Esses modelos podem ser separados em dois tipos: **Baseadas em Uso** e **Baseadas em Regressão com Eventos de Performance**.

O primeiro tipo utiliza métricas de sensores de hardware, como o RAPL, para obter o gasto total da CPU. Em seguida, o tempo de CPU que cada processo utilizou é utilizado como estimativa para a fatia de consumo que o processo alvo utilizou.
* [ ] Falar sobre as limitações desse método.

Já o segundo utiliza métricas do RAPL em combinação com modelos de regressão alimentados com contadores de eventos de performance de hardware. Alguns desses eventos são os ciclos de clock da CPU, número de instruções executadas e *caches misses*.  Esse método requer uma calibração inicial com um medidor de potência externo ou dados do RAPL.

# Sensores de Hardware e suas Interfaces

Na seção acima, discutimos sobre a utilização de sensores de hardware para medição energética. Abaixo, iremos detalhar algumas interfaces conhecidas.
# RAPL
- [ ] Algumas informações boas:
"AMD RAPL Characteristics", "Key Takeaways for RAPL Measurements" e "Challenges and Edge Cases" em[^2]**TODO**
# IPMI

**TODO**
# NVML

**TODO**

# Medição Energética de Aplicações Específicas (provavelmente essa seção será deletada)

**TODO**

Aqui podemos citar:
- que os sensores existentes dentro do computador apenas fornecem dados brutos do consumo total da máquina e não dividem esse gasto entre as aplicações. 
- Da dificuldade de estimar o custo energético exato de aplicações
- Diferença breve dos softwares do tipo: Modelos de Divisão de Energia e Modelos de Isolamento de Energia
- Um breve histórico de como essa medição é/era feita (Seção Related Work de [^1] e artigo RAPL in Action
- Iremos focar inicialmente no consumo da CPU) 

# Modelos de Divisão de Potência
**TODO**
- [ ] Explicar diferença modelos de potencia e energia (artigo protocolo dos power models)
- [ ] falar das Limitações conhecidas desses modelos e do erro

São softwares que realizam modelagem de potência e energia a nível de processo, por meio da consulta de sensores de hardware via interfaces, para obter o consumo energético total de um dispositivo e, em seguida, consultar métricas de sistema para dividir esse consumo entre as aplicações que estão sendo executadas no dispositivo [^1] .  

Note que as interfaces utilizadas para obter dados de sensores de hardware sobre o consumo de energia (e.g RAPL, NVML) fornecem valores em Joules (Energia). Entretanto, como a consulta desses dados é feita de forma periódica, veremos que os modelos a seguir frequentemente realizam a conversão desses valores para Joules (Potência), com base no intervalo de tempo em que o consumo de energia foi observado. Segundo [^2], essa prática ;e importante para ajudar os usuários a compreender o consumo instantâneo de suas aplicações.

- [ ] verificar oq o [^1] fala sobre isso, confirmando as informações e analisando anovamente a crítica deles com relaç~ao a isso
- [ ] Falar sobre essa citaçao do codecarbon
> [!PDF|255, 208, 0] [[CodeCarbon documentacao.pdf#page=27&annotation=1323R]]
> > The most accurate tracking methods rely on built-in hardware energy counters rather than instantaneous power draw. 
> 
> 





## Scaphandre [^3]
- [ ] Detalhar como os dados sao obtidos em SOs diferentes
O Scaphandre é um agente de monitoramento escrito em RUST, com foco em obter o consumo energético específico de processos, máquinas virtuais e containers (kubernetes).

### Técnica utilizada

Para calcular o consumo energético de aplicações, o Scaphandre coleta continuamente dados dos sensores RAPL durante a execução do programa, com foco no domínio de energia PSYS por cobrir a maioria dos componentes. Se esse domínio não estiver disponível, são somados os dados do domínio PKG + DRAM.

A cada dado coletado do RAPL, são lidos os valores do tempo de uso da CPU de cada processo sendo executado na máquina naquele intervalo.

Em seguida, é calculada uma estimativa para o gasto por meio de uma proporção entre o consumo energético total do processador no intervalo e a fatia de tempo de cpu que um processo utilizou.

Note que alguns serviços e programas são executados em diversos processos diferentes ao mesmo tempo. Nesse caso, é recomendado exportar os dados para um Banco de Dados de Séries Temporais, como o do software Prometheus, por exemplo. Assim, é possível agregar o consumo energético dos processos e obter o gasto total da aplicação.

### Particuliaridades

O Scaphandre foi pensado em ser extensível, basicamente se limitando a duas tarefas: **coletar/pré-computar** as métricas de consumo energético e **exporta-lás**. Logo, é possível utilizar diversos softwares diferentes para visualizar os dados de energia, como o [Grafana](https://github.com/grafana/grafana) e [Prometheus](https://github.com/prometheus/prometheus), por exemplo. 
- [ ] Acrescentar terminologia dos Jiffies
- [ ] Mencionar o sistema de arquivos proc/pid/stats da onde vem o tempo de cpu
- [ ] mencionar oq o scaphandre faz para quebrar a virtualização das VMs e calcular o gasto energético




## CEEMS

**TODO para cada processo sendo executado na máquina **


**TODO**
## Tracarbon

**TODO**
## JoularJX

É um agente baseada em Java com a função de realizar monitoramento de energia em nível de código ou de aplicações em Java. A ferramenta se propoẽ a 


## Cloud Carbon Footprint

**TODO**
## Kepler

**TODO**
## PowerAPI

**TODO**
# Modelos de Isolamento
**TODO**

## CodeCarbon[^2]

É uma biblioteca em Python open source, com o objetivo de monitorar as emissões de carbono provenientes da computação realizada em um computador local. Para calcular essas emissões, é necessário calcular o gasto energético associado ao alvo da observação.

Nesse sentido,  a bilbioteca se propõe a estimar o consumo energético de trechos específicos de códigos em Python e, além disso, permite também obter medições de energia do sistema total ou durante a execução de algum comando 
- [ ] (**verificar se no segundo caso há técnicas de cpu usage**).
### Métricas de energia utilizadas

Atualmente, Codecaarbon tem suporte para obter o consumo energético dos seguintes hardwares:
- GPU, via biblioteca nvidia-ml-py 
- [ ] verificar se essa biblioteca consulta a NVML
- RAM, via heurísticas baseadas no tamanho da RAM. Por mais que o RAPL forneça dados de consumo energético da DRAM, a ferramenta optou por não utilizar por não ter certeza da acurácia dos dados.
- [ ] Detalhar essa heurística
- CPU, via Intel Power Gadget no Windows/Mac, `powermetrics`em processadores Apple Silicon Chips e arquivos do RAPL no Linux.


Note que, caso não seja possível acessar as métricas de consumo de energia da CPU, o Codecarbon passa a realizar aproximações com base no tipo da CPU e seus valores de [Thermal Design Powers](https://en.wikipedia.org/wiki/Thermal_design_power).
### Utilização do RAPL

O codecarbon faz uma seleção inteligente dos domínios de energia do RAPL que serão utilizados para fornecer as métricas do consumo energético da CPU. 

Em primeiro lugar, o Codecarbon prioriza o package domain. Esse domínio de energia  fornece dados dos núcleos da CPU e GPU integrada. Segundo a ferramenta, esse domínio possui uma taxa de atualização confiável quando a CPU está sobrecarregada, fornece dados consistentes entre diversas gerações Intel e pode ser integrado ao domínio da DRAM para obter gastos da memória.

Entretanto, pode-se customizar a biblioteca para utilizar o domínio PSYs
- [ ] Falar talvez dos bonus de utilizar ele e estudar essa conexão coom o PCIe
- [ ]falar tambem dos dados do Last-level cache �LLC� • Memory controller • System agent/uncore que vem no package domain.

### Técnica Utilizada
Para monitorar o gasto de energia o Codecarbon faz uma consulta periódicas aos sensores de hardware via interfaces, conforme discutido anteriormente em métricas utilizadas. Note que, quando não disponíveis, a ferramenta utiliza modelos genêricos baseados no tipo do hardware, realizando aproximações.

A cada consulta, é calculada a variação de energia com base nas medições anteriores. Em seguida, calcula-se a potência média desse intervalo de medição, dividindo a variação encontrada pelo intervalo de tempo. O Codecarbon afirma que monitorar a potência ao invés da energia é importante para ajudar os usuários a entender o consumo instantâneo das aplicações.

Como os sensores de potência de um computador não são confiáveis, a transformação utilizando os contadores de energia se torna necessária 
- [ ] Embasar isso. Verificar no artigo [^1]

O somatório de todas as variações de energia e a média entre as potências dos intervalos se tornam as métricas analisar o comportamento do sistema durante a execução de uma aplicação.

### Visualização dos dados
- [ ] Falar que o gráfico de potência não aponta muita coisa visto que é uma média de potências. Isso esconde picos de potência que não aparecem

### Ruído de sistema
- [ ] Falar que a documentação não aborda o ruído de sistema proveniente de considerar o gasto da máquina como o gasto de aplicação. Técnicas para minimização desse ruído serão abordadas mais a frente.

## Green Metrics Tool (GMT) [^4]

É uma ferramenta de desenvolvedor capaz de realizar medição energética de aplicações e suas emissões de carbono. Possui suporte específico para aplicações com interface gráfica, machine learning, aplicações web e virtualização por máquinas virtuais. Focaremos na medição bare-metal, sem abordar as funcionalidades para aplicações específicas.

Uma das filosofias adotadas por esse software é a containerização das aplicações para a medição energética.  Segundo a ferramenta,  isso permite um maior controle da execução, interface e ambiente ao redor do processo. Além disso, a containerização traz uma baixa sobrecarga de processamento, afetando pouco a medição em si.

### Técnica utilizada

Enquanto os Power Models utilizam modelos matemáticos para fatiar o consumo total da máquina entre as aplicações, o GMT realiza uma estratégia diferente. Eles decidiram que irão atribuir o gasto total da máquina ao software sendo medido durante a sua execução. Segundo a ferramenta, ainda não há um padrão ouro para fatiar o consumo energético entre as aplicações e, a técnica de divisão de potência por tempo de cpu apresenta muitas limitações.  

Para permitir que o custo  energético real da aplicação sendo medida seja mais próximo com o custo total da máquina, a ferramenta exige uma preparação de ambiente por meio de uma coleção de boas práticas. Essas medidas serão discutidas em uma seção separada.

### Métricas de energia utilizadas

O GMT possui suporte para métricas diversas métricas de energia, sendo tanto da máquina inteira via IPMI e MCP ou de componentes específicos, como CPU e DRAM, via RAPL.  A lista completa de métricas suportadas está disponível da documentação [^4], assim como as instruções para a configuração da medição. Note que as métricas que serão utilizadas em uma medição devem ser especificadas nos arquivos de configuração da ferramenta.

### O Gasto Energético da Própria Medição

Um diferencial do GMT é a presença de um script de calibração que estima o consumo energético da própria medição em si, obtendo uma sobrecarga relativa em comparação com o gasto total da aplicação. Esse script é executado antes da medição real do software. Ele atua em tres etapas:

1. System Baseline: É realizado a leitura do gasto do servidor em estado de repouso com apenas uma métrica de energia (a menor sobrecarga possível).
2. System Idle: Ainda com o servidor em repouso, o script liga todos os sensores para obter dados de todas as métricas possíveis. A diferença de potência entre o passo 1 e 2 mostra quanto de sobrecarga relativa de energia os sensores geram por existir.
3. O script gera um estresse artificial para sobrecarregar totalmente a máquina, ao mesmo tempo que realiza as medições com todas as métricas determinadas. É calculado aqui a sobrecarga de energia desses sensores em um contexto de estresse.

A diferença entre o consumo de energia no passo 3 com o do passo 2 mostra uma estimativa do consumo de energia dos sensores.

### Temperatura do Computador 
O GMT considera a temperatura da CPU para as medições, pois a temperatura altera o gasto energético. 
* [ ] Puxar uma referência para isso
Por isso, o mesmo script de calibração executado na seção anterior também calcula o tempo que leva para a cpu esfriar após ser estressada. Esse valor é importante para servir como guia para a execução de testes. Um teste não deve ser executado em seguida do outro, deve-se aguardar esse tempo.

### Estimando o gasto de conteiners

Algumas aplicações (como web) podem exigir que mais de um container seja executado simultaneamente. Por mais que o foco do GMT não seja a distribuição do gasto total da máquina entre diferentes processos, a ferramenta oferece uma estimativa para o consumo individual de cada container.

Nesses casos, a ferramenta implementa um modelo de divisão de potência utilizando dados do consumo total da máquina e do tempo de CPU de cada container, seguindo uma técnica semelhante ao do Scaphandre.

Para diminuir o erro, é encorajado fortemente seguir uma série de boas práticas que serão definidas em seções abaixo.

Por fim, recentemente o GMT lançou uma funcionalidade beta que utiliza core-pinning (fixar conteiners em núcleos específicos) em processadores AMD. Essa técnica permite separar melhor o gasto energético de cada conteiner.

# Boas práticas para medição energética de aplicações
**TODO**

# Emissões de carbono
**TODO**
Explicar um pouco sobre a natureza dessas emissões e etc. 

  

## ISO medição de carbono
**TODO**
  

# Softwares de estimativa para emissões de carbono

  Colocar a lista de softwares que calculam essas emissões. Cada um terá titulo ##. Falarei sobre como ele faz a conta, como obtém dados da intensidade de carbono, etc. Segue a ISO? coisas assim

  **TODO**
# Referências



[1]: CADOREL, Emile; SAINGRE, Dimitri. A protocol to assess the accuracy of process-level power models. In: **2024 IEEE International Conference on Cluster Computing (CLUSTER)**. IEEE, 2024. p. 74-84.
[^2]: CODECARBON. **CodeCarbon documentation**. [S. l.], 2026. Disponível em: https://docs.codecarbon.io. Acesso em: 26 abr. 2026.
[^3]: HUBBLO. **Scaphandre documentation**. [S. l.], 2026. Disponível em: [https://hubblo-org.github.io/scaphandre-documentation](https://hubblo-org.github.io/scaphandre-documentation). Acesso em: 22 abr. 2026.
[^4]:  GREEN METRICS TOOL. GMT documentation https://docs.green-coding.io/docs
[^5]: JAY, Mathilde et al. An experimental comparison of software-based power meters: focus on CPU and GPU. In: **2023 IEEE/ACM 23rd International Symposium on Cluster, Cloud and Internet Computing (CCGrid)**. IEEE, 2023. p. 106-118.