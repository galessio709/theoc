import requests
import os
from fastapi import FastAPI, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import logic as logic


app = FastAPI(debug=os.environ.get("MODE", "DEBUG") == "DEBUG")
######################
UPLOAD_FOLDER = 'uploads' 
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LogName(BaseModel):
    name: str

class EventPattern(BaseModel):
    et: str
    phiet: dict
    op: str
    n: int
    q: str
    ot: str
    phiot: dict

class FlowPattern(BaseModel):
    fp: str
    opD: str
    td: int
    psi: list

@app.post("/api/uploadLog")
async def uploadFile(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    if logic.uploadLog(file_path):
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            print("The file does not exist")
    return getLog(file.filename)

@app.post("/api/loadLog")
async def loadLog(log: LogName):
    url = ""
    if log.name == "Logistic":
        url = 'https://zenodo.org/records/8428084/files/ContainerLogistics.json?download=1'
    elif log.name == "Order management":
        url = 'https://zenodo.org/records/8428112/files/order-management.json?download=1'
    elif log.name == "Procure to payment":
        url = 'https://zenodo.org/records/8412920/files/ocel2-p2p.json?download=1'
    r = requests.get(url, allow_redirects=True)
    logic.loadLog(r.content)
    return getLog(log.name)

def getLog(log: str):
    objects = logic.getObjects()
    events = logic.getEvents() 
    objTypes = logic.getObjectTypes()
    evTypes = logic.getEventTypes()
    return JSONResponse(content={"logName": log, "numObjects": objects, "numEvents": events, "objTypes": objTypes, "evTypes": evTypes})


@app.post("/api/evalOCCRu")
async def submit_data(ePa: EventPattern, fp: FlowPattern):
    print(ePa)
    print(fp)
    res = logic.evalOCCRu(ePa, fp)
    return res

@app.post("/api/evalOCCRb")
async def submit_data(ePa: EventPattern, fp: FlowPattern, ePb: EventPattern):
    print(ePa)
    print(fp)
    print(ePb)
    res = logic.evalOCCRb(ePa, fp, ePb)
    return res


if not app.debug:
    static_files_folder = os.path.join(os.path.dirname(__file__), 'static')
    if os.path.exists(static_files_folder) and os.path.isdir(static_files_folder):
        app.mount("/", StaticFiles(directory=static_files_folder, html=True), name="static")
