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
"AMD RAPL Characteristics", "Key Takeaways for RAPL Measurements" e "Challenges and Edge Cases" em[^2]
## Definição

## Leitura via Registradores MSRs
Causa menos overhead [^6]
**TODO**

## Leitura via Sistema Operacional (`powercap`) [^7]
Uma maneira de evitar a complexidade de lidar diretamente com instruções RDMSR em ambientes linux é utilizar o framework Powercap, mantido pela Linux Foundation.

Não haviam restrições de acesso root para leitura dos dados do powercap, permitindo que qualquer aplicação pudesse monitorar o consumo energético. Até que foi constatada uma falha de segurança em 2020 [^8], implementando a necessidade de acesso privilegiado a esses dados. Aplicações mal intencionadas poderiam utilizar a energia consumida em um intervalo para inferir o tipo de instrução sendo executada e, assim, roubar informações sigilosas.

### Powercap

É um framework do kernel do linux que atua como uma camada de abstração, fornecendo uma interface (via sysfs) entre o kernel e o espaço do usuário, permitindo que ferramentas possam monitorar e limitar o consumo de energia de dispositivos do hardware de forma padronizada.

O framework expõe os dispositivos do hardware via uma árvore de objetos. No linux, um objeto representa uma estrutura de dados do kernel que armazena informações referentes ao Sistema Operacional. Um objeto é sempre carregado na memória e, para facilitar a visualização para o usuário, aparece virtualmente como um diretório no gerenciador de arquivos.

No contexto do Powercap, o objeto no topo (raiz) da árvore representa o tipos de controle, referente ao método de power capping (limitação de potência). Nesse caso, trabalharemos com o RAPL.

Dentro de cada objeto de tipo de controle, temos acesso aos domínios de energia do método selecionado, contendo **atributos de monitoramento**, para visualizar o gasto de energia, e **atributos de restrições**, fornecendo opções para limitar o consumo de energia de um componente.

Lembre-se que, os domínios de energia são hierárquicos. Essa hierarquia está presente no powercap, onde cada objeto contendo os domínios de energia podem englobar outros subdomínios. Se aplicarmos uma restrição de potência em um domínio de energia, o próprio hardware vai definir como essa restrição será aplicada entre os subdomínios por meio de heuristicas.

### Atributos de monitoramento mais relevantes

Abaixo, destacamos 3 atributos de monitoramento importantes para medição energética. A lista completa de atributos, incluindo os de restrição, pode ser encontrada na documentação do Kernel Linux em [^7]

#### energy_uj (rw)
Contador de energia em microjoules do do domínio de energia acessado. Escreva 0 para resetar o contador.

#### max_energy_range (ro)
Valo máximo do contador antes de dar overflow.

#### name (ro)
Nome da power zone.

### Chamadas de Sistema

Os atributos presentes no powercap podem ser lidos por meio de `cat`ou abertos com editores de texto comuns. Quando um desses programas é executado, é feita uma solicitação ao SO (system call), que direciona o pedido ao framework do powercap. O powercap chama a função do driver responsável pelo atributo (no nosso contexto, intel_rapl).

A função do driver é executada. Se estivermos consultando o contador de energia de um domínio de energia do RAPL, são lidos os valores do MSR (Model Specific Register) via instruções rdmsr (Reading Model Specific Registers). A função converte o valor obtido,  codificado em uma unidade de energia da arquitetura do processador, para microjoules.


## Informações Relevantes para Medição com RAPL [^2]

### Domínio de Energia Mais Confiável

Segundo o CodeCarbon [^2], o domínio mais confiável é `package`, englobando os contadores dos núcleos da CPU, GPU integrada, System Agent e controlador da LLC (Last-Level Cache). Isso se deve ao fato de fornecer medidads mais consistentes que atualizam corretamente durante estresse em todas as gerações da Intel.

Segundo a ferramenta, por mais que o domínio `psys` seja maia alto na hierarquia e englobe mais componentes, ele pode não incluir todos os componentes em sistemas Intel mais antigos, deixando o domínio `package`de fora, por exemplo.

Note que nunca se deve somar domínios de energia do RAPL sem verificar a hierarquia, pois isso pode levar a duplicação de valores. Verifique sempre se um domínio já está contido no outro antes da soma.

## Desafios e Anomalias na leitura de dados do RAPL [^2]

