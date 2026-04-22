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

**TODO**
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
# Modelos de Divisão de Potência
**TODO**
- [ ] Explicar diferença modelos de potencia e energia (artigo protocolo dos power models)
- [ ] falar das Limitações conhecidas desses modelos e do erro
- [ ] Listar softwares explorados
	- [ ] SCAPHANDRE
	- [ ] muitos outros

São softwares que utilizam sensores em bare-metal para obter o consumo energético total de um dispositivo e, em seguida, consultam métricas de sistemas para dividir esse consumo entre as aplicações que estão sendo executadas no dispositivo [^1] .  Veremos a seguir alguns softwares para medição energética de aplicações que adotaram essa metodologia como base.





## Scaphandre [^2]

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
## CodeCarbon

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
[^2]: HUBBLO. **Scaphandre documentation**. [S. l.], 2026. Disponível em: [https://hubblo-org.github.io/scaphandre-documentation](https://hubblo-org.github.io/scaphandre-documentation). Acesso em: 22 abr. 2026.

