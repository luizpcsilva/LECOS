# Aborta em caso de erro
set -e
QTD_EXECUCOES=15

ESTRESSORES=(
    "stress-ng --cpu 1 --cpu-method ackermann -t 30"
    "stress-ng --cpu 1 --cpu-method queens -t 30" 
    "stress-ng --cpu 1 --cpu-method fibonacci -t 30" 
    "stress-ng --cpu 1 --cpu-method float -t 30" 
    "stress-ng --cpu 1 --cpu-method int64 -t 30" 
    "stress-ng --cpu 1 --cpu-method double -t 30" 
    "stress-ng --cpu 1 --cpu-method int64float -t 30" 
    "stress-ng --cpu 1 --cpu-method int64double -t 30" 
    "stress-ng --matrix 1 --matrix-method prod -t 30" 
    "stress-ng --cpu 1 --cpu-method rand -t 30" 
    "stress-ng --cpu 1 --cpu-method jmp -t 30" 
) 

for comando in "${ESTRESSORES[@]}"; do
    echo "====================================================="
    echo "Preparando ambiente para o estressor residual:"
    echo "$comando"
    echo "====================================================="

    # altera dinamicamente o arquivo valores.sh a expressão busca a linha que começa com export ESTRESSOR_RESIDUAL= e a substitui inteira
    sed -i "s/^export ESTRESSOR_RESIDUAL=.*/export ESTRESSOR_RESIDUAL=\"$comando\"/" valores.sh

    # percorre as execuções para o estressor da iteração atual
    for i in $(seq 1 $QTD_EXECUCOES); do
        echo "iniciando teste $i de $QTD_EXECUCOES para [$comando]"
        
        sudo ./protocolo.sh
        
        #pausa de segurança para garantir a liberação de recursos entre as rodadas
        sleep 5
    done
done

echo "====================================================="
echo "Todas as baterias de testes foram finalizadas!"
echo "====================================================="