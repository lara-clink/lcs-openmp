#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <mpi.h>

#ifndef max
#define max(a, b) ((a) > (b) ? (a) : (b))
#endif

#ifndef min
#define min(a, b) ((a) < (b) ? (a) : (b))
#endif

typedef unsigned short mtype;

// Block size for blocking algorithm
#define BLOCK_SIZE 256

// MPI communication tags
#define TAG_BLOCK_DATA 100
#define TAG_RESULT 200

// Reads a sequence from a file
char* read_sequence(const char *filename) {
    FILE *file = fopen(filename, "rt");
    if (!file) {
        printf("Error reading file %s\n", filename);
        exit(1);
    }

    fseek(file, 0L, SEEK_END);
    long size = ftell(file);
    rewind(file);

    char *sequence = calloc(size + 1, sizeof(char));
    if (!sequence) {
        printf("Memory allocation failed for sequence %s\n", filename);
        exit(1);
    }

    int i = 0;
    while (!feof(file)) {
        char ch = fgetc(file);
        if (ch != '\n' && ch != EOF) {
            sequence[i++] = ch;
        }
    }
    sequence[i] = '\0';
    fclose(file);
    return sequence;
}

// NOVA VERSÃO: MPI com distribuição real de blocos e comunicação ponto-a-ponto
// Cada processo só aloca seus blocos locais e troca fronteiras com vizinhos

