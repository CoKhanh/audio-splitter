from typing import Union
import asyncio
import os
from pathlib import Path

from fastapi import FastAPI, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import demucs.separate

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the separated folder as static files
app.mount("/audio", StaticFiles(directory="separated/htdemucs"), name="audio")

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.post("/separate")
async def separate_audio(request: Request, file: UploadFile = File(...)):
    # Save the uploaded file temporarily
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)

    file_path = upload_dir / file.filename
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    # Process the audio file
    await asyncio.to_thread(
        demucs.separate.main,
        ["--mp3", "--two-stems", "vocals", str(file_path)]
    )

    # Delete the uploaded file after processing
    if file_path.exists():
        file_path.unlink()

    # Get the output folder path (without extension)
    file_name_without_ext = Path(file.filename).stem
    output_folder = Path("separated/htdemucs") / file_name_without_ext

    # Build the base URL
    base_url = f"{request.url.scheme}://{request.url.netloc}"

    # Collect all files in the output folder
    files_dict = {}
    if output_folder.exists():
        for file_path in output_folder.glob("*.mp3"):
            file_name_without_ext = file_path.stem
            # Create the public URL
            relative_path = file_path.relative_to("separated/htdemucs")
            file_url = f"{base_url}/audio/{relative_path}"
            files_dict[file_name_without_ext] = file_url

    return files_dict