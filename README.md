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
- Integração segura com MongoDB Atlas para armazenamento de dados
- Sistema de cache para melhorar performance e resiliência
- Fallback para dados locais em CSV quando MongoDB não está disponível

## Integração com MongoDB Atlas

A aplicação suporta integração com MongoDB Atlas para armazenamento e recuperação de dados de odds. As credenciais são gerenciadas de forma segura através de:

1. **Variáveis de ambiente**: Configure a variável `MONGODB_ATLAS_URI` para armazenar a URI de conexão de forma segura
2. **Gerenciamento interno seguro**: As credenciais são mascaradas quando exibidas na interface
3. **Validação de URI**: O sistema valida as URIs para garantir que são válidas e seguras

Para configurar o MongoDB Atlas:
1. Crie uma conta no [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Configure um cluster e obtenha a URI de conexão
3. Adicione a URI nas configurações da aplicação ou defina a variável de ambiente
4. A aplicação gerencia automaticamente conexões, retries e timeouts específicos para o Atlas

Para instruções detalhadas sobre como configurar o MongoDB Atlas, consulte o arquivo [mongodb_atlas_setup.md](mongodb_atlas_setup.md).

## Versão de Demonstração

Esta versão utiliza dados do MongoDB Atlas e possui fallbacks para demonstrar o conceito e a interface do OddsHunter. Em uma versão de produção, seria integrada com APIs reais de odds ou web scrapers para coletar dados em tempo real.

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

## Segurança

O OddsHunter foi desenvolvido com foco em segurança, especialmente para integração com MongoDB Atlas. Principais recursos de segurança:

### Gerenciamento Seguro de Credenciais

- Suporte a variáveis de ambiente para armazenar credenciais sensíveis
- Mascaramento automático de URIs de conexão na interface
- Detecção e alertas de segurança para credenciais expostas
- Validação abrangente de URIs de conexão do MongoDB Atlas

### Recursos de Segurança da Conexão

- Opções de conexão otimizadas para MongoDB Atlas
- Timeouts e limites de tentativas configuráveis
- Tratamento apropriado de erros de conexão
- Validação de URIs antes da conexão

### Interface de Configuração Segura

- Campos de senha protegidos para entrada de credenciais
- Indicadores visuais do status da conexão
- Documentação integrada sobre melhores práticas de segurança
- Verificações de segurança com recomendações

### Documentação

- [Guia de Configuração do MongoDB Atlas](mongodb_atlas_setup.md) - Instruções detalhadas para configurar MongoDB Atlas
- [Instruções de Implantação](deployment_instructions.md) - Guia para implantar a aplicação com segurança

## Desenvolvido por

Manus AI - 2025
