#valores que serão utilizados pelo protocolo.sh:
export N_CORES="6"

#estressores - codigo do stress-ng:
export ESTRESSOR_1=
export ESTRESSOR_2=

#medicoes -> variavel vazia força uma nova medição
export CONSUMO_RESIDUAL=
export BASELINE_P1=
export BASELINE_P2=
#se o baseline acima nao tiver valor, o script irá calcula-lo com os valores abaixo
export CONSUMO_ATIVO_P1=
export CONSUMO_ATIVO_P2=
export CONSUMO_ATIVO_P1_P2=

#configurações
export DO_ISOLAMENTO="0"   #1 para isolar e 0 para nao isolar
export DO_RESFRIAMENTO="0" #1 para aplicar timer de resfriamento entre medições e 0 para não fazer isso
