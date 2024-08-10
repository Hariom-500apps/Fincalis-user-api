"""Bunny For media file upload"""
import requests
import logging
from os import environ
from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger(__name__)

STORAGE_ZONE_NAME = environ.get("STORAGE_ZONE_NAME")
ACCESS_KEY =environ.get("ACCESS_KEY")
base_url = environ.get("BASE_URL")


def upload_file(file_path, file_name, m):
    try:
        if m == "p_image":
          dir = "profile_images"
        elif m == "pan_image":
            dir = "pan_images"
        elif m == "bank_st":
            dir = "bank_statement"
        else:
            dir = "aadhar_images"
            
        url = f"https://{base_url}/{STORAGE_ZONE_NAME}/fincalis/media/{dir}/{file_name}"

        headers = {
            "AccessKey": ACCESS_KEY,
            "Content-Type": "application/octet-stream",
            "accept": "application/json"
        }
        with open(file_path, 'rb') as file_data:
            response = requests.put(url, headers=headers, data=file_data)
        return response 
    except Exception as exc:
        msg = f"upload file bunny exception {str(exc)}"
        logger.exception(msg)
        response(str(exc), 0, 404)

def get_file(file_name, m):
    try:
        if m == "p_image":
          dir = "profile_images"
        elif m == "pan_image":
            dir = "pan_images"
        elif m == "bank_st":
            dir = "bank_statement"
        else:
            dir = "aadhar_images"
        url = f"https://{base_url}/{STORAGE_ZONE_NAME}/fincalis/media/{dir}/{file_name}"
        headers = {
            "AccessKey": ACCESS_KEY,
            "Content-Type": "application/octet-stream",
            "accept": "application/json"
        }
        response = requests.get(url, headers=headers)
        return response
    except Exception as exc:
        msg = f"get file bunny exception {str(exc)}"
        logger.exception(msg)
        response(str(exc), 0, 404)
