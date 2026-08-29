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