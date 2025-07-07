from pydantic import BaseModel, Field
from typing import List

class ImportSummary(BaseModel):
    records_processed: int = Field(..., description="Total number of records found in the CSV file.")
    records_imported: int = Field(..., description="Number of records successfully imported.")
    errors: List[str] = Field(..., description="A list of errors encountered during the import process.") 