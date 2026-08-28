from datetime import date, datetime
from typing import Any, Literal, Type, TypeAlias, Annotated, Union
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, RootModel, model_validator, BeforeValidator, PlainSerializer, WithJsonSchema, StringConstraints


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

cidade_options = [
					"Maracanaú",
					"Maranguape",
					"Eusébio",
					"Caucaia",
					"Fortaleza",
					"fortaleza",
					"Florianópolis"
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

class list_hobbies(RootModel[list[valid_hobbies]]):
	@model_validator(mode="after")
	def check_duplicates(self) -> "list_hobbies":
		if len(self.root) != len(set(self.root)):
			raise ValueError("Valor inválido para hobbies: A lista não pode conter valores duplicados.")
		return self

# 1.Factory method to create validatos for the BR date and datetime format
def dates_br_factory(expected_type: Type[Union[date, datetime]]) -> Any:
	is_datetime = expected_type is datetime
	formats = ["%d/%m/%Y %H:%M"] if is_datetime else ["%d/%m/%Y"]
	error_msg = "DD/MM/YYYY HH:MM" if is_datetime else "DD/MM/YYYY"

	def validator(value: Any) -> Any:
		if isinstance(value, str):
			for format in formats:
				try:
					dt = datetime.strptime(value, format)
					return dt if is_datetime else dt.date()
				except ValueError:
					continue
			raise ValueError(f"Formato de data inválido. Use o padrão {error_msg}.")
		raise ValueError(f"O campo deve ser uma string no formato {error_msg}.")

	def serializer(value: Any) -> str:
		output_format = "%d/%m/%Y %H:%M" if isinstance(value, datetime) else "%d/%m/%Y"
		return value.strftime(output_format)

	return validator, serializer, error_msg

validate_date, format_date, date_example = dates_br_factory(date)
validate_datetime, format_datetime, datetime_example = dates_br_factory(datetime)

DateBR = Annotated[
	date,
	BeforeValidator(validate_date),
	PlainSerializer(format_date, return_type=str),
	WithJsonSchema({"type": "string", "example": date_example})
	]

DatetimeBR = Annotated[
	datetime,
	BeforeValidator(validate_datetime),
	PlainSerializer(format_datetime, return_type=str),
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

@app.get("/")
def greeting():
	return {"message": "Bem vindo a API!"}

@app.post("/card")
def create_card(card: CardData) -> dict[str, Any]:
	if card.data == None:
		card.data = datetime.now()
	print(card)
	return {
		"received_data": card
	}