### Overflow nos Contadores de Energia
Os contadores de energia costumam ter um limite de 32 ou 64 bits. Quando eles chegam no limite máximo, eles retornam para zero. Ao realizar o delta de energia ($E_2 - E_1$) nesse intervalo, será constatado um valor negativo, pois o primeiro valor será menor que o segundo. É necessário aplicar correções a esses valores.

### Intervalos de Medições Muito Pequeno
Por conta de anomalias no escalonador da thread, o intervalo entre as medições pode ser muito pequeno. Caso se queira converter a energia consumida para potência média nesse intervalo, a divisão $E \div T$  pode causar uma explosão no valor de Watts, por conta de T ser muito próximo de zero.

# IPMI
**TODO**
# NVML
**TODO**
# Ferramentas para Medição Energética e de Potência
**TODO**
- [ ] Explicar diferença modelos de potencia e energia (artigo protocolo dos power models)
- [ ] falar das Limitações conhecidas desses modelos e do erro
Nessa seção, traremos a descrição e metodologia de ferramentas que reportam o consumo de energia de componentes de hardware, trazendo o consumo energético bare-metal total da máquina em um intervalo de tempo. O processo para obtenção desses dados está descrito na seção [Sensores de Hardware e Suas Interfaces](# Sensores de Hardware e suas Interfaces).

Alguma delas implementam [Modelos de Divisão de Potência](#modelos-de-divisão-de-potência), trazendo uma estimativa do consumo a nível de processo, container ou máquina virtual. Reservamos uma seção mais abaixo para tratar dessas ferramentas

## CodeCarbon[^2]

É uma biblioteca em Python open source, com o objetivo de monitorar as emissões de carbono provenientes da computação realizada em um computador local. Para calcular essas emissões, é necessário calcular o gasto energético associado ao alvo da observação.

Nesse sentido,  a bilbioteca se propõe a estimar o consumo energético de trechos específicos de códigos em Python e, além disso, permite também obter medições de energia do sistema total ou durante a execução de algum comando 
- [ ] (**verificar se no segundo caso há técnicas de cpu usage**).
### Métricas de energia utilizadas

Atualmente, Codecarbon tem suporte para obter o consumo energético em ambiente Linux, Windows e MacOS. A técnica utilizada para interagir do hardware depende de qual ambiente está sendo realizado o teste. Os domínios de energia consultados vão depender de qual tecnologia será consultada.

### Ambiente Linux
Nesse caso, a obtenção dos dados de medição energética é realizada via consultas a interface do RAPL, por meio do framework [powercap](#powercap).

### Ambiente Windows
Nesse caso, é utilizada a ferramente Intel Power Gadget. Note que se trata de uma ferramenta descontinuada em 2023 pela Intel.

### Ambiente MacOS
É utilizada a ferramenta `powermetrics`, nativa desse ambiente.

- GPU, via biblioteca nvidia-ml-py 
- [ ] verificar se essa biblioteca consulta a NVML
- RAM, via heurísticas baseadas no tamanho da RAM. Por mais que o RAPL forneça dados de consumo energético da DRAM, a ferramenta optou por não utilizar por não ter certeza da acurácia dos dados.
- [ ] Detalhar essa heurística
- CPU, via Intel Power Gadget no Windows/Mac, `powermetrics`em processadores Apple Silicon Chips e arquivos do RAPL no Linux, na pasta `sys/class/powercap.



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

São softwares que reportam o consumo de energia e o consumo de potência de componentes do hardware, como CPU,
# Modelos de Divisão de Potência

São softwares que realizam modelagem de potência e energia a nível de processo, por meio da consulta de sensores de hardware via interfaces, para obter o consumo energético total de um dispositivo e, em seguida, consultar métricas de sistema para dividir esse consumo entre as aplicações que estão sendo executadas no dispositivo [^1] . 

Note que as interfaces utilizadas para obter dados de sensores de hardware sobre o consumo de energia (e.g RAPL, NVML) fornecem valores em Joules (Energia). Entretanto, como a consulta desses dados é feita de forma periódica, veremos que os modelos a seguir frequentemente realizam a conversão desses valores para Watts (Potência), com base no intervalo de tempo em que o consumo de energia foi observado. Segundo [^2], essa prática é importante para ajudar os usuários a compreender o consumo instantâneo de suas aplicações.

- [ ] verificar oq o [^1] fala sobre isso, confirmando as informações e analisando anovamente a crítica deles com relaç~ao a isso
- [ ] Falar sobre essa citaçao do codecarbon: "The most accurate tracking methods rely on built-in hardware energy counters rather than instantaneous power draw.". 
- [ ] Acrescentar terminologia dos Jiffies
- [ ] Mencionar o sistema de arquivos proc/pid/stats da onde vem o tempo de cpu
- [ ] mencionar os erros desse tipo de medição
## Scaphandre [^3]

O Scaphandre é um agente de monitoramento escrito em RUST, com foco em obter o consumo energético específico de processos, máquinas virtuais e containers (kubernetes).

A ferramenta utiliza dados do RAPL e possui compatibilidade com Windows e GNU/LINUX, havendo poucas diferenças na oferta de funcionalidades entre os SOs

Para calcular o consumo energético de aplicações, o Scaphandre coleta continuamente dados dos sensores de hardware durante a execução do programa. A interface de hardware utilizada dependem do ambiente no qual a ferramenta será executada.

A cada dado coletado, são lidos os valores do tempo de uso da CPU de cada processo. Abaixo, explicamos como essa coleta é feita em ambiente Linux:
### Execução em  Ambiente Linux.
Nesse caso, são coletados os dados do RAPL via framework [powercap](#), com foco no domínio de energia PSYS por cobrir a maioria dos componentes. Se esse domínio não estiver disponível, são somados os dados do domínio PKG + DRAM.

Para obter o tempo de CPU dos processos, são lidos os dados do `proc/ Filesystem` [^11].  Nesse sentido, duas leituras são feitas. A primeira obtém o tempo de CPU em `proc/{pid}/stat` de cada processo, somando as duas colunas de unidades de `USER_HZ`,  `utime` (user mode) e `stime` (kernel mode) .

A segunda leitura é realizada no arquivo `proc/stat` [^12], para obter o tempo total da CPU decorrido desde o início da execução do dispositivo. Essa medida é necessário para calcular a parcela de consumo do tempo de CPU por um processo dentro de um intervalo de tempo, permitindo que o perfilamento de energia seja feito. 

Note que nesse arquivo existem diversas colunas de dados, fornecendo os contadores de tempo da CPU para diferentes tipos de trabalho. São elas, respectivamente:

1. Processos executando em user mode.
2. Processos com nice executando em user mode.
3. Processos executando em kernel mode.
4. Tempo em espera (idle).
5.  Tempo de espera de instruções de I/O (não é confiável).
6. Tempo de interrupções de serviço.
7. Tempo de interrupções de software.
8. Tempo de espera involuntária (steal).
9. Tempo de execução de uma sessão de convidado.
10. Tempo de execução de uma sessão de convidado com nice.

Assim, realizamos a soma dessas colunas. Porém, note que nem todas contabilizam o tempo em que a CPU esteve ativa de fato. Portanto, a ferramenta Scaphandre desconsidera as colunas de: Tempo de espera, Tempo de espera de I/O, Interrupções de serviço e de software.  Esse comportamento pode ser observado na função `total_time_jiffies` do arquivo `scaphandre/src/sensors/mod.rs` do repositório da ferramenta.
### Execução em Ambiente Windows
A leitura é feita diretamente nos registradores MSR, via instruções RDMSR.

### Particuliaridades

O Scaphandre foi pensado em ser extensível, basicamente se limitando a duas tarefas: **coletar/pré-computar** as métricas de consumo energético e **exporta-lás**.Logo, é possível utilizar diversos softwares diferentes para visualizar os dados de energia, como o [Grafana](https://github.com/grafana/grafana) e [Prometheus](https://github.com/prometheus/prometheus), por exemplo. 

Além disso, conforme citado anteriormente, o Scaphandre possui suporte para modelar o consumo energético e de potência em máquinas virtuais. Note que nesses ambientes existem complicações, já que VMs só tem acesso a uma parte do sistema onde estão implementadas e não possuem acesso a métricas de energia do host.

Portanto, para tornar essa medição possível, o Scaphandre realiza uma ponte entre a máquina virtual e se host, trazendo as métricas de energia do bare-metal para ambiente virtualizado. 

Note que alguns serviços e programas são executados em diversos processos diferentes ao mesmo tempo. Nesse caso, é recomendado exportar os dados para um Banco de Dados de Séries Temporais, como o do software Prometheus, por exemplo. Assim, é possível agregar o consumo energético dos processos e obter o gasto total da aplicação.


## CEEMS

**TODO para cada processo sendo executado na máquina **

**TODO**
## Tracarbon

**TODO**
## JoularJX

É um agente baseada em Java com a função de realizar monitoramento de energia em nível de código ou de aplicações em Java
*TODO*


## Cloud Carbon Footprint

**TODO**
## Kepler

**TODO**
## PowerAPI

**TODO**

# Boas práticas para medição energética 

Nessa seção, detalharemos uma coletânea de boas práticas extraídas de artigos e ferramentas. 

## Taxa de amostragem [^4]
A frequência de coleta de dados das métricas (taxa de amostragem) deve ser de pelo menos a metade da duração do menor evento que se deseja capturar. Isso garante a precisão necessária para não perder picos rápidos de consumo durante a execução do experimento.

## Controle da temperatura [^4]
A temperatura de um processador influencia na medição energética. É importante esperar um intervalo de tempo de 180 segundos entre uma medição e outra, para dar tempo dos componentes esfriarem. Em processadores com mais de 30 cores, esse tempo deve ser maior.
Controle a temperatura. Dê um espaçamento de tempo adequado entre as medições. Se um sistema sobreaquecer durante a medição, isso deve ser levado em consideração. 

## Minimização do ruído de fundo [^4]
Durante a execução do experimento, o gasto energético total da máquina será capturado por interfaces de hardware como o RAPL. Para garantir que estamos medindo o software alvo e não o "ruído" do sistema operacional, é importante diminuir a possibilidade de interrupções na CPU. Recomenda-se tomar as seguintes precauções:

- Desativar conexões de rede (Wi-Fi e Internet), a menos que sejam objeto de teste;
- Evitar qualquer interação com periféricos (mouse e teclado) durante a execução;
- Desligar o escurecimento automático da tela, proteção de tela e modos de suspensão;
- Encerrar processos em segundo plano que não sejam essenciais;
- Desativar tarefas agendadas, atualizações automáticas do sistema operacional e rotinas de manutenção

## Escreva resultados na memória [^4]
Para armazenar os valores das medições, é recomendado realizar a escrita em um arquivo que esteja localizado na memória RAM. A escrita em disco é uma operação que gasta bastante energia e, caso seja feita com frequência, pode alterar o experimento a depender as métricas utilizadas.

# Boas práticas para medição energética de aplicações
Na seção [Modelos de Divisão de Potência](#modelos_de_divisao_de_potencia), detalhamos como o particionamento de energia entre as aplicações era feito. Segundo [^4], esse método só funciona caso esteja em uma frequência de clock fixa, sem Hyperthreading ou Turboboost ativado. Além disso, a execução de instruções estranhas como AVX podem distorcer o fatiamento de energia. É importante levar em consideração esses fatores pois, com eles, o tempo de uso de CPU deixa de ter uma relação clara com o consumo de energia.

Em [^1],  também foi observado que quando Hyperthreading e Turboboost estão ativos, a estimativa de consumo de energia e potência não são equivalentes na execução paralela e sequencial. Além disso, uma das conclusões do trabalho é que o tempo de CPU não é totalmente correlacionado com o consumo energético, por mais que possa servir como uma aproximação.

Logo, é recomendado desativar o turboboost e hyperthreading quando for fatiar o consumo energético utilizando modelos de divisão de potência.

# stress-ng[^9]

stress-ng *(next generation)* é uma ferramenta utilizada para sobrecarregar partições físicas e núcleos de processamento de um computador, permitindo a realização de testes de desempenho e consumo de energia de forma selecionável. 

Os mecanismos de estresse, chamados de estressores, são diversos e cada um utiliza de um ou mais métodos para induzir alterações na performance do sistema. Inicialmente, eles são estruturados para serem executados sob configurações padrão de tamanhos de memória, cache e arquivo, porém essas podem ser alteradas com a função `--maximize`, causando ainda mais estresse.

Ainda, ao adicionar `--rapl` à sua chamada, stress-ng é capaz de fazer leituras do RAPL durante a execução de seus testes. Não apenas isso: também é possível fazer leituras constantes com o comando `--raplstat S`, com S representando o número de segundos entre cada leitura[^10]. Para utilizar essas funções, é necessário que o programa tenha permissões de root, o que requer cautela, pois dessa forma os parâmetros de memória são alterados e o estresse é maximizado.

Finalmente, no Linux, sua instalação pode ser feita a partir do terminal com gerenciadores de pacote ou arquivos `.deb` que, tal como os códigos-fonte, podem ser encontrados no seu [repositório oficial](https://github.com/ColinIanKing/stress-ng).

# Emissões de carbono
**TODO**
Explicar um pouco sobre a natureza dessas emissões e etc. 

  

## ISO medição de carbono
**TODO**
  

# Softwares de estimativa para emissões de carbono

  Colocar a lista de softwares que calculam essas emissões. Cada um terá titulo ##. Falarei sobre como ele faz a conta, como obtém dados da intensidade de carbono, etc. Segue a ISO? coisas assim





  **TODO**
# Referências

[^1]: CADOREL, Emile; SAINGRE, Dimitri. A protocol to assess the accuracy of process-level power models. In: **2024 IEEE International Conference on Cluster Computing (CLUSTER)**. IEEE, 2024. p. 74-84.

[^2]: CODECARBON. **CodeCarbon documentation**. [S. l.], 2026. Disponível em: https://docs.codecarbon.io. Acesso em: 26 abr. 2026.

[^3]: HUBBLO. **Scaphandre documentation**. [S. l.], 2026. Disponível em: [https://hubblo-org.github.io/scaphandre-documentation](https://hubblo-org.github.io/scaphandre-documentation). Acesso em: 22 abr. 2026.

[^4]:  GREEN METRICS TOOL. GMT documentation https://docs.green-coding.io/docs

[^5]: JAY, Mathilde et al. An experimental comparison of software-based power meters: focus on CPU and GPU. In: **2023 IEEE/ACM 23rd International Symposium on Cluster, Cloud and Internet Computing (CCGrid)**. IEEE, 2023. p. 106-118.

[^6]: DIAMOND, Jeremy; STOICO, Vincenzo. What Is the Cost of Energy Monitoring? An Empirical Study on the Overhead of RAPL-Based Tools. arXiv preprint arXiv:2604.26815, 2026.

[^7]: THE KERNEL DEVELOPMENT COMMUNITY. **Power Capping Framework**. Documentação do Kernel Linux. Disponível em: [https://www.kernel.org/doc/html/next/power/powercap/powercap.html](https://www.kernel.org/doc/html/next/power/powercap/powercap.html). Acesso em: 18 maio 2026.

[^8]: BROWN, Len. **powercap: restrict energy meter to root access**. Commit 949dd0104c496fa7c14991a23c03c62e44637e71 no repositório oficial do Kernel Linux. 10 nov. 2020. Disponível em: [https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=949dd0104c496fa7c14991a23c03c62e44637e71](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=949dd0104c496fa7c14991a23c03c62e44637e71). Acesso em: 18 maio 2026.
 
[^9]: KING, Colin Ian. **stress-ng**. [S. l.], 2020. Disponível em: [https://wiki.ubuntu.com/Kernel/Reference/stress-ng](https://wiki.ubuntu.com/Kernel/Reference/stress-ng). Acesso em: 29 maio 2026.

[^10]: KING, Colin Ian. **stress-ng - Debian testing**. [S. l.], 2025. Disponível em: [https://manpages.debian.org/testing/stress-ng/stress-ng.1.en.html](https://manpages.debian.org/testing/stress-ng/stress-ng.1.en.html). Acesso em: 29 maio 2026.

[^11]: THE KERNEL DEVELOPMENT COMMUNITY. **The /proc Filesystem**. The Linux Kernel documentation. [S.l.], [s.d.]. Disponível em: <[https://docs.kernel.org/filesystems/proc.html](https://docs.kernel.org/filesystems/proc.html)>. Acesso em: 15 jun. 2026.

[^12]: LINUX MAN-PAGES PROJECT. **proc_pid_stat(5) - Linux manual page**. Versão 6.18. [S.l.], 8 fev. 2026. Disponível em: <[https://man7.org/linux/man-pages/man5/proc_pid_stat.5.html](https://man7.org/linux/man-pages/man5/proc_pid_stat.5.html)>. Acesso em: 15 jun. 2026.