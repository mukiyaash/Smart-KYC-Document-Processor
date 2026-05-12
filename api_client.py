import requests


API_BASE_URL = "http://127.0.0.1:8000"


def check_api_health():
    """
    Checks whether FastAPI backend is running.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)

        if response.status_code == 200:
            return True, response.json()

        return False, {
            "error": f"API returned status code {response.status_code}",
            "response": response.text,
        }

    except Exception as e:
        return False, {
            "error": str(e)
        }


def extract_single_via_api(uploaded_file, mode="Balanced"):
    """
    Sends one Streamlit uploaded file to FastAPI /extract endpoint.
    """

    files_payload = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            uploaded_file.type or "application/octet-stream",
        )
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/extract",
            params={"mode": mode},
            files=files_payload,
            timeout=300,
        )

        if response.status_code != 200:
            return False, {
                "error": response.text,
                "status_code": response.status_code,
            }

        return True, response.json()

    except Exception as e:
        return False, {
            "error": str(e)
        }


def extract_batch_via_api(uploaded_files, mode="Balanced"):
    """
    Sends any number of Streamlit uploaded files to FastAPI /extract-batch endpoint.

    This version supports n files in one batch.
    """

    files_payload = []

    for file in uploaded_files:
        file_bytes = file.getvalue()

        files_payload.append(
            (
                "files",
                (
                    file.name,
                    file_bytes,
                    file.type or "application/octet-stream",
                ),
            )
        )

    if not files_payload:
        return False, {
            "error": "No files selected for upload."
        }

    try:
        response = requests.post(
            f"{API_BASE_URL}/extract-batch",
            params={"mode": mode},
            files=files_payload,
            timeout=600,
        )

        if response.status_code != 200:
            return False, {
                "error": response.text,
                "status_code": response.status_code,
            }

        return True, response.json()

    except Exception as e:
        return False, {
            "error": str(e)
        }


def validate_json_via_api(record):
    """
    Sends already extracted KYC JSON to FastAPI /validate-json endpoint.
    """

    try:
        response = requests.post(
            f"{API_BASE_URL}/validate-json",
            json=record,
            timeout=60,
        )

        if response.status_code != 200:
            return False, {
                "error": response.text,
                "status_code": response.status_code,
            }

        return True, response.json()

    except Exception as e:
        return False, {
            "error": str(e)
        }