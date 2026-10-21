from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1. Definimos dónde se guardará la base de datos.
# Al usar sqlite:///./bodega.db, le decimos que cree un archivo local llamado "bodega.db"
SQLALCHEMY_DATABASE_URL = "sqlite:///./bodega.db"

# 2. Creamos el Motor (Engine). Es el encargado de ejecutar las sentencias SQL por detrás.
# El "check_same_thread": False es una regla estricta solo para SQLite cuando se usa con FastAPI.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. Creamos la "Fábrica de Sesiones". 
# Cada vez que un cliente compre algo o agregues mercancía, abriremos una de estas sesiones.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)