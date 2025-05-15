# OddsHunter

OddsHunter é uma plataforma de monitoramento de odds de apostas esportivas que identifica oportunidades de arbitragem estatística entre diferentes casas de apostas.

## Sobre o Projeto

Esta aplicação monitora odds de diversas casas de apostas e identifica oportunidades de arbitragem, onde é possível garantir lucro independentemente do resultado do evento esportivo.

### Funcionalidades

- Monitoramento de odds em tempo real (simulado nesta versão)
- Detecção automática de oportunidades de arbitragem
- Cálculo de stakes proporcionais para maximizar o lucro
- Interface intuitiva com visualização de dados
- Personalização de parâmetros (valor de investimento, limiar de lucro)

## Versão de Demonstração

Esta versão utiliza dados simulados para demonstrar o conceito e a interface do OddsHunter. Em uma versão de produção, seria integrada com APIs reais de odds ou web scrapers para coletar dados em tempo real.

## Como Usar

1. Ajuste o valor total a ser investido na barra lateral
2. Defina o limiar mínimo de lucro para filtrar oportunidades
3. Ative a atualização automática ou clique em "Atualizar Agora"
4. Explore as oportunidades de arbitragem detectadas
5. Visualize as odds por evento e esporte

## Tecnologias Utilizadas

- Python
- Streamlit
- Pandas
- NumPy
- Pillow

## Instalação Local

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Desenvolvido por

Manus AI - 2025
