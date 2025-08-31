# Copyright Sajid
# Updates Channel https://t.me/OxONemo

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import brotli
import gzip
import json
import csv
import logging
from io import BytesIO
from datetime import datetime
from cachetools import TTLCache
from typing import Optional

app = FastAPI(
    title="Education API",
    description="Converted from Flask to FastAPI",
    version="1.0.0"
)

# Allow all origins (customize if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.handlers = []
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

cache = TTLCache(maxsize=100, ttl=3600)

# ----------------- HELPERS ----------------- #

def decompress_response(response):
    encoding = response.headers.get('Content-Encoding', '')
    content = response.content
    try:
        if 'br' in encoding.lower():
            return brotli.decompress(content).decode('utf-8')
        elif 'gzip' in encoding.lower():
            buf = BytesIO(content)
            return gzip.GzipFile(fileobj=buf).read().decode('utf-8')
        else:
            return content.decode('utf-8')
    except Exception as e:
        logger.error(f"Decompression error: {str(e)}")
        return None

def fetch_data(url, params=None):
    cache_key = f"{url}_{json.dumps(params, sort_keys=True)}"
    if cache_key in cache:
        logger.info(f"Cache hit for {url} with params {params}")
        return cache[cache_key]
    
    headers = {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip, deflate, br',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '').lower()
        
        try:
            if 'application/json' in content_type:
                data = response.json()
            else:
                decompressed = decompress_response(response)
                if decompressed:
                    data = json.loads(decompressed)
                else:
                    logger.error(f"Failed to decompress response from {url} with params {params}")
                    return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {url} with params {params}: {str(e)}")
            return None
            
        if data and isinstance(data, dict) and 'data' in data:
            cache[cache_key] = data
            logger.info(f"Successfully fetched data from {url} with params {params}")
            return data
        else:
            logger.error(f"No valid data from {url} with params {params}: {data}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {url} with params {params}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error for {url} with params {params}: {str(e)}")
        return None

def get_thanas(district_code):
    url = "http://202.72.235.218:8000/api/v1/thana/all"
    params = {'districtCode': district_code}
    data = fetch_data(url, params)
    if data and data.get('data'):
        return {t['thanaName']: t['thanaCode'] for t in data['data'] if t['thanaName'] != "None"}
    if district_code == '82':
        return {
            'Goalanda': '308229',
            'Kalukhali': '308247',
            'Baliakandi': '308207',
            'Pangsha': '308273',
            'Rajbari Sadar': '308276'
        }
    return {}

# ----------------- ROUTES ----------------- #

@app.get("/")
async def status():
    logger.info("Serving status.html for root endpoint")
    return FileResponse("status.html")

@app.get("/api/v1/divisions")
async def get_divisions():
    divisions = {
        'Barisal': '01',
        'Chittagong': '02',
        'Dhaka': '03',
        'Khulna': '04',
        'Rajshahi': '05',
        'Rangpur': '06',
        'Sylhet': '07',
        'Mymensingh': '08'
    }
    return {
        'status': 'success',
        'data': divisions,
        'api_owner': '@OxO_Nemo',
        'api_dev': 't.me/@OxO_Nemo'
    }

@app.get("/api/v1/districts")
async def get_districts():
    districts = {
        'Dhaka': '26', 'Faridpur': '29', 'Gazipur': '33', 'Gopalganj': '35',
        'Kishoreganj': '48', 'Madaripur': '54', 'Manikganj': '56', 'Munshiganj': '59',
        'Narayanganj': '67', 'Narsingdi': '68', 'Rajbari': '82', 'Shariatpur': '86',
        'Tangail': '93'
    }
    return {
        'status': 'success',
        'data': districts,
        'api_owner': '@OxO_Nemo',
        'api_dev': 't.me/@OxO_Nemo'
    }

@app.get("/api/v1/thanas")
async def get_thanas_endpoint(district_code: str = Query(..., description="District code required")):
    thanas = get_thanas(district_code)
    if not thanas:
        raise HTTPException(status_code=404, detail={
            'status': 'error',
            'message': 'No thanas found for this district',
            'api_owner': '@OxO_Nemo',
            'api_dev': 't.me/@OxO_Nemo'
        })
    return {
        'status': 'success',
        'data': thanas,
        'api_owner': '@OxO_Nemo',
        'api_dev': 't.me/@OxO_Nemo'
    }

@app.get("/api/v1/institute-types")
async def get_institute_types():
    institute_types = {
        'School': 11,
        'College': 12,
        'Madrasah': 13,
        'Technical': 14,
        'University': 15
    }
    return {
        'status': 'success',
        'data': institute_types,
        'api_owner': '@OxO_Nemo',
        'api_dev': 't.me/@OxO_Nemo'
    }

@app.get("/api/v1/institutes")
async def fetch_institutes_endpoint(
    page: int = 1,
    size: int = 10,
    division_code: Optional[str] = None,
    district_code: Optional[str] = None,
    thana_code: Optional[str] = None,
    institute_type_id: int = 11,
    is_govt: str = "false",
    eiin_no: Optional[str] = None,
    full_response: str = "false",
    export_csv: str = "false"
):
    params = {
        'page': page,
        'size': size,
        'division_code': division_code,
        'district_code': district_code,
        'thana_code': thana_code,
        'institute_type_id': institute_type_id,
        'is_govt': is_govt.lower(),
        'eiin_no': eiin_no
    }
    
    url = "http://202.72.235.218:8082/api/v1/institute/list"
    data = fetch_data(url, {k: v for k, v in params.items() if v is not None})
    
    if not data or not data.get('data'):
        raise HTTPException(status_code=404, detail={
            'status': 'error',
            'message': 'No institute data found',
            'api_owner': '@OxO_Nemo',
            'api_dev': 't.me/@OxO_Nemo'
        })
        
    response_data = {
        'status': 'success',
        'data': [{
            'name': inst.get('instituteName', 'N/A'),
            'name_bn': inst.get('instituteNameBn', 'N/A'),
            'eiin': inst.get('eiinNo', 'N/A'),
            'type': inst.get('instituteTypeName', 'N/A'),
            'type_bn': inst.get('instituteTypeNameBn', 'N/A'),
            'division': inst.get('divisionName', 'N/A'),
            'division_bn': inst.get('divisionNameBn', 'N/A'),
            'district': inst.get('districtName', 'N/A'),
            'district_bn': inst.get('districtNameBn', 'N/A'),
            'thana': inst.get('thanaName', 'N/A'),
            'thana_bn': inst.get('thanaNameBn', 'N/A'),
            'mobile': inst.get('mobile', 'N/A'),
            'email': inst.get('email', 'N/A')
        } for inst in data['data']],
        'api_owner': '@OxO_Nemo',
        'api_dev': 't.me/@OxO_Nemo'
    }
    
    if full_response.lower() == "true":
        response_data['full_response'] = data
        
    if export_csv.lower() == "true":
        filename = f"institutes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data['data'][0].keys())
            writer.writeheader()
            writer.writerows(data['data'])
        response_data['csv_file'] = filename
        
    return response_data

@app.get("/api/v1/employees")
async def fetch_employees_endpoint(
    eiin_no: str = Query(..., description="Valid EIIN number required"),
    page: int = 1,
    size: int = 50,
    full_response: str = "false",
    export_csv: str = "false"
):
    if not eiin_no.isdigit():
        raise HTTPException(status_code=400, detail={
            'status': 'error',
            'message': 'Valid EIIN number is required',
            'api_owner': '@OxO_Nemo',
            'api_dev': 't.me/@OxO_Nemo'
        })
    
    url = "http://202.72.235.218:8082/api/v1/employee/list"
    params = {'page': page, 'size': size, 'eiinNo': eiin_no}
    data = fetch_data(url, params)
    
    if not data or not data.get('data'):
        raise HTTPException(status_code=404, detail={
            'status': 'error',
            'message': f'No employees found for EIIN: {eiin_no}',
            'api_owner': '@OxO_Nemo',
            'api_dev': 't.me/@OxO_Nemo'
        })
        
    response_data = {
        'status': 'success',
        'data': [{
            'name': emp.get('generalInformation', {}).get('employeeName', 'N/A'),
            'name_bn': emp.get('generalInformation', {}).get('employeeNameBn', 'N/A'),
            'gender': emp.get('generalInformation', {}).get('gender', 'N/A'),
            'date_of_birth': emp.get('generalInformation', {}).get('dateOfBirth', 'N/A'),
            'designation': emp.get('recruitmentInformation', {}).get('designationName', 'N/A'),
            'employment_status': emp.get('recruitmentInformation', {}).get('employmentStatus', 'N/A')
        } for emp in data['data']],
        'meta': data.get('meta', {}),
        'api_owner': '@OxO_Nemo',
        'api_dev': 't.me/@OxO_Nemo'
    }
    
    if full_response.lower() == "true":
        response_data['full_response'] = data
        
    if export_csv.lower() == "true":
        filename = f"employees_{eiin_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        employee_data = [{
            'Name': emp.get('generalInformation', {}).get('employeeName', 'N/A'),
            'Name (BN)': emp.get('generalInformation', {}).get('employeeNameBn', 'N/A'),
            'Gender': emp.get('generalInformation', {}).get('gender', 'N/A'),
            'Date of Birth': emp.get('generalInformation', {}).get('dateOfBirth', 'N/A'),
            'Designation': emp.get('recruitmentInformation', {}).get('designationName', 'N/A'),
            'Employment Status': emp.get('recruitmentInformation', {}).get('employmentStatus', 'N/A')
        } for emp in data['data']]
        if employee_data:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=employee_data[0].keys())
                writer.writeheader()
                writer.writerows(employee_data)
            response_data['csv_file'] = filename
            
    return response_data

