# LCS (Longest Common Subsequence) - Implementação Paralela

Este repositório contém uma implementação paralela do algoritmo de Longest Common Subsequence (LCS), bem como scripts para testes, geração de entradas e avaliação de desempenho.

## Estrutura do Projeto

- **lcs.c**: Implementação do código paralelo
- **lcs_original.c**: Adaptação do código fornecido pelo professor, modificado para aceitar qualquer entrada genérica
- **experiment_config.py**: Configuração dos experimentos
- **generate_test_files.py**: Script para gerar arquivos de teste de diferentes tamanhos
- **lcs_benchmark.py**: Script para execução dos experimentos, geração de gráficos, tabela CSV e JSON com dados experimentais
- **test_compare.py**: Script de teste para verificar se as saídas do código sequencial original (lcs_original.c) são consistentes com as saídas do código paralelo implementado (lcs.c)
- **requirements.txt**: Lista de dependências Python
- **Makefile**: Facilita a compilação e limpeza do projeto

## Instalação e Compilação

Para compilar o programa principal, a versão original e instalar as dependências do Python:

```bash
make
```

Este comando compilará:
- O programa principal (`lcs`)
- A versão original (`lcs_original`)
- Instalará as dependências Python listadas em `requirements.txt`

## Geração de Arquivos de Teste

Para gerar os arquivos de entrada para testes:

```bash
python3 generate_test_files.py
```

## Execução

Para executar o algoritmo LCS, use o seguinte formato:

```bash
./lcs <entrada1> <entrada2> <número_de_threads>
```

Exemplo:

```bash
./lcs 20000.in 20000.in2 1
```

## Experimentos

Para executar os experimentos de benchmark:

```bash
python3 lcs_benchmark.py
```

Este script irá executar os experimentos configurados, gerar gráficos, uma tabela CSV e um arquivo JSON com os resultados.

## Limpeza

Para remover arquivos compilados e gerados:

```bash
make clean
```

Este comando removerá:
- Arquivos objeto (*.o)
- Executáveis (lcs, lcs_original)
- Diretórios de resultados de experimentos (experiment_results_*)
- Arquivos de entrada gerados (*.in, *.in2)
