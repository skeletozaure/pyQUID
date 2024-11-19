
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from data_loader import DataLoader
from quid import QuidProcessor

app = FastAPI(
    title="Delta Program Dependencies Fetcher",
    description="This API fetches the dependencies of a program",
    version="1.0.0",
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Local server"
        }
    ]
)

class Program(BaseModel):
    program_name: str = Field(..., title="Name of the program to process")

@app.post("/get_dependencies/", response_description="Get the dependencies of a program")
def process_program(program: Program):
    """
    Process the given program and generate a JSON structure.
    This function initializes a DataLoader with specified configuration,
    loads the necessary data, and processes it using a QuidProcessor to
    build a JSON structure based on the program's name.
    Args:
        program (Program): The program object containing the program details.
    Returns:
        dict: A JSON structure representing the processed program data.
    Raises:
        HTTPException: If the required data is missing in the cache.
    """
    data_loader = DataLoader(
        config_path="config.json",
        environment="DEV",
        use_cache=True
    )
    data_loader.load_data()

    if not data_loader.docsp_data or not data_loader.docfic_data:
        raise HTTPException(status_code=400, detail="Données manquantes en cache.")

    processor = QuidProcessor(
        docsp_data=data_loader.docsp_data,
        docfic_data=data_loader.docfic_data
    )
    quid_structure = processor.build_json_structure(program.program_name)  # Passer le nom du programme en tant que chaîne
    return quid_structure