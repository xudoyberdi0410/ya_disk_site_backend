from dotenv import load_dotenv
from flask import Flask, request
from flask_cors import CORS
from aiohttp import ClientSession
import os

load_dotenv()

app = Flask(__name__)
CORS(app)
class YaDisk:
    def __init__(self):
        self.basic_url = f"https://cloud-api.yandex.net/v1/disk"
        self.token = os.getenv("YA_TOKEN")
        self.headers = {
            "Authorization": f"OAuth {self.token}",
        }
        self.folder_path = os.getenv("FOLDER_NAME")
    
    async def get_upload_href(self, file_name: str, overwrite: bool = False, fields: list[str] = None):
        url = f"{self.basic_url}/resources/upload"
        params = {
            "path": f"/{self.folder_path}/{file_name}",
            "overwrite": str(overwrite)
        }
        if fields:
            params["fields"] = ",".join(fields)
        async with ClientSession() as self.session:
            async with self.session.get(url, headers=self.headers, params=params) as response:
                if response.status != 200:
                    return {"error": await response.json()},  response.status
                data = await response.json()
                return data["href"]
    
    async def get_info(self, file_name: str,
                 fields: list[str] = None,
                 limit: int = 20,
                 offset: int = 0,
                 preview_crop: bool = False,
                 preview_size: str = None,
                 sort: str = "name" ) -> dict:
        params = {
            "path": f"/{self.folder_path}/{file_name}",
            "limit": limit,
            "preview_crop": str(preview_crop),
            "sort": sort
        }
        if fields:
            params["fields"] = ",".join(fields)
        if offset:
            params["offset"] = offset
        if preview_size:
            params["preview_size"] = preview_size
        
        url = f"{self.basic_url}/resources"
        async with ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    return {"error": response.status}
    
    async def do_publish(self, file_name: str) -> dict:
        url = f"{self.basic_url}/resources/publish"
        params = {
            "path": f"/{self.folder_path}/{file_name}"
        }
        async with ClientSession() as session:
            async with session.put(url, headers=self.headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return str({"error": response.status})

ya_disk = YaDisk()

@app.route("/get_info", methods=["GET"])
async def get_info():
    params = dict()
    if not request.args.get("file_name"):
        return {"error": "file_name is required"}
    params["file_name"] = request.args.get("file_name")
    if request.args.get("fields"):
        params["fields"] = request.args.get("fields")
    return await ya_disk.get_info(**params)

@app.route("/get_upload_href", methods=["GET"])
async def get_upload_href():
    params = dict()
    if not request.args.get("file_name"):
        return {"error": "file_name is required"}, 400
    params["file_name"] = request.args.get("file_name")
    if request.args.get("overwrite"):
        params["overwrite"] = request.args.get("overwrite")
    if request.args.get("fields"):
        params["fields"] = request.args.get("fields")
    return await ya_disk.get_upload_href(**params)

@app.route("/publish", methods=["GET"])
async def publish():
    if not request.args.get("file_name"):
        return {"error": "file_name is required"}, 400
    await ya_disk.do_publish(request.args.get("file_name"))
    return await ya_disk.get_info(request.args.get("file_name"), fields=["public_url"])