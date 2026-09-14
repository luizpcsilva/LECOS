#valores que serão utilizados pelo protocolo.sh:
export N_CORES="6"
export T_DURACAO="-t 30"

#estressores - codigo do stress-ng:
#OBS: escreva apenas stress-ng --tipo_do_estresse. oculte a qtd de núcleos e a duração do estresse
export TIPO_ESTRESSOR_1=
export TIPO_ESTRESSOR_2=

#para o estressor utilizado no consumo residual, pode escrever o comando todo (sem o taskset, apenas stress-ng)
export ESTRESSOR_RESIDUAL="stress-ng --cpu 1 -t 30"

#medicoes -> variavel vazia força uma nova medição
export CONSUMO_RESIDUAL=
export BASELINE_P1=1
export BASELINE_P2=1
#se o baseline acima nao tiver valor, o script irá calcula-lo com os valores abaixo
export CONSUMO_ATIVO_P1=1
export CONSUMO_ATIVO_P2=1
export CONSUMO_ATIVO_P1_P2=1

export CONSUMO_SCAPHANDRE=

#configurações
export DO_ISOLAMENTO="1"   #1 para isolar e 0 para nao isolar
export DO_RESFRIAMENTO="1" #1 para aplicar timer de resfriamento entre medições e 0 para não fazer isso