// Função principal de LCS com distribuição real
int compute_lcs_mpi(const char *A, const char *B, int lenA, int lenB, int rank, int size) {
    int num_blocks_i = (lenA + BLOCK_SIZE - 1) / BLOCK_SIZE;
    int num_blocks_j = (lenB + BLOCK_SIZE - 1) / BLOCK_SIZE;
    int total_blocks = num_blocks_i * num_blocks_j;

    // Distribuir blocos entre processos (round-robin)
    int my_blocks = 0;
    for (int b = 0; b < total_blocks; b++) {
        if (b % size == rank) my_blocks++;
    }

    // Estrutura para guardar os blocos locais
    typedef struct {
        int block_i, block_j;
        mtype *data; // (BLOCK_SIZE+1)x(BLOCK_SIZE+1)
    } Block;
    Block *blocks = malloc(my_blocks * sizeof(Block));
    int block_idx = 0;
    for (int bi = 0; bi < num_blocks_i; bi++) {
        for (int bj = 0; bj < num_blocks_j; bj++) {
            int b = bi * num_blocks_j + bj;
            if (b % size == rank) {
                blocks[block_idx].block_i = bi;
                blocks[block_idx].block_j = bj;
                blocks[block_idx].data = calloc((BLOCK_SIZE+1)*(BLOCK_SIZE+1), sizeof(mtype));
                block_idx++;
            }
        }
    }

    // Inicializar blocos de fronteira (primeira linha/coluna)
    for (int k = 0; k < my_blocks; k++) {
        Block *blk = &blocks[k];
        if (blk->block_i == 0) {
            for (int j = 0; j <= BLOCK_SIZE; j++) blk->data[j] = 0;
        }
        if (blk->block_j == 0) {
            for (int i = 0; i <= BLOCK_SIZE; i++) blk->data[i*(BLOCK_SIZE+1)] = 0;
        }
    }

    // Para cada onda diagonal
    for (int wave = 0; wave < num_blocks_i + num_blocks_j - 1; wave++) {
        // 1. Receber fronteiras necessárias
        for (int k = 0; k < my_blocks; k++) {
            Block *blk = &blocks[k];
            int bi = blk->block_i, bj = blk->block_j;
            if (bi + bj != wave) continue;
            int start_i = bi * BLOCK_SIZE;
            int start_j = bj * BLOCK_SIZE;
            int end_i = min(start_i + BLOCK_SIZE, lenA);
            int end_j = min(start_j + BLOCK_SIZE, lenB);
            // Receber linha de cima
            if (bi > 0) {
                int src = ((bi-1)*num_blocks_j + bj) % size;
                MPI_Recv(&blk->data[0], BLOCK_SIZE+1, MPI_UNSIGNED_SHORT, src, 100, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            }
            // Receber coluna da esquerda
            if (bj > 0) {
                int src = (bi*num_blocks_j + (bj-1)) % size;
                for (int i = 0; i <= BLOCK_SIZE; i++) {
                    MPI_Recv(&blk->data[i*(BLOCK_SIZE+1)], 1, MPI_UNSIGNED_SHORT, src, 101, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
                }
            }
        }
        // 2. Calcular blocos da onda
        for (int k = 0; k < my_blocks; k++) {
            Block *blk = &blocks[k];
            int bi = blk->block_i, bj = blk->block_j;
            if (bi + bj != wave) continue;
            int start_i = bi * BLOCK_SIZE;
            int start_j = bj * BLOCK_SIZE;
            int end_i = min(start_i + BLOCK_SIZE, lenA);
            int end_j = min(start_j + BLOCK_SIZE, lenB);
            for (int i = 1; i <= end_i - start_i; i++) {
                for (int j = 1; j <= end_j - start_j; j++) {
                    int ai = start_i + i - 1;
                    int bj_ = start_j + j - 1;
                    if (A[ai] == B[bj_]) {
                        blk->data[i*(BLOCK_SIZE+1)+j] = blk->data[(i-1)*(BLOCK_SIZE+1)+(j-1)] + 1;
                    } else {
                        blk->data[i*(BLOCK_SIZE+1)+j] = max(
                            blk->data[(i-1)*(BLOCK_SIZE+1)+j],
                            blk->data[i*(BLOCK_SIZE+1)+(j-1)]
                        );
                    }
                }
            }
        }
        // 3. Enviar fronteiras calculadas
        for (int k = 0; k < my_blocks; k++) {
            Block *blk = &blocks[k];
            int bi = blk->block_i, bj = blk->block_j;
            if (bi + bj != wave) continue;
            int end_i = min((bi+1)*BLOCK_SIZE, lenA);
            int end_j = min((bj+1)*BLOCK_SIZE, lenB);
            // Enviar linha de baixo
            if (bi < num_blocks_i-1) {
                int dst = ((bi+1)*num_blocks_j + bj) % size;
                MPI_Send(&blk->data[BLOCK_SIZE*(BLOCK_SIZE+1)], BLOCK_SIZE+1, MPI_UNSIGNED_SHORT, dst, 100, MPI_COMM_WORLD);
            }
            // Enviar coluna da direita
            if (bj < num_blocks_j-1) {
                int dst = (bi*num_blocks_j + (bj+1)) % size;
                for (int i = 0; i <= BLOCK_SIZE; i++) {
                    MPI_Send(&blk->data[i*(BLOCK_SIZE+1)+BLOCK_SIZE], 1, MPI_UNSIGNED_SHORT, dst, 101, MPI_COMM_WORLD);
                }
            }
        }
    }

    // O processo que possui o bloco final retorna o resultado
    int lcs_result = 0;
    for (int k = 0; k < my_blocks; k++) {
        Block *blk = &blocks[k];
        if (blk->block_i == num_blocks_i-1 && blk->block_j == num_blocks_j-1) {
            int ei = min(BLOCK_SIZE, lenA - (num_blocks_i-1)*BLOCK_SIZE);
            int ej = min(BLOCK_SIZE, lenB - (num_blocks_j-1)*BLOCK_SIZE);
            lcs_result = blk->data[ei*(BLOCK_SIZE+1)+ej];
        }
    }
    // Reduzir para rank 0
    int final_result = 0;
    MPI_Reduce(&lcs_result, &final_result, 1, MPI_INT, MPI_MAX, 0, MPI_COMM_WORLD);

    // Liberar memória
    for (int k = 0; k < my_blocks; k++) free(blocks[k].data);
    free(blocks);
    return final_result;
}

int main(int argc, char **argv) {
    int rank, size;
    
    // Initialize MPI
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    
    if (argc < 3) {
        if (rank == 0) {
            printf("Usage: mpirun -np <num_processes> %s fileA fileB\n", argv[0]);
        }
        MPI_Finalize();
        return 1;
    }

    double start = MPI_Wtime();

    // Only rank 0 reads the files and broadcasts to others
    char *seqA = NULL, *seqB = NULL;
    int lenA, lenB;
    
    if (rank == 0) {
        seqA = read_sequence(argv[1]);
        seqB = read_sequence(argv[2]);
        lenA = strlen(seqA);
        lenB = strlen(seqB);
        
        printf("Sequence lengths: A=%d, B=%d\n", lenA, lenB);
    }
    
    // Broadcast sequence lengths
    MPI_Bcast(&lenA, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(&lenB, 1, MPI_INT, 0, MPI_COMM_WORLD);
    
    // Allocate memory for sequences on all processes
    if (rank != 0) {
        seqA = malloc((lenA + 1) * sizeof(char));
        seqB = malloc((lenB + 1) * sizeof(char));
    }
    
    // Broadcast sequences
    MPI_Bcast(seqA, lenA + 1, MPI_CHAR, 0, MPI_COMM_WORLD);
    MPI_Bcast(seqB, lenB + 1, MPI_CHAR, 0, MPI_COMM_WORLD);

    double mid = MPI_Wtime();

    int lcs_length = compute_lcs_mpi(seqA, seqB, lenA, lenB, rank, size);

    double end = MPI_Wtime();

    if (rank == 0) {
        printf("Score: %d\n", lcs_length);
        printf("Total time: %lf seconds\n", end - start);
        printf("LCS computation time: %lf seconds\n", end - mid);
    }

    free(seqA);
    free(seqB);
    
    MPI_Finalize();
    return 0;
}
