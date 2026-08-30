from datetime import date, datetime
from typing import Any, Literal, Type, TypeAlias, Annotated, Union
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import httpx
from pydantic import BaseModel, Field, field_validator, RootModel, model_validator, BeforeValidator, PlainSerializer, WithJsonSchema, StringConstraints
from dotenv import load_dotenv
import sys
import os

def env_initialization(): 
	load_dotenv()
	required_envs = ["PIPEFY_API_URL", "PIPEFY_TOKEN", "PIPE_ID"]
	missing_envs: list[str] = []

	for env in required_envs:
		if not os.getenv(env):
			missing_envs.append(env)

	if missing_envs:
		print(f"Erros: Variáveis de ambiente faltando: {', '.join(missing_envs)}")
		print("Preencha o arquivo .env antes de iniciar.")
		sys.exit(1)

	print("Variáveis de ambiente carregadas com sucesso!")

env_initialization()

def create_type_from_list_of_options(valid_options: list[str], field: str) -> Any:
	# Creating a customized Pydantic typy from a list

	options_set = set(valid_options)

	def validator(v: str | None) -> str| None:
		if v is None:
				return None
		if v not in options_set:
			options_str = ", ".join(f"'{o}'" for o in valid_options)
			raise ValueError(
				f"Valor inválido para {field}: '{v}'. "
				f"As opções permitidas são: {options_str}."
			)
		return v

	return validator

#creating list of options for the Card data
sexo_options= [
				"Masculino",
				"Feminino",
				"Prefere não responder"
				]

valid_hobbies: TypeAlias = Literal[
					"Teatro",
					"Música",
					"Cinema",
					"Esportes",
					"Leitura",
					"Viagem",
					"Artes"
					]

cidades_id={
	"Maracanaú": "850256388",
	"Maranguape": "850256601",
	"Eusébio": "850256710",
	"Caucaia": "850256822",
	"Fortaleza": "850256930",
	"fortaleza": "1150166576",
	"Florianópolis": "1340824346",
}

cidade_options = list(cidades_id.keys())

class list_hobbies(RootModel[list[valid_hobbies]]):
	@model_validator(mode="after")
	def check_duplicates(self) -> "list_hobbies":
		if len(self.root) != len(set(self.root)):
			raise ValueError("Valor inválido para hobbies: A lista não pode conter valores duplicados.")
		return self

# 1.Factory method to create validators for the BR date and datetime format
def dates_br_factory(expected_type: Type[Union[date, datetime]]) -> Any:
	is_datetime = expected_type is datetime
	format = "%d/%m/%Y %H:%M" if is_datetime else "%d/%m/%Y"
	error_msg = "DD/MM/YYYY HH:MM" if is_datetime else "DD/MM/YYYY"

	def validator(value: Any) -> str:
		if hasattr(value, "strftime"):
			return value.strftime(format)
		if isinstance(value, str):
			try:
				dt = datetime.strptime(value, format)
				return dt.strftime(format)
			except ValueError:
				raise ValueError(f"Formato de data inválido. Use o padrão {error_msg}.")
		raise ValueError(f"O campo deve ser uma string no formato {error_msg}.")
	
	def serializer(value: Any) -> str:
		if hasattr(value, "strftime"):
			return value.strftime(format)
		return str(value)

	return validator, serializer, error_msg

validate_date, serialize_date, date_example = dates_br_factory(date)
validate_datetime, serialize_datetime, datetime_example = dates_br_factory(datetime)

DateBR = Annotated[
	str,
	BeforeValidator(validate_date),
	PlainSerializer(serialize_date, return_type=str, when_used="always"),
	WithJsonSchema({"type": "string", "example": date_example})
	]

DatetimeBR = Annotated[
	str,
	BeforeValidator(validate_datetime),
	PlainSerializer(serialize_datetime, return_type=str, when_used="always"),
	WithJsonSchema({"type": "string", "example": datetime_example})
	]

CPF = Annotated[
	str, 
	Field(
		min_length=11, 
		max_length=11, 
		pattern=r"^\d+$",
	)
]

def validate_telefone_br(value: Any) -> str:
	if not isinstance(value, int):
		raise ValueError("O telefone deve ser enviado apenas com números.")
	phone_str = str(value)
	if len(phone_str) not in (10,11):
		raise ValueError(
				f"O telefone deve conter o DD mais 8 dígitos para número fixo ou DD mais 9 dígitos para celular. O número enviado tem um total de {len(phone_str)} dígitos."
			)
	return f"+55{value}"

TelefoneBr = Annotated[str,BeforeValidator(validate_telefone_br)]
short_text = Annotated[str, StringConstraints(max_length=255)]

