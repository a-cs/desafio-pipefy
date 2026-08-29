from datetime import date, datetime
import sys
from typing import Any, Literal, Type, TypeAlias, Annotated, Union
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, RootModel, model_validator, BeforeValidator, PlainSerializer, WithJsonSchema, StringConstraints
from dotenv import load_dotenv
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

# 1.Factory method to create validatos for the BR date and datetime format
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
				value = getattr(value, "root", value)
			if value is None:
				continue

			fields_attributes.append({
				"field_id": field_name,
				"field_value": str(value)
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
			status_code=status.HTTP_400_BAD_REQUEST,  # 400 é semanticamente melhor para JSON quebrado
			content={
				"error": "Erro de sintaxe no JSON",
				"details": [
					{
						"field": "body",
						"message": "O body da requisição está com um erro de sintaxe no JSON."
					}
				]
			},
		)

	return JSONResponse(
		status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
		content={
			"error":  clean_errors
		},
	)

pipefy_api_url = os.getenv("PIPEFY_API_URL")
pipefy_token = os.getenv("PIPEFY_TOKEN")
pipe_id = os.getenv("PIPE_ID")

@app.get("/")
def greeting():
	return {"message": "Bem vindo a API!"}

@app.post("/card")
def create_card(card: CardData) -> dict[str, Any]:
	card_title = card.nome
	pipefy_fields = card.to_pipefy_fields()

	query = """
	mutation ($pipe_id: ID!, $title: String!, $fields_attributes: [UndefinedInput]) {
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

	return {
		"received_data": card.to_pipefy_fields()
	}
