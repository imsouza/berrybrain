
imsouza.github.io
Definições do Aprendizado de Máquina
Mateus Almeida
13–17 minutes

Escrito por Mateus Almeida
em  1 Maio 2023
11 min de leitura

Machine Learning

Birds

O Machine Learning (aprendizado de máquina) é o ramo da Inteligência Artificial que estuda e desenvolve sistemas computacionais capazes de aprender, prever e identificar padrões a partir de dados inseridos. É uma forma de inteligência artificial que incorpora a estratégia de aprendizado e previsão a partir de dados.

Existem vários tipos de aprendizado de máquina, como o aprendizado supervisionado, que analisa dados rotulados para prever novas saídas, e o aprendizado não supervisionado, que encontra padrões e estruturas nos dados. Neste artigo, vamos explorar os conceitos fundamentais do aprendizado de máquina, incluindo os diferentes tipos de aprendizado, técnicas de avaliação de modelos, técnicas de otimização e seus principais algoritmos.
Aprendizado Supervisionado

A aprendizagem supervisionada é um ramo do aprendizado de máquina que envolve o treinamento de um modelo com um conjunto de dados rotulados. O objetivo é aprender a relação entre as entradas e as saídas esperadas, de forma que o modelo possa prever corretamente as saídas para novas entradas. Alguns exemplos de algoritmos de aprendizado supervisionado são regressão linear, regressão logística, árvores de decisão e redes neurais.

Este aprendizado é amplamente utilizado em problemas de classificação e regressão. Ele é usado quando se tem dados rotulados e se quer prever novas saídas. O modelo é treinado com um conjunto de dados rotulados e, em seguida, é testado com um conjunto de dados não rotulados para avaliar o seu desempenho. O objetivo é encontrar um modelo que generalize bem para novos dados.

Alguns exemplos de algoritmos são:

    k-Nearest Neighbors
    Support Vector Machines (SVMs)
    Linear regression
    Logistic regression
    Decision Trees
    Random Forests

Aprendizado Não Supervisionado

O aprendizado não supervisionado é uma técnica de aprendizado de máquina em que o modelo é treinado com um conjunto de dados não rotulados. O objetivo é encontrar padrões e estruturas nos dados, de forma que o modelo possa agrupar os dados em categorias ou reduzir a dimensionalidade dos dados.

Este aprendizado é usado quando se quer encontrar padrões e estruturas nos dados. Ele é amplamente utilizado em problemas de clusterização e redução de dimensionalidade. O modelo é treinado com um conjunto de dados não rotulados e, em seguida, é testado com um conjunto de dados não rotulados para avaliar o seu desempenho. O objetivo é encontrar uma estrutura nos dados que possa ser usada para análise posterior.
Clusterização

A clusterização é uma técnica de aprendizado não supervisionado que permite agrupar dados em clusters ou grupos com base em suas características. É útil para explorar conjuntos de dados sem a necessidade de rótulos ou categorias pré-definidas.
Detecção de anomalia

A detecção de anomalia é outra técnica de aprendizado não supervisionado que permite identificar padrões incomuns ou anômalos nos dados. É útil para detectar fraudes, falhas em sistemas e outras anomalias.
Redução de dimensionalidade

A redução de dimensionalidade é uma técnica de aprendizado de máquina que permite reduzir a quantidade de variáveis em um conjunto de dados, mantendo as informações mais importantes. É útil para simplificar a análise de dados e melhorar o desempenho dos modelos de aprendizado de máquina.

Alguns exemplos de algoritmos não supervisionados são:

    K-Means
    DBSCAN
    Hierarchical Cluster Analysis (HCA)
    One-class SVM
    Isolation Forest
    PCA
    t-SNE

Aprendizado semi-supervisionado

O aprendizado semi supervisionado é uma técnica de aprendizado de máquina que combina elementos do aprendizado supervisionado e não supervisionado. Ele é usado quando se tem um conjunto de dados com poucos dados rotulados e muitos dados não rotulados. O objetivo é usar os dados rotulados para treinar o modelo e, em seguida, usar os dados não rotulados para melhorar o desempenho do modelo.

