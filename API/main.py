from datetime import date, datetime
from typing import Any
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

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

hobbies_options = [
					"Teatro",
					"Música",
					"Cinema",
					"Esportes",
					"Leitura",
					"Viagem",
					"Artes"
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
        #handle syntax error, json_invalid
        if error["type"] in ("json_invalid", "value_error.jsondecode"):
            is_json_malformed = True
            break

        message = error["msg"]
        # Removes Pydantic's default prefix
        if message.startswith("Value error, "):
            message = message.replace("Value error, ", "")
            
        # Gets the exact field name that failed
        field = error["loc"][-1] if error["loc"] else "payload"
        
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
    nome: str
    data_de_nascimento: date | None = None #requidred false 
    ##CONSERTAR ERRO PARA ACEITAR DATA PT BR E CORRIGIR MENSAGEM DO ERROR HANDLING
    cpf: int | None = None #requidred false  #### checar tipo correto
    telefone: int | None = None #requidred false  #### checar tipo correto
    data: datetime | None = None #requidred false  #### checar tipo correto
    sexo: str | None = None
    sexo_validator = field_validator("sexo", mode="after")(create_type_from_list_of_options(sexo_options, "sexo"))
    hobbies: str | None = None
    hobbies_validator = field_validator("hobbies", mode="after")(create_type_from_list_of_options(hobbies_options, "hobbies"))
    cidade: str | None = None
    cidade_validator = field_validator("cidade", mode="after")(create_type_from_list_of_options(cidade_options, "cidade"))

@app.get("/")
def read_root():
    return {"message": "Welcome to my Python API!"}

@app.post("/card")
def create_card(card: CardData) -> dict[str, Any]:
	print(card)
	return {
        "received_data": card
    }
