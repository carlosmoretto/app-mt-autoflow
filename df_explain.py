
#Debugar:  
import pdb; pdb.set_trace()


import pandas as pd

# Criando um DataFrame de exemplo
data = {
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [28, 34, 29],
    'city': ['New York', 'San Francisco', 'Los Angeles']
}

df = pd.DataFrame(data)

# Imprimindo o DataFrame
print(df)

# Primeiras 5 linhas do DataFrame (padrão)
print(df.head())

# Primeiras 3 linhas do DataFrame
print(df.head(3))

# Últimas 5 linhas do DataFrame (padrão)
print(df.tail())

# Últimas 2 linhas do DataFrame
print(df.tail(2))

# Informações gerais sobre o DataFrame
print(df.info())

# Estatísticas descritivas para colunas numéricas
print(df.describe())

# Visualizar coluna 'name'
print(df['name'])

# Visualizar múltiplas colunas
print(df[['name', 'city']])

# Exportando para CSV
df.to_csv('data.csv', index=False)

# Exportando para Excel
df.to_excel('data.xlsx', index=False)

# Código Completo de Exemplo

import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import HTML

# Criando um DataFrame de exemplo
data = {
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [28, 34, 29],
    'city': ['New York', 'San Francisco', 'Los Angeles']
}

df = pd.DataFrame(data)

# Visualização básica
print("DataFrame Original:")
print(df)

# Primeiras linhas
print("\nPrimeiras linhas:")
print(df.head())

# Informações gerais
print("\nInformações gerais:")
print(df.info())

# Estatísticas descritivas
print("\nEstatísticas descritivas:")
print(df.describe())

# Visualizando colunas específicas
print("\nColunas específicas:")
print(df[['name', 'city']])

# Visualizando em Jupyter Notebook (apenas digitando 'df' no notebook)
# df

# Estilizando o DataFrame
print("\nDataFrame Estilizado:")
styled_df = df.style.highlight_max(axis=0)
display(styled_df)

# Exportando para CSV
df.to_csv('data.csv', index=False)

# Criando um gráfico de barras das idades
print("\nGráfico de Barras:")
df['age'].plot(kind='bar')
plt.show()


import pandas as pd
import numpy as np

# Criando um DataFrame de exemplo
data = {
    'payable_account.expected_deposit_account_id': [123, np.nan, 456, np.nan, 789]
}

df = pd.DataFrame(data)

# Preenchendo NaNs com um valor específico, por exemplo, -1
df['payable_account.expected_deposit_account_id'] = df['payable_account.expected_deposit_account_id'].fillna(-1).astype(int)

print("DataFrame após preenchimento e conversão para int:")
print(df)