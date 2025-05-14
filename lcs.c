#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>

#ifndef max
#define max(a, b) ((a) > (b) ? (a) : (b))
#endif

typedef unsigned short mtype;

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

// Computes LCS with anti-diagonal parallelization
int compute_lcs_diagonal(const char *A, const char *B, int lenA, int lenB) {
    mtype **dp = malloc((lenA + 1) * sizeof(mtype*));
    for (int i = 0; i <= lenA; i++) {
        dp[i] = calloc(lenB + 1, sizeof(mtype));
    }

    // Initialize first row and column
    for (int i = 0; i <= lenA; i++) dp[0][i] = 0;
    for (int i = 0; i <= lenB; i++) dp[i][0] = 0;

    // Compute LCS using anti-diagonal parallelization
    for (int d = 2; d <= lenA + lenB; d++) {
        #pragma omp parallel for
        for (int i = 1; i <= lenA; i++) {
            int j = d - i;
            if (j < 1 || j > lenB) continue;

            if (A[i - 1] == B[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
    }

    int result = dp[lenA][lenB];

    // Cleanup
    for (int i = 0; i <= lenA; i++) {
        free(dp[i]);
    }
    free(dp);

    return result;
}

int main(int argc, char **argv) {
    if (argc < 3) {
        printf("Usage: %s fileA fileB [num_threads]\n", argv[0]);
        return 1;
    }

    if (argc == 4) {
        omp_set_num_threads(atoi(argv[3]));
    }

    double start = omp_get_wtime();

    char *seqA = read_sequence(argv[1]);
    char *seqB = read_sequence(argv[2]);
    int lenA = strlen(seqA), lenB = strlen(seqB);

    double mid = omp_get_wtime();

    int lcs_length = compute_lcs_diagonal(seqA, seqB, lenA, lenB);

    double end = omp_get_wtime();

    printf("Score: %d\n", lcs_length);
    printf("Total time: %lf seconds\n", end - start);
    printf("LCS computation time: %lf seconds\n", end - mid);

    free(seqA);
    free(seqB);

    return 0;
}