@app.get("/api/v1/teachers")
async def fetch_teachers_endpoint(
    eiin_no: str = Query(..., description="Valid EIIN number required"),
    page: int = 1,
    size: int = 50,
    full_response: str = "false",
    export_csv: str = "false"
):
    if not eiin_no.isdigit():
        raise HTTPException(status_code=400, detail={
            'status': 'error',
            'message': 'Valid EIIN number is required',
            'api_owner': '@OxO_Nemo',
            'api_dev': 't.me/@OxO_Nemo'
        })
    
    url = "http://202.72.235.218:8082/api/v1/employee/list"
    params = {'page': page, 'size': size, 'eiinNo': eiin_no}
    data = fetch_data(url, params)
    
    if not data or not data.get('data'):
        raise HTTPException(status_code=404, detail={
            'status': 'error',
            'message': f'No teachers found for EIIN: {eiin_no}',
            'api_owner': '@OxO_Nemo',
            'api_dev': 't.me/@OxO_Nemo'
        })
        
    teachers = [emp for emp in data['data'] if emp.get('recruitmentInformation', {}).get('employeeTypeId') == 2]
    
    response_data = {
        'status': 'success',
        'data': [{
            'name': emp.get('generalInformation', {}).get('employeeName', 'N/A'),
            'name_bn': emp.get('generalInformation', {}).get('employeeNameBn', 'N/A'),
            'gender': emp.get('generalInformation', {}).get('gender', 'N/A'),
            'date_of_birth': emp.get('generalInformation', {}).get('dateOfBirth', 'N/A'),
            'designation': emp.get('recruitmentInformation', {}).get('designationName', 'N/A'),
            'employment_status': emp.get('recruitmentInformation', {}).get('employmentStatus', 'N/A'),
            'employee_type_id': emp.get('recruitmentInformation', {}).get('employeeTypeId', 'N/A'),
            'employee_type_name': emp.get('recruitmentInformation', {}).get('employeeTypeNameBn', 'N/A'),
            'exam_program': emp.get('recruitmentInformation', {}).get('examProgramNameBn', 'N/A'),
            'training_info': emp.get('employeeTrainingInformations', 'N/A')
        } for emp in teachers],
        'meta': data.get('meta', {}),
        'api_owner': '@OxO_Nemo',
        'api_dev': 't.me/@OxO_Nemo'
    }
    
    if full_response.lower() == "true":
        response_data['full_response'] = data
        
    if export_csv.lower() == "true":
        filename = f"teachers_{eiin_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        teacher_data = [{
            'Name': emp.get('generalInformation', {}).get('employeeName', 'N/A'),
            'Name (BN)': emp.get('generalInformation', {}).get('employeeNameBn', 'N/A'),
            'Gender': emp.get('generalInformation', {}).get('gender', 'N/A'),
            'Date of Birth': emp.get('generalInformation', {}).get('dateOfBirth', 'N/A'),
            'Designation': emp.get('recruitmentInformation', {}).get('designationName', 'N/A'),
            'Employment Status': emp.get('recruitmentInformation', {}).get('employmentStatus', 'N/A'),
            'Employee Type ID': emp.get('recruitmentInformation', {}).get('employeeTypeId', 'N/A'),
            'Employee Type Name': emp.get('recruitmentInformation', {}).get('employeeTypeNameBn', 'N/A'),
            'Exam Program': emp.get('recruitmentInformation', {}).get('examProgramNameBn', 'N/A'),
            'Training Info': json.dumps(emp.get('employeeTrainingInformations', 'N/A'))
        } for emp in teachers]
        if teacher_data:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=teacher_data[0].keys())
                writer.writeheader()
                writer.writerows(teacher_data)
            response_data['csv_file'] = filename
            
    return response_data

# ---------------------- RUN ---------------------- #
# Run with: uvicorn filename:app --host 0.0.0.0 --port 8000 --reload
