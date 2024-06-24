Explicação da Estrutura
modules/: Este diretório contém diferentes módulos funcionais do seu aplicativo. Cada subdiretório representa um componente ou funcionalidade separada do sistema, como 'dashboard', 'reports', ou 'data'.

dashboard/: Contém scripts específicos para a funcionalidade do dashboard, como visualizações e lógicas auxiliares.
reports/: Contém scripts para gerar relatórios periódicos.
data/: Agrupa funcionalidades relacionadas ao carregamento e processamento de dados.

```app_module/
│
├── modules/
│ ├── init.py
│ ├── dashboard/
│ │ ├── init.py
│ │ ├── main.py # Visualizações principais do dashboard
│ │ └── helpers.py # Funções auxiliares para o dashboard
│ │
│ ├── reports/
│ │ ├── init.py
│ │ ├── weekly_report.py
│ │ └── monthly_report.py
│ │
│ └── data/
│ ├── init.py
│ ├── load_data.py # Módulo para carregamento de dados
│ └── process_data.py # Módulo para processamento de dados
│
├── authentication/
│ ├── init.py
│ └── login.py
│
├── static/
│ ├── images/
│ │ └── logo.png
│ └── styles/
│ └── main.css
│
├── utils/
│ ├── init.py
│ └── utilities.py
│
├── app.py
└── requirements.txt```