class CardData(BaseModel):
	nome: short_text #requidred true
	data_de_nascimento: DateBR | None = None #requidred false 
	cpf: CPF | None = None #requidred false
	telefone: TelefoneBr | None = None #requidred false
	data: DatetimeBR | None = None #requidred false
	sexo: str | None = None #requidred false
	sexo_validator = field_validator("sexo", mode="after")(create_type_from_list_of_options(sexo_options, "sexo"))
	cidade: str #requidred true
	cidade_validator = field_validator("cidade", mode="after")(create_type_from_list_of_options(cidade_options, "cidade"))
	hobbies: list_hobbies | None = None #requidred false

	@property
	def cidade_id(self) -> str | None:
		return cidades_id.get(self.cidade)


	def to_pipefy_fields(self) -> list[dict[str, str]]:
		fields_attributes: list[dict[str, str]] = []

		for field_name in self.__dict__.keys():
			if field_name == "cidade":
				value = self.cidade_id
			else:
				value = getattr(self, field_name)
				print(value)
				value = getattr(value, "root", value)
				print(value)
			if value is None:
				continue

			fields_attributes.append({
				"field_id": field_name,
				"field_value": str(value) if field_name != "hobbies" else value
			})

		return fields_attributes


app = FastAPI()

# CORS
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],  # Allows all origins, change to your specific domain in production
	allow_credentials=True,
	allow_methods=["*"],  # Allows POST, GET, OPTIONS, etc.
	allow_headers=["*"],  # Allows headers like Content-Type
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
	clean_errors: list[dict[str, Any]] = []
	is_json_malformed = False

	for error in exc.errors():
		if error["type"] in ("json_invalid", "value_error.jsondecode"):
			is_json_malformed = True
			break
		field = error["loc"][1] if error["loc"] else "payload"
		message = error["msg"]

		if field == "nome" and error["type"] == "string_too_long":
			message = "O nome pode ter no máximo 255 caracteres."
		elif field == "cpf":
			message = "CPF inválido. O CPF deve ser um texto (string) contendo 11 números. Ex: 01234567891"
		elif message.startswith("Value error, "):
			message = message.replace("Value error, ", "")
		elif message.startswith("Input should be "):
			if "date" in message:
				message = "Data invalida"
			else: 
				message = message.replace("Input should be ", "Os valores permitidos são: ")
				message = message.replace(" or ", " ou ")
		elif message == "Field required":
			message = "Campo obrigatório"
		clean_errors.append({
			"campo": field,
			"mensagem": message
		})

	if is_json_malformed:
		return JSONResponse(
			status_code=status.HTTP_400_BAD_REQUEST,
			content={
				"error": "Erro de sintaxe no JSON",
				"details": [
					{
						"messagem": "O body da requisição está com um erro de sintaxe no JSON."
					}
				]
			},
		)

	return JSONResponse(
		status_code=status.HTTP_400_BAD_REQUEST,
		content={
			"error":  clean_errors
		},
	)

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, e: HTTPException):
	if "Card not found with id:" in e.detail:
		e.detail = e.detail.replace("Card not found with id:", "Não foi possível encontrar o card com o id:")
	if "Couldn't find Card with ID=" in e.detail:
		e.detail = e.detail.replace("Couldn't find Card with ID=", "Não foi possível encontrar o card com o id: ")
	if "The card is already in the destination phase." in e.detail:
		e.detail = "O Card já está na phase de destino."
	return JSONResponse(
		status_code=e.status_code,
		content={"error":{"mensagem": e.detail}}, 
	)

pipefy_api_url = os.environ["PIPEFY_API_URL"]
pipefy_token = os.environ["PIPEFY_TOKEN"]
pipe_id = os.environ["PIPE_ID"]

@app.get("/")
def greeting():
	return {"message": "Bem vindo a API!"}

