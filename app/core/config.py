# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "Galactum API"
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str = "a_very_secret_key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    #DB_USER: str
   # DB_PASSWORD: str
  #  DB_HOST: str
 #   DB_PORT: str
#    DB_NAME: str

    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[str] = None
    DB_NAME: Optional[str] = None

    DATABASE_URL: Optional[str] = None

##    @validator("DATABASE_URL", pre=True)
##    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        # Si DATABASE_URL ya existe en .env, úsala directamente
##        if v:
##            return v

        # Asegurar formato correcto del nombre de base de datos
##        db_name = values.get("DB_NAME", "")
##        if not db_name.startswith("/"):
##            db_name = f"/{db_name}"

        # Construir manualmente la URL PostgreSQL estándar
##        return (
##            f"postgresql://{values.get('DB_USER')}:{values.get('DB_PASSWORD')}"
##            f"@{values.get('DB_HOST')}:{values.get('DB_PORT')}{db_name}"
##        )
        
        
        #if isinstance(v, str):
         #   return v
        
        # Corrección para asegurar que no haya doble barra
        #path = values.get("DB_NAME", "")
        #if not path.startswith("/"):
        #    path = f"{path}"
        #path = f"/{path}"
        #return str(
         #   AnyUrl.build(
          #      scheme="postgresql+psycopg2",
           #     username=values.get("DB_USER"),
            #    password=values.get("DB_PASSWORD"),
             #   host=values.get("DB_HOST"),
              #  port=int(values.get("DB_PORT")),
               # path=path,
                #path=f"{values.get('DB_NAME')}",
            #)
        #)  
    class Config:
        case_sensitive = True
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()