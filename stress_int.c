#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Uso: %s <duracao_em_segundos>\n", argv[0]);
        return 1;
    }

    int duration = atoi(argv[1]);
    time_t start_time = time(NULL);
    
    // volatile obriga a cpu a executar as contas e não pular o código morto
    volatile int a = 1;

    while (time(NULL) - start_time < duration) {
        // loop de operações
        for (int i = 0; i < 100000; i++) {
            a += 5;
            a *= 3;
            a /= 2;
            a -= 1;
        }
    }

    return 0;
}