@app.post("/card")
async def create_card(card: CardData) -> dict[str, Any]:
	card_title = card.nome
	pipefy_fields = card.to_pipefy_fields()

	query = """
	mutation ($pipe_id: ID!, $title: String!, $fields_attributes: [FieldValueInput]) {
		createCard(input: {
			pipe_id: $pipe_id,
			title: $title,
			fields_attributes: $fields_attributes
		}) {
			card {
				id
				title
			}
		}
	}
	"""

	variables: dict[str, str | list[dict[str, str]] | None] = {
		"pipe_id": pipe_id,
		"title": card_title,
		"fields_attributes": pipefy_fields
	}

	headers = {
		"Authorization": f"Bearer {pipefy_token}",
		"Content-Type": "application/json"
	}

	print(variables)

	async with httpx.AsyncClient() as client:
		try:
			response = await client.post(
				pipefy_api_url,
				json={"query": query, "variables": variables},
				headers=headers
			)
			
			# Valida erro de conexão HTTP genérico (ex: 404 ou 500 do servidor deles)
			if response.status_code != 200:
				raise HTTPException(
					status_code=response.status_code, 
					detail=f"Erro na API do Pipefy: {response.text}"
				)
				
			response_data = response.json()
			
			# Tratamento essencial: GraphQL retorna HTTP 200 mesmo em erros de sintaxe interna
			if "errors" in response_data:
				raise HTTPException(
					status_code=status.HTTP_400_BAD_REQUEST,
					detail=response_data["errors"][0]["message"]
				)
				
			# Retorno de sucesso com o ID do card criado
			return {
				"mensagem": "Card criado no Pipefy com sucesso!",
				"card_id": response_data["data"]["createCard"]["card"]["id"]
			}
			
		except httpx.RequestError as e:
			raise HTTPException(
				status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
				detail=f"Falha ao tentar conectar ao Pipefy: {e}"
			)

@app.delete("/card/{card_id}")
async def delete_card(card_id: int):
	query = """
	mutation ($card_id: ID!) {
		deleteCard(input: { id: $card_id }) {
		success
		}
	}
	"""

	variables = {
		"card_id": str(card_id)
	}

	headers = {
		"Authorization": f"Bearer {pipefy_token}",
		"Content-Type": "application/json"
	}

	async with httpx.AsyncClient() as client:
		try:
			response = await client.post(
				pipefy_api_url,
				json={"query": query, "variables": variables},
				headers=headers
			)
			
			if response.status_code != 200:
				raise HTTPException(
					status_code=response.status_code, 
					detail=f"Erro na comunicação com o Pipefy: {response.text}"
				)
				
			response_data = response.json()
			
			if "errors" in response_data:
				raise HTTPException(
					status_code=status.HTTP_400_BAD_REQUEST,
					detail=response_data["errors"][0]["message"]
				)
				
			success_status = response_data["data"]["deleteCard"]["success"]
			
			if not success_status:
				raise HTTPException(
					status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
					detail="O Pipefy processou a requisição, mas não conseguiu deletar o card."
				)
				
			return {
				"status": "sucesso",
				"mensagem": f'Card {card_id} deletado com sucesso do Pipefy!'
			}
			
		except httpx.RequestError as exc:
			raise HTTPException(
				status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
				detail=f"Falha de rede ao tentar conectar ao Pipefy: {exc}"
			)

allowed_phases_id = Literal[323403002, 323403003, 323403004]

class change_card_phase_data(BaseModel):
	destination_phase_id: allowed_phases_id

@app.post("/card/{card_id}/change_phase")
async def change_card_to_phase(card_id: int, phase: change_card_phase_data) -> dict[str, str | dict[str, Any]]:
	query = """
	mutation ($card_id: ID!, $destination_phase_id: ID!) {
		moveCardToPhase(input: { 
		card_id: $card_id, 
		destination_phase_id: $destination_phase_id 
		}) {
		card {
			id
			title
			current_phase {
			id
			name
			}
		}
		}
	}
	"""

	variables = {
		"card_id": str(card_id),
		"destination_phase_id": str(phase.destination_phase_id)
	}

	headers = {
		"Authorization": f"Bearer {pipefy_token}",
		"Content-Type": "application/json"
	}

	async with httpx.AsyncClient() as client:
		try:
			response = await client.post(
				pipefy_api_url,
				json={"query": query, "variables": variables},
				headers=headers
			)
			
			if response.status_code != 200:
				raise HTTPException(
					status_code=response.status_code, 
					detail=f"Erro na comunicação com o Pipefy: {response.text}"
				)
				
			response_data = response.json()
			
			if "errors" in response_data:
				raise HTTPException(
					status_code=status.HTTP_400_BAD_REQUEST,
					detail=response_data["errors"][0]["message"]
				)
				
			updated_card = response_data["data"]["moveCardToPhase"]["card"]
			
			return {
				"mensagem": f"Card movido para a phase {updated_card["current_phase"]["id"]} com sucesso!{" O Card chegou na phase final!" if updated_card["current_phase"]["name"] == "Concluído" else ""}",
				"dados": {
					"card_id": updated_card["id"],
					"titulo": updated_card["title"],
					"nova_phase_id": updated_card["current_phase"]["id"],
					"nova_phase_nome": updated_card["current_phase"]["name"]
				}
			}
			
		except httpx.RequestError as exc:
			raise HTTPException(
				status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
				detail=f"Falha de rede ao tentar conectar ao Pipefy: {exc}"
			)