Existem várias técnicas de aprendizado semi supervisionado, como a propagação de rótulos, a co-regularização e a mistura de modelos. O aprendizado semi supervisionado é útil em problemas em que é difícil obter dados rotulados suficientes para treinar um modelo de aprendizado de máquina. Ele permite que o modelo use informações dos dados não rotulados para melhorar o seu desempenho.
Aprendizado por reforço

O aprendizado por reforço é uma técnica de aprendizado de máquina em que um agente aprende a tomar ações em um ambiente para maximizar uma recompensa acumulada ao longo do tempo. O agente aprende a atingir uma meta em um ambiente incerto, recebendo feedback em forma de recompensas ou penalidades. O objetivo é maximizar a recompensa acumulada ao longo do tempo, aprendendo a tomar ações que levem a recompensas maiores.

Esta técnica é usada em problemas em que é difícil definir uma função de custo ou em que a função de custo é desconhecida. Ele é usado em jogos, robótica, finanças e outras áreas. O aprendizado por reforço é uma técnica poderosa de aprendizado de máquina que permite que os agentes aprendam a tomar decisões em ambientes complexos e incertos.
Conjunto de treino, validação e teste

O conjunto de treinamento, validação e teste é uma técnica de avaliação de modelos de aprendizado de máquina. O conjunto de treinamento é usado para treinar o modelo, o conjunto de validação é usado para ajustar os hiperparâmetros do modelo e o conjunto de teste é usado para avaliar o desempenho final do modelo.

A divisão dos dados em conjuntos de treino, validação e teste é uma técnica comum em problemas de aprendizado supervisionado, em que o modelo é treinado com um conjunto de dados rotulados e, em seguida, é testado com um conjunto de dados não rotulados para avaliar o seu desempenho. É importante ter um conjunto de teste separado para avaliar o desempenho do modelo em dados não vistos durante o treinamento.
Overfitting e underfitting

O overfitting e o underfitting são problemas comuns em modelos de aprendizado de máquina. O overfitting ocorre quando o modelo se ajusta muito bem aos dados de treinamento, mas não generaliza bem para novos dados.

https://imgur.com/vgybW40.png

O underfitting ocorre quando o modelo é muito simples e não consegue capturar a complexidade dos dados, ou seja, o modelo não treinou o suficiente. Para evitar o overfitting e o underfitting, é importante ajustar os hiperparâmetros do modelo e usar técnicas de regularização. Esses são problemas comuns em modelos de aprendizado de máquina e podem levar a resultados ruins.
Regularização

Essa técnica adiciona uma penalização em modelos que são muito complexos ou que dão muito destaque para uma característica específica. Ela prefere modelos mais simples uma vez que são melhores para generalizar.

    A regularização é usada para evitar o overfitting, adicionando uma penalidade aos parâmetros do modelo.

Métricas de avaliação

As métricas de avaliação são usadas para avaliar o desempenho de modelos de aprendizado de máquina.
Classificação

Algumas das principais métricas de avaliação para problemas de classificação são:

    Acurácia: mede a proporção de exemplos classificados corretamente.
    Sensibilidade (recall ou revocação): mede a proporção de exemplos positivos que foram corretamente identificados.
    Especificidade: mede a proporção de exemplos negativos que foram corretamente identificados.
    Precisão: mede a proporção de exemplos positivos classificados corretamente.
    F-score: é uma média harmônica da precisão e recall.
    Curva ROC: é uma curva que mostra a taxa de verdadeiros positivos em relação à taxa de falsos positivos.

Regressão

Em problemas de regressão, as métricas de avaliação comuns incluem:

    Erro médio absoluto (MAE): mede a média das diferenças absolutas entre as previsões e os valores reais.
    Erro médio quadrático (MSE): mede a média das diferenças quadráticas entre as previsões e os valores reais.
    Raiz do erro médio quadrático (RMSE): é a raiz quadrada do MSE.
    Coeficiente de determinação (R²): mede a proporção da variância nos dados que é explicada pelo modelo.

Loss

A loss function é outra métrica que mede a diferença entre a saída prevista e a saída real. Ela é usada para ajustar os parâmetros do modelo durante o treinamento. Algumas das loss functions comuns são:

    Entropia cruzada binária: usada em problemas de classificação binária.
    Entropia cruzada categórica: usada em problemas de classificação multiclasse.
    Erro médio quadrático: usada em problemas de regressão.

