# Sobre o projeto
## Objetivo
- O objetivo desse projeto é criar uma API utilizando um framework em Python que atuara como uma integração com o Pipefy.

## Exemplo de funcionamento:
- O usuário irá fazer uma requisição para a API usando o padrão REST, a API fará uma pre-validação dos dados, caso os dados sejam validos a API ira fazer uma requisição para o Pipefy utilizando o GraphQL e retornara o resultado para o usuário.

## Vantagem
- A vantagem de ter essa API atuando como integração com o Pipefy é que facilitara a intregração do Pipefy com outros serviços, sevindo como se fosse uma camada de abstração, onde o usuário não precisara saber utilizar o GraphQl, apenas precisará do conhecimento em REST API, que é um padrão mais comum de ser utilizado no mercado.

<br/>
<br/>
<br/>

# Como executar o projeto

## Apenas na primeira vez que ativar o Ambiente venv do python
- Para começar instale o Python 3 na sua maquina caso não tenha
- Abra o terminal na pasta raiz do projeto
- No terminal para criar o ambiente, execute o comando:
   ```shell
  python -m venv .venv
  ```
- No terminal para ativar o ambiente, execute o comando:
  - No Windows:
	```shell
	.venv\Scripts\activate
	```
  - No Mac/Linux:
	```shell
	source .venv/bin/activate
	```
- No terminal para instalar as dependências do projeto no ambiente, execute o comando:
  ```shell
	pip install -r requirements.txt
	```

## Nas proximas vezes para ativar o venv do Python
- Abra o terminal na pasta raiz do projeto
- No terminal para ativar o ambiente, execute o comando:
  - No Windows:
	```shell
	.venv\Scripts\activate
	```
  - No Mac/Linux:
	```shell
	source .venv/bin/activate
	```

## Para setar as variaveis de ambiente
- Entre na pasta /API
- Abra o terminal na pasta
- No terminal execute o comando para criar o arquivo ".env" com base no arquivo ".env.example":
  ```shell
  cp .env.example .env
  ```
- Abrar o arquivo ".env"
- Digita os valores das variáveis de ambiente

## Como ativar a API
- Entre na pasta /API
- Abra o terminal na pasta
- No terminal execute o comando:
  ```shell
  uvicorn main:app --reload
  ```

## Para utilizar Collection no Postman para conectar a API
- Execute a API
- Abra o Postman
- Importe a Collection do arquivo "Desafio Pipefy.postman_collection.json"
- No Postman, crie a variavel de ambiente chamada "url", no campo value da variavel coloque "http://localhost:8000"
- Ativar o Ambiente para que a variavel seja carregada
- Executar as requisições da Collection importada

<br/>
<br/>
<br/>

# Como utilizar as Rotas do Postman

## Create Card
- Os dados deverão ser passados no body da requisição,
	- Ex:
	```json
	{
		"nome": "Nome",
		"sexo": "Masculino",
		"cidade": "Fortaleza",
		"hobbies": ["Viagem", "Cinema"],
		"data_de_nascimento": "01/01/2000",
		"data": "28/08/2026 10:01",
		// "cpf": "01234567891",
		"telefone": 85123456789
	}
	```
	Obs:
	1. Apenas os campos de nome e cidade são obrigatórios.
	2. No campo sexo os valores permitidos são: 
		```json
		"Masculino", "Feminino" ou "Prefere não responder"
		```
	3. No campo cidade os valores permitidos são:
		```json
		"Maracanaú", "Maranguape", "Eusébio", "Caucaia", "Fortaleza", "fortaleza", "Florianópolis"
		```
	4. No campo hobbies deverá ser uma lista contendos alguns dos valores permitidos dessa lista:
		```json
		["Teatro", "Música", "Cinema", "Esportes", "Leitura", "Viagem", "Artes"]
		```
	5. Caso deseje utilizar o campo cpf, o valor do cpf precisará ser um valor válido.
	6. O campo telefone deverá ser nos formatos
        - (85) 91234-5678, passando apenas os digitos no campo:
			```json
			85912345678
			```
        - ou (85) 1234-5678, passando apenas os digitos no campo:
			```json
			8512345678
			```


## Delete Card
- O card_id devera ser passado como path param na url da requisição
	- Ex: 
	 ```{{url}}/card/{card_id}```

## Move Card to phase
- O card_id devera ser passado como path param na url da requisição
	- Ex: 
	 ```{{url}}/card/{card_id}```
- No body da requisição deverá ser passado um phase_id valido
	- Ex:
	```json
	{
		"destination_phase_id": {phase_id}
	}
	```