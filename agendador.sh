# Aborta em caso de erro
set -e
QTD_EXECUCOES=20

ESTRESSORES=(
    "stress-ng --cpu 1 --cpu-method ackermann -t 30"
    "stress-ng --cpu 1 --cpu-method queens -t 30" 
    "stress-ng --cpu 1 --cpu-method fibonacci -t 30" 
    "stress-ng --cpu 1 --cpu-method float -t 30" 
    "stress-ng --cpu 1 --cpu-method int64 -t 30" 
    "stress-ng --cpu 1 --cpu-method decimal64 -t 30" 
    "stress-ng --cpu 1 --cpu-method double -t 30" 
    "stress-ng --cpu 1 --cpu-method int64float -t 30" 
    "stress-ng --cpu 1 --cpu-method int64double -t 30" 
    "stress-ng --matrix 1 --matrix-method prod -t 30" 
    "stress-ng --cpu 1 --cpu-method rand -t 30" 
    "stress-ng --cpu 1 --cpu-method jmp -t 30" 
) 

for comando in "${ESTRESSORES[@]}"; do
    echo "========================================"
    echo "Executando: $comando"
    echo "========================================"
    
    $comando 
    
    sleep 2
done