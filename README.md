## Para setar as variaveis de ambiente
- Entre na pasta /API
- Abra o terminal na pasta
- No terminal execute o comando para criar o arquivo ".env" com base no arquivo ".env.example":
  ```shell
  cp .env.example .env
  ```
- Abrar o arquivo ".env"
- Digita os valores das variáveis de ambiente

## Como ativar a api
- Entre na pasta /API
- Abra o terminal na pasta
- No terminal execute o comando:
  ```shell
  uvicorn main:app --reload
  ```

## Para utilizar Collection no Postman para conectar a api
- Execute a API
- Abra o Postman
- Importe a Collection do arquivo "Desafio Pipefy.postman_collection.json"
- No Postman, Crie a variavel de ambiente chamada "url", no campo value da variavel coloque "http://localhost:8000"
- Ativar o Ambiente para que a variavel seja carregada
- Executar as requisições da Collection importada
