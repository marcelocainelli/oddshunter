# Configurando MongoDB Atlas com OddsHunter

Este guia explica como configurar o OddsHunter para se conectar ao MongoDB Atlas de forma segura.

## Configurando Variáveis de Ambiente (Mais Seguro)

Para armazenar suas credenciais do MongoDB Atlas de forma segura, é recomendado usar variáveis de ambiente. Isso impede que suas credenciais sejam expostas no código ou no controle de versão.

### No Windows:

1. Abra o Prompt de Comando como administrador
2. Configure a variável de ambiente:
   ```
   setx MONGODB_ATLAS_URI "mongodb+srv://seu_usuario:sua_senha@seu_cluster.mongodb.net/?retryWrites=true&w=majority"
   ```
3. Reinicie o terminal ou computador para que a variável seja reconhecida

### No Linux/Mac:

1. Edite o arquivo `~/.bashrc` ou `~/.zshrc` (dependendo do seu shell)
2. Adicione a linha:
   ```
   export MONGODB_ATLAS_URI="mongodb+srv://seu_usuario:sua_senha@seu_cluster.mongodb.net/?retryWrites=true&w=majority"
   ```
3. Salve o arquivo e execute `source ~/.bashrc` ou `source ~/.zshrc`

### No Streamlit Cloud:

Se estiver implantando no Streamlit Cloud, configure a variável de ambiente nas configurações do aplicativo:

1. Vá para as configurações do seu aplicativo no Streamlit Cloud
2. Em "Secrets", adicione:
   ```
   MONGODB_ATLAS_URI="mongodb+srv://seu_usuario:sua_senha@seu_cluster.mongodb.net/?retryWrites=true&w=majority"
   ```

## Formato da URI do MongoDB Atlas

A URI do MongoDB Atlas geralmente segue este formato:

```
mongodb+srv://usuario:senha@cluster.mongodb.net/?opções
```

Onde:
- `usuario` é o nome de usuário do MongoDB Atlas
- `senha` é a senha do usuário
- `cluster.mongodb.net` é o endereço do seu cluster
- `opções` são parâmetros adicionais de conexão

## Obtendo sua URI do MongoDB Atlas

1. Faça login no [MongoDB Atlas](https://cloud.mongodb.com/)
2. Navegue até o seu cluster
3. Clique em "Connect"
4. Escolha "Connect your application"
5. Selecione "Python" e a versão mais recente
6. Copie a URI de conexão e substitua `<password>` pela sua senha

## Configuração via Interface

Caso prefira não usar variáveis de ambiente, você pode configurar a URI diretamente pela interface da aplicação:

1. Inicie o OddsHunter
2. Expanda a seção "Configurações do MongoDB" na barra lateral
3. Selecione "MongoDB Atlas" como tipo de conexão
4. Insira sua URI de conexão do MongoDB Atlas no campo correspondente
5. Clique em "Atualizar Configurações" e depois em "Testar Conexão"

**Nota de Segurança:** Quando você insere a URI pela interface, ela é armazenada apenas na sessão atual do Streamlit e não é salva permanentemente, a menos que você configure a variável de ambiente.

## Verificando sua Conexão

Após configurar sua URI:

1. Clique em "Testar Conexão" para verificar se a conexão está funcionando
2. O sistema informará se a conexão foi bem-sucedida e exibirá informações sobre o servidor

## Suporte a Parâmetros Avançados

Você pode incluir parâmetros adicionais na sua URI para otimizar a conexão:

```
mongodb+srv://usuario:senha@cluster.mongodb.net/?retryWrites=true&w=majority&maxPoolSize=50&readPreference=secondaryPreferred
```

Parâmetros comuns:
- `retryWrites=true`: Tenta novamente operações de escrita que falham
- `w=majority`: Requer confirmação da maioria dos nós para escritas
- `maxPoolSize`: Define o número máximo de conexões mantidas pelo driver
- `readPreference`: Define de quais nós ler (primário, secundário, etc.)

## Solução de Problemas

Se encontrar problemas na conexão:

1. Verifique se a URI está correta, incluindo usuário e senha
2. Confirme que seu IP está na lista de IPs permitidos no MongoDB Atlas
3. Certifique-se de que o usuário tem as permissões necessárias no MongoDB Atlas
4. Verifique se não há firewalls bloqueando a conexão

Para assistência adicional, consulte a [documentação oficial do MongoDB Atlas](https://docs.atlas.mongodb.com/).
