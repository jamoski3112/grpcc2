from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import datetime

def generate_certs(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate CA key and certificate
    ca_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    ca_subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, u"MirageCA"),
    ])
    
    ca_cert = x509.CertificateBuilder().subject_name(
        ca_subject
    ).issuer_name(
        ca_subject
    ).public_key(
        ca_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=None),
        critical=True,
    ).sign(ca_key, hashes.SHA256())
    
    # Save CA certificate and private key
    with open(output_dir / "ca.key", "wb") as f:
        f.write(ca_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    with open(output_dir / "ca.crt", "wb") as f:
        f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
    
    # Generate server key and certificate
    server_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    server_subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, u"MirageServer"),
    ])
    
    server_cert = x509.CertificateBuilder().subject_name(
        server_subject
    ).issuer_name(
        ca_subject
    ).public_key(
        server_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName(u"localhost"),
            x509.DNSName(u"*"),
        ]),
        critical=False,
    ).sign(ca_key, hashes.SHA256())
    
    # Save server certificate and private key
    with open(output_dir / "server.key", "wb") as f:
        f.write(server_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    with open(output_dir / "server.crt", "wb") as f:
        f.write(server_cert.public_bytes(serialization.Encoding.PEM))

if __name__ == "__main__":
    cert_dir = Path("certs")
    generate_certs(cert_dir)
    print(f"Certificates generated in {cert_dir.absolute()}") 