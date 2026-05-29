#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Uso: %s <duracao_em_segundos>\n", argv[0]);
        return 1;
    }

    int duration = atoi(argv[1]);
    time_t start_time = time(NULL);
    
    volatile double a = 2.0;

    while (time(NULL) - start_time < duration) {
        // loop das operações
        for (int i = 0; i < 100000; i++) {
            a = sqrt(a * 2.5);
            a = sin(a);
            a = a + 1.5;
        }
    }

    return 0;
}