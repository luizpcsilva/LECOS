#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define N 512 

double a[N][N];
double b[N][N];
double r[N][N];

void inicializar_matrizes() {
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            a[i][j] = (double)(rand() % 100) / 10.0;
            b[i][j] = (double)(rand() % 100) / 10.0;
            r[i][j] = 0.0;
        }
    }
}

void multiplicar_matrizes() {
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            for (int k = 0; k < N; k++) {
                r[i][j] += a[i][k] * b[k][j];
            }
        }
    }
}

int main(int argc, char *argv[]) {

    if (argc != 2) {
        printf("Argumentos de Entrada Incorretos! Passe o tempo da duração do script\n");
        return 1;
    }

    int tempo_limite = atoi(argv[1]);
    
    if (tempo_limite <= 0) {
        printf("O tempo deve ser maior que 0 segundos.\n");
        return 1;
    }

    inicializar_matrizes();

    time_t inicio = time(NULL);

    while (time(NULL) - inicio < tempo_limite) {
        multiplicar_matrizes();
    }

    return 0;
}