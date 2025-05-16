# Como testar e executar o OddsHunter com segurança

Este guia fornece instruções sobre como executar, testar e implantar com segurança o OddsHunter com a integração MongoDB Atlas.

## Pré-requisitos

1. Python 3.7+ instalado
2. Conta no MongoDB Atlas (gratuita ou paga)
3. Pip para instalação de dependências

## Instalação

1. Clone o repositório ou descompacte o arquivo do projeto:
   ```
   git clone https://github.com/seuusuario/oddshunter.git
   ```

2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

## Configuração segura do MongoDB Atlas

### Método 1: Usando variáveis de ambiente (Recomendado)

1. Obtenha sua URI de conexão do MongoDB Atlas
2. Configure a variável de ambiente:

   **Windows:**
   ```
   setx MONGODB_ATLAS_URI "mongodb+srv://seu_usuario:sua_senha@seu_cluster.mongodb.net/?retryWrites=true&w=majority"
   ```

   **Linux/Mac:**
   ```
   export MONGODB_ATLAS_URI="mongodb+srv://seu_usuario:sua_senha@seu_cluster.mongodb.net/?retryWrites=true&w=majority"
   ```

   **Permanente no Linux/Mac (adicione ao seu .bashrc ou .zshrc):**
   ```
   echo 'export MONGODB_ATLAS_URI="mongodb+srv://seu_usuario:sua_senha@seu_cluster.mongodb.net/?retryWrites=true&w=majority"' >> ~/.bashrc
   source ~/.bashrc
   ```

3. Reinicie seu terminal ou sessão após configurar a variável de ambiente

### Método 2: Usando a interface (Menos seguro)

1. Inicie a aplicação
2. Acesse a seção "Configurações do MongoDB" na barra lateral
3. Digite sua URI do MongoDB Atlas no campo "Nova MongoDB Atlas URI"
4. Clique em "Atualizar Configurações"

## Teste de conexão e validação

1. Depois de configurar sua URI, clique em "Testar Conexão"
2. Verifique se a conexão foi bem-sucedida
3. Verifique se o banco de dados e a coleção são acessíveis

## Executando a aplicação

Execute o aplicativo Streamlit com:

```
streamlit run streamlit_app.py
```

## Verificação de segurança

A aplicação inclui várias camadas de segurança:

1. **Mascaramento de URI**: Todas as URIs exibidas na interface são mascaradas para ocultar credenciais
2. **Validação de URI**: As URIs são validadas antes de serem usadas
3. **Verificação de segurança**: A aplicação verifica e alerta sobre problemas de segurança
4. **Documentação**: Orientações detalhadas sobre as melhores práticas

## Implantação segura

Para implantar em produção:

1. **Streamlit Cloud**:
   - Configure as variáveis de ambiente nas configurações da sua aplicação
   - Use secrets.toml para armazenar informações sensíveis

2. **Heroku**:
   - Configure variáveis de ambiente na interface do Heroku ou através da CLI
   ```
   heroku config:set MONGODB_ATLAS_URI="mongodb+srv://..."
   ```

3. **Docker**:
   - Use arquivos .env ou secrets do Docker para gerenciar as credenciais
   - Não inclua credenciais no Dockerfile ou na imagem Docker

## Recomendações adicionais de segurança

1. Crie um usuário específico no MongoDB Atlas para a aplicação com privilégios mínimos
2. Configure whitelist de IPs no MongoDB Atlas para permitir apenas conexões conhecidas
3. Ative autenticação de dois fatores na sua conta MongoDB Atlas
4. Faça backups regulares dos seus dados
5. Monitore logs de acesso e tentativas de conexão suspeitas

## Solução de problemas comuns

- **Erro de conexão "timeout"**: Verifique se seu IP está na lista de permitidos do MongoDB Atlas
- **Falha de autenticação**: Verifique se o usuário e senha estão corretos
- **Problemas de DNS**: Verifique sua conexão com a internet e resolução de DNS
- **Variável de ambiente não reconhecida**: Reinicie seu terminal ou computador após configurá-la

## Informações adicionais

Consulte a documentação oficial do MongoDB Atlas para mais detalhes sobre segurança e melhores práticas:
[MongoDB Atlas Security Documentation](https://docs.atlas.mongodb.com/security/)