A escolha da métrica de avaliação e da loss function depende do tipo de problema de aprendizado de máquina e dos objetivos do modelo. É importante escolher as métricas corretas para avaliar o desempenho do modelo e ajustar a loss function para obter um modelo com bom desempenho.
Hyperparâmetro X parâmetro

Em aprendizado de máquina, os parâmetros são os valores que o modelo aprende durante o treinamento, enquanto os hiperparâmetros são os valores que controlam o processo de treinamento do modelo. Os parâmetros são ajustados pelo modelo durante o treinamento para minimizar a função de custo. Eles são os pesos e vieses que o modelo usa para fazer previsões.

Os hiperparâmetros são definidos antes do treinamento e controlam o processo de treinamento, como a taxa de aprendizado, o número de épocas e o tamanho do batch. Eles são definidos pelo usuário e afetam o desempenho do modelo. A escolha dos hiperparâmetros corretos é importante para obter um modelo com bom desempenho.

O ajuste de hiperparâmetros é o processo de encontrar os melhores valores para os hiperparâmetros do modelo. Ele é feito por meio de tentativa e erro ou por meio de técnicas mais avançadas, como o GridSearch ou o RandomSearch. O ajuste de hiperparâmetros é uma parte importante do processo de treinamento de modelos de aprendizado de máquina.
Otimização

A otimização é uma técnica importante em aprendizado de máquina que permite ajustar os parâmetros de um modelo para melhorar o seu desempenho. O gradiente descendente é um exemplo bem famoso de algoritmo de otimização que ajusta os parâmetros de um modelo para minimizar uma função de custo ou perda.

Ele funciona calculando o gradiente da função de custo em relação aos parâmetros do modelo e, em seguida, ajustando os parâmetros na direção oposta ao gradiente, ou seja, “descendo” cada vez mais até alcançar o ponto mais baixo possível, também chamado de mínimo global, sendo esse mínimo global seu objetivo.

https://imgur.com/IpnpCdj.png

O tamanho do passo (conhecido como taxa de aprendizagem ou learning rate) que devemos tomar a cada iteração é um dos hiperparâmetros mais importantes a ser decidido quando se está treinando um modelo, pois, se o seu valor for muito pequeno, o progresso pode ser muito devagar, e caso seja muito grande, podemos até mesmo ter uma piora na perda.

Existem três tipos de gradiente descendente: batch, minibatch e estocástico.
Batch

O gradiente descendente batch usa todo o conjunto de dados para calcular o gradiente e atualizar os parâmetros.
Estocástico

O gradiente descendente estocástico usa apenas um exemplo de cada vez para calcular o gradiente e atualizar os parâmetros.
Minibatch

O gradiente descendente minibatch usa um pequeno conjunto de dados para calcular o gradiente e atualizar os parâmetros. O gradiente descendente estocástico e minibatch são mais rápidos do que o batch, mas podem ser menos precisos. A escolha do tipo de gradiente descendente depende do tamanho do conjunto de dados e da complexidade do modelo.
Conclusão

Neste artigo foram apresentados os principais conceitos do aprendizado de máquina e suas técnicas, incluindo o aprendizado supervisionado, não supervisionado, semi supervisionado e por reforço. Foram discutidas as métricas de avaliação e as funções de perda comuns usadas para avaliar o desempenho do modelo e ajustar os parâmetros do modelo durante o treinamento. Em geral, o aprendizado de máquina é uma área em constante evolução e oferece muitas oportunidades para aplicação em diversas áreas, incluindo a mineração de dados, diagnósticos médicos, biometria, extração de conhecimento, identificação de exceções dos dados de entrada, entre outras.
Referências

Didática Tech. Entenda: Aprendizado Supervisionado vs Não Supervisionado

TIBCO. O que é aprendizagem supervisionada?

Betrybe. Aprendizado supervisionado: 7 exemplos sobre como aplicar

FourWeekMBA. Aprendizado supervisionado versus não supervisionado

Desmistificando termos Machine Learning: Tipos de Aprendizado

O que é regularização L1/L2?

Principais conceitos por trás do Machine Learning
