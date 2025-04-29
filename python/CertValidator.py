#!/usr/bin/env python3

import ssl
import socket
import logging
import argparse
import datetime
from typing import Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DATE_FORMAT = '%b %d %H:%M:%S %Y %Z'

class CertificateError(Exception):
    """Custom Exception for Certificate retrieval errors."""
    pass

def get_valid_not_after(domain: str, port: int = 443) -> str:
    """
    Retrieve the 'notAfter' field from the SSL certificate of the given domain.

    Args:
        domain (str): The domain name or IP address.
        port (int): The port number (default is 443).

    Returns:
        str: The 'notAfter' field of the SSL certificate.

    Raises:
        CertificateError: If there is an issue retrieving the certificate.
    """
    server: Tuple[str, int] = (domain, port)
    context = ssl.create_default_context()
    try:
        with socket.create_connection(server, timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                if 'notAfter' not in cert:
                    raise CertificateError("Certificate does not contain 'notAfter' field.")
                return cert['notAfter']
    except (socket.error, ssl.SSLError) as e:
        raise CertificateError(f"Error occurred while retrieving certificate: {e}")

def is_cert_valid(date: str) -> bool:
    """
    Check if the SSL certificate is still valid.

    Args:
        date (str): The 'notAfter' date string from the certificate.

    Returns:
        bool: True if the certificate is valid, False otherwise.

    Raises:
        ValueError: If the date format is invalid.
    """
    current = datetime.datetime.now()
    try:
        date_object = datetime.datetime.strptime(date, DATE_FORMAT)
    except ValueError as e:
        raise ValueError(f"Invalid Date Format. Expected Format: '{DATE_FORMAT}'") from e
    return date_object >= current

def validate_arguments(domain: str, port: int) -> None:
    """
    Validate the input arguments.

    Args:
        domain (str): The domain name or IP address.
        port (int): The port number.

    Raises:
        ValueError: If the domain or port is invalid.
    """
    if not domain:
        raise ValueError("Domain cannot be empty.")
    if not (1 <= port <= 65535):
        raise ValueError("Port must be between 1 and 65535.")

def main() -> None:
    """
    Main Function to parse arguments and validate SSL certificate.
    """
    parser = argparse.ArgumentParser(
        prog='CertValidator',
        description='Retrieve the SSL Certificate Validity.'
    )
    parser.add_argument('-d', '--domain', help='Domain / IP address', required=True)
    parser.add_argument('-p', '--port', help='Server port (default 443)', type=int, default=443)
    args = parser.parse_args()

    domain = args.domain.strip()
    port = args.port

    try:
        validate_arguments(domain, port)
        date = get_valid_not_after(domain, port)
        if is_cert_valid(date):
            logging.info(f"SSL Certificate for {domain} is valid until {date}.")
        else:
            logging.warning(f"SSL Certificate for {domain} has expired on {date}.")
    except CertificateError as ce:
        logging.error(f"Certificate Error: {ce}")
    except ValueError as ve:
        logging.error(f"Value Error: {ve}")
    except Exception as e:
        logging.error(f"Unexpected Error: {e}")

if __name__ == "__main__":
    main()
