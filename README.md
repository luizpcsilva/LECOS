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

# Medição energética 

**TODO**
Uma seçao para dar um leve histórico da medição energética no computador e tals. 
começar a enumerar algumas ferramentas importantes que fazem essa medição

## RAPL
- [ ] Algumas informações boas:
"AMD RAPL Characteristics", "Key Takeaways for RAPL Measurements" e "Challenges and Edge Cases" em[^2]**TODO**
## IPMI

**TODO**
## NVML

**TODO**
# Medição Energética de Aplicações Específicas

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

São softwares que consultam sensores em bare-metal via interfaces específicas, para obter o consumo energético total de um dispositivo e, em seguida, consultam métricas de sistema para dividir esse consumo entre as aplicações que estão sendo executadas no dispositivo [^1] .  

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

**TODO**
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

## Green Metrics Tool

**TODO**

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
