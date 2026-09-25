#!/bin/bash

#aborta em caso de erro
set -e

#quantidade de execuções por dupla de estressores
QTD_EXECUCOES=5

TIPOS_ESTRESSOR=(
    "stress-ng --cpu"
    "stress-ng --cpu"
    "stress-ng --cpu"
    "stress-ng --cpu"
    "stress-ng --cpu"
    "stress-ng --cpu"
    "stress-ng --cpu"
    "stress-ng --cpu"
    "stress-ng --matrix"
    "stress-ng --cpu"
    "stress-ng --cpu"
)

METODOS_ESTRESSOR=(
    "--cpu-method ackermann"
    "--cpu-method queens"
    "--cpu-method fibonacci"
    "--cpu-method float"
    "--cpu-method int64"
    "--cpu-method double"
    "--cpu-method int64float"
    "--cpu-method int64double"
    "--matrix-method prod"
    "--cpu-method rand"
    "--cpu-method jmp"
)

N_ESTRESSORES=${#TIPOS_ESTRESSOR[@]}

#percorre todas as duplas possíveis (combinação 2 a 2, sem repetição e sem ordem)
for idx1 in $(seq 0 $((N_ESTRESSORES - 2))); do
    for idx2 in $(seq $((idx1 + 1)) $((N_ESTRESSORES - 1))); do

        #extrai o tipo e o método de cada estressor da dupla atual
        TIPO_ESTRESSOR_1="${TIPOS_ESTRESSOR[$idx1]}"
        METODO_ESTRESSOR_1="${METODOS_ESTRESSOR[$idx1]}"
        TIPO_ESTRESSOR_2="${TIPOS_ESTRESSOR[$idx2]}"
        METODO_ESTRESSOR_2="${METODOS_ESTRESSOR[$idx2]}"

        ESTRESSOR_MONTADO_1="$TIPO_ESTRESSOR_1 $METODO_ESTRESSOR_1"
        ESTRESSOR_MONTADO_2="$TIPO_ESTRESSOR_2 $METODO_ESTRESSOR_2"

        echo "====================================================="
        echo "Configurando dupla de estressores para a bateria paralela:"
        echo "P1: $ESTRESSOR_MONTADO_1"
        echo "P2: $ESTRESSOR_MONTADO_2"
        echo "====================================================="

        #atualiza individualmente as variáveis no arquivo valores.sh
        sed -i "s|^export TIPO_ESTRESSOR_1=.*|export TIPO_ESTRESSOR_1=\"$TIPO_ESTRESSOR_1\"|" valores.sh
        sed -i "s|^export METODO_ESTRESSOR_1=.*|export METODO_ESTRESSOR_1=\"$METODO_ESTRESSOR_1\"|" valores.sh
        sed -i "s|^export TIPO_ESTRESSOR_2=.*|export TIPO_ESTRESSOR_2=\"$TIPO_ESTRESSOR_2\"|" valores.sh
        sed -i "s|^export METODO_ESTRESSOR_2=.*|export METODO_ESTRESSOR_2=\"$METODO_ESTRESSOR_2\"|" valores.sh

        #executa as rodadas para a dupla atual
        for i in $(seq 1 $QTD_EXECUCOES); do
            echo "--> Iniciando Rodada $i de $QTD_EXECUCOES para [$ESTRESSOR_MONTADO_1] x [$ESTRESSOR_MONTADO_2]"

            sudo ./protocolo.sh

            sleep 5
        done
    done
done

echo "====================================================="
echo "Todas os testes paralelos foram concluídos!"
echo "====================================================="
