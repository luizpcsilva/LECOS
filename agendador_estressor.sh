#!/bin/bash

#aborta em caso de erro
set -e

#quantidade de execuções por estressor
QTD_EXECUCOES=15

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

for idx in "${!TIPOS_ESTRESSOR[@]}"; do
    
    #extrai o tipo e o método usando o índice atual de ambas as listas
    TIPO_ESTRESSOR_1="${TIPOS_ESTRESSOR[$idx]}"
    METODO_ESTRESSOR_1="${METODOS_ESTRESSOR[$idx]}"

    ESTRESSOR_MONTADO="$TIPO_ESTRESSOR_1 $METODO_ESTRESSOR_1"

    echo "====================================================="
    echo "Configurando estressor para a bateria sequencial:"
    echo "Tipo:   $TIPO_ESTRESSOR_1"
    echo "Método: $METODO_ESTRESSOR_1"
    echo "Unido:  $ESTRESSOR_MONTADO"
    echo "====================================================="

    #atualiza individualmente as variáveis no arquivo valores.sh
    sed -i "s|^export TIPO_ESTRESSOR_1=.*|export TIPO_ESTRESSOR_1=\"$TIPO_ESTRESSOR_1\"|" valores.sh
    sed -i "s|^export METODO_ESTRESSOR_1=.*|export METODO_ESTRESSOR_1=\"$METODO_ESTRESSOR_1\"|" valores.sh

    #executa as rodadas para o estressor atual
    for i in $(seq 1 $QTD_EXECUCOES); do
        echo "--> Iniciando Rodada $i de $QTD_EXECUCOES para [$ESTRESSOR_MONTADO]"
        
        sudo ./protocolo.sh

        sleep 5
    done
done

echo "====================================================="
echo "Todas as $QTD_EXECUCOES baterias sequenciais foram concluídas!"
echo "====================================================="