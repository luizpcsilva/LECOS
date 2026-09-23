# LECOS
> Laboratório de Estudos em Computação Sustentável
---

O seguinte repositório contém os algoritmos necessários para executar o protocolo experimental proposto por:

* CADOREL, Emile; SAINGRE, Dimitri. A protocol to assess the accuracy of process-level power models. In: 2024 IEEE International Conference on Cluster Computing (CLUSTER). IEEE, 2024. p. 74-84

Inicialmente, utilizaremos um ambiente bare-metal com Ubuntu Server e processador 12th Gen Intel(R) Core(TM) i5-12400

# Passos para a execução do protocolo:

**Leia Antes de Executar os Scripts**: Durante a execução do isolamento da máquina, o wifi/tailscale é desativado. Assim, nunca execute o script diretamente no terminal do ssh, pois isso irá causar o encerramento da sessão e a conexão será perdida, sem que a placa de rede e os serviços de rede sejam reativados. Siga [esses passos](#obs-sessões-de-terminais-persistentes) para a execução em ambiente ssh.

## 0. Configurações Iniciais:

### 1. Clone o repositório
```bash
git clone --single-branch --branch code/protocolo-avaliacao-power-models https://github.com/luizpcsilva/LECOS.git
```

### 2. Dê permissão de execução para protocolo.sh
```bash
cd LECOS
sudo chmod +x protocolo.sh
```

## 1. Isolamento da Máquina

Para diminuir o ruído de fundo do sistema, é importante implementar medidas como o desligamento de atualizações de sistema, controle de temperatura, etc. As boas práticas de medição identificadas estão descritas [aqui - seção 1.3.4](https://doi.org/10.5753/sbc.20175.9.1)

Assim, desenvolvemos o script bash `protocolo.sh`. O script executa os seguintes passos:

### Desligamento de serviços de fundo:

Os seguintes serviços do SO são desligados para evitar interrupções de sistema durante a medição de energia:

1. `cron`: Evita a execução de tarefas agendadas do SO e rotinas de manutenção inesperadas.
2. `snapd` e `snapd.socket`: Interrompem a verificação e o download de atualizações automáticas do SO.
4. `ModemManager`, `wpa_supplicant` e `tailscaled`: Silencial o gerenciamento de conexões de rede e Wi-Fi, garantindo que o sistema não gaste energia tentando reestabelecer conexões derrubadas
5. `udisks2`, `upower` e `multipathd`: Desativam o monitoramento dos discos e de energia.
9. `unattended-upgrades`: Bloqueia a instalação silenciosa de pacotes de segurança.

### Desligamento físico da placa de rede:

Para o desligamento total da conexão wifi, as placas físicas devem ser desligadas. O script `isolamento.sh` as identifica por meio do comando `INTERFACES_FISICAS=$(ls /sys/class/net/ | grep -E '^(en|wl|eth)')` e, em seguida, as desativa por meio de um loop for.

### Desligamento do Turboboost e Hyperthreading
A desativação do Turbo Boost impede que a frequência do processador exceda o valor base, estabilizando o consumo. A desativação do Hyper‑Threading garante que cada processo seja alocado a um núcleo físico exclusivo.
```bash
echo "1" > /sys/devices/system/cpu/intel_pstate/no_turbo   # desativa Turbo Boost
echo off > /sys/devices/system/cpu/smt/control              # desativa Hyper‑Threading
```

### Restauração Automática:
A função `restaurar_ambiente()` é chamada ao final do script (ou em caso de erro/SIGINT) para:
1. Religar as placas de rede.
2. Reativar o Turbo Boost e o Hyper‑Threading.
3. Reiniciar os serviços desligados.

### OBS: Sessões de Terminais Persistentes

Como os scripts serão executados via ssh, é importante que sejam utilizadas sessões de terminais persistentes para que, ao interromper os serviços de rede, a execução do script não seja abortada pelo fim da conexão ssh.

Assim, deve-se utilizar ferramentas conhecidas como multiplexadores de terminal. No caso, utilizaremos o `tmux`. Execute `tmux` no terminal ao logar no ssh para abrir o terminal tmux, identificado por uma barra verde no canto inferior da tela. Utilize-o como um terminal comum.

Caso saia da sessão, use o comando `tmux ls` para listar as sessões abertas e `tmux attach-session -t [numero da sessão]` para relogar

## Medição idle
Executa scripts/medicao-idle.py por 30 segundos, com amostragem de 1 segundo. O script:

1. Lê o contador RAPL /sys/class/powercap/intel-rapl/subsystem/intel-rapl:0/energy_uj a cada segundo.

2. Salva os dados em testes/idle/idle_YYYYMMDD_HHMMSS.csv.

3. Chama scripts/calculo-melhor-media-e-std.py para selecionar a janela de 10 s com menor desvio padrão e retornar a média de potência (em watts). A média definitiva é salva em `log.csv`.

Esse valor é usado apenas para referência. O consumo residual é medido separadamente e contém o idle.

## Medição Residual

Executa scripts/medicao-estressor.py com o comando:

```bash
taskset -c 0 stress-ng --cpu 1 -t 30
```

Isso gera carga em apenas um núcleo (core 0) por 30 s. O script mede o consumo total e extrai a melhor média (janela de 10 s com menor desvio padrão). Esse valor é chamado `CONSUMO_RESIDUAL` e corresponde a R (consumo total com um único núcleo ativo, incluindo o idle).

O valor é salvo no log.csv pelo script scripts/salvar-residual.py

## Medição das Aplicações Isoladas
Para cada aplicação a ser avaliada (ex: stress-ng --cpu 6, stress-ng --matrix 6), o script:

1. Executa o estressor por 30 s usando scripts/medicao-estressor.py.
2. Obtém o consumo total médio (CONSUMO_TOTAL_P1, CONSUMO_TOTAL_P2).
3. Calcula o consumo ativo com scripts/calculo-consumo-ativo.py:
```
CONSUMO_ATIVO_P1 = CONSUMO_TOTAL_P1 - CONSUMO_RESIDUAL
CONSUMO_ATIVO_P2 = CONSUMO_TOTAL_P2 - CONSUMO_RESIDUAL
``` 

## Medição Paralela
Executa as duas aplicações simultaneamente, mas com metade da quantidade de workes cada para evitar concorrência:

```bash
sudo stress-ng --cpu 3 -t 30
sudo stress-ng --matrix 3 -t 30
``` 

O consumo total paralelo (`CONSUMO_TOTAL_P1_P2`) é medido e o consumo ativo paralelo é calculado subtraindo o residual.

## Cálculo do Baseline
O script scripts/calculo-baseline.py recebe:
* `CONSUMO_ATIVO_P1_P2`: consumo ativo total no cenário paralelo.
* `CONSUMO_ATIVO_P1` e `CONSUMO_ATIVO_P2`: consumos ativos individuais.

E calcula a divisão proporcional esperada, com base na equação 3 do artigo:

```
baseline_p1 = consumo_ativo_paralelo * (consumo_ativo_p1 / (consumo_ativo_p1 + consumo_ativo_p2))
baseline_p2 = consumo_ativo_paralelo * (consumo_ativo_p2 / (consumo_ativo_p1 + consumo_ativo_p2))
```
Esses valores são impressos e salvos no `log.csv`.

## Medição com o Scaphandre

Roda **o mesmo cenário paralelo** da etapa anterior (`ESTRESSOR_1_PAR` e `ESTRESSOR_2_PAR`),
desta vez com o Scaphandre medindo, para obter o consumo **estimado pelo modelo** (`Ce`) de
cada aplicação. É contra esses valores que o baseline será comparado.

O `scripts/medicao-scaphandre.py` sobe o contêiner do Scaphandre com o **exportador JSON**,
dispara os dois estressores e agrega o consumo de cada um:

```bash
docker run --rm --name scaphandre --privileged \
    -v /sys/class/powercap:/sys/class/powercap \
    -v /proc:/proc \
    hubblo/scaphandre json -s 1 --max-top-consumers 50 --resources
```

Decisões que sustentam a validade da medição:

* **Exportador JSON, não prometheus.** No exportador prometheus a janela de medição é definida
  por *quem faz a requisição*: a primeira volta zerada, um segundo consumidor desalinha as
  demais e, sob carga total, o contêiner é preterido e o contador congela. O exportador JSON
  amostra no próprio timer (`--step`), então o consumidor sai do caminho crítico.
* **Sem `-f`**, o relatório sai no `stdout` do contêiner. O script acumula em memória e só
  grava o CSV depois que os estressores terminam — nada é escrito em disco dentro da janela.
* **`--max-top-consumers 50`**: o default de 10 cortaria workers do `stress-ng` (3+3 workers
  mais os dois pais já são 8, e há daemons disputando o ranking).
* **Sem `--process-regex`**: preservar todos os consumidores mantém a coluna `soma_todos_uw`,
  que é o que testa a premissa da Equação 4 (o modelo divide o *total*?).
* **Separação por árvore de PIDs**, não por `cmdline`: o `stress-ng` apaga o método dos seus
  workers, e em 10 dos 12 testes do artigo os dois lados são `--cpu-method` com string
  idêntica. Filtrar por label seria impossível.

A série bruta vai para `testes/scaphandre/<cenário>-<timestamp>.csv`. Além de `ce_p1_uw` e
`ce_p2_uw`, o CSV traz colunas de diagnóstico:

| Coluna | Para que serve |
|---|---|
| `socket0_uw` | domínio *package* — **mesma base** que o protocolo lê do RAPL em `intel-rapl:0` |
| `host_uw` | consumo do host; é PSYS quando a placa expõe esse domínio |
| `soma_todos_uw` | `soma_todos / socket0` testa a premissa da Equação 4 |
| `cpu_p1_pct` / `cpu_p2_pct` | se `ce_p1/ce_p2 == cpu_p1/cpu_p2`, está demonstrado que a chave de rateio é tempo de CPU |
| `delta_t_s` | espaçamento entre amostras; desvios indicam que o agente foi preterido |
| `n_pids_p1` / `n_pids_p2` | quantos PIDs de cada árvore entraram na amostra |

Como nas demais etapas, a média sai da janela de 10 amostras mais estável — aqui, a de menor
desvio padrão **da fração** `ce_p1 / (ce_p1 + ce_p2)`, não do total: numa deriva
anticorrelacionada o total fica plano justamente quando a divisão muda mais rápido.

## TODO

O script ainda não implementa:

1. Coleta de estimativas do PowerAPI para comparação com o baseline. A do Scaphandre já
está implementada em `scripts/medicao-scaphandre.py`, via exportador JSON.

1. Aplicação da Equação 5 (cálculo do erro)

2. Alinhar o protocolo às práticas mais recentes de validação (ver Bellal et al., 2025) -> Fixação da frequência da CPU (governor userspace), recomendada para eliminar variações de DVFS -> Desativação de C‑states (estados ociosos profundos), que afetam o consumo do pacote -> Variação de co‑runners e cargas memory‑bound..

    

