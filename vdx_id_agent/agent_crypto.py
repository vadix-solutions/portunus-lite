##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import base64
import logging
import os
from io import BytesIO

from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA

from . import agent_config as conf

logger = logging.getLogger("vdx_id.%s" % __name__)


key = RSA.generate(2048)
private_key = key.export_key()
file_out = open("private.pem", "wb")
file_out.write(private_key)
file_out.close()

public_key = key.publickey().export_key()
file_out = open("receiver.pem", "wb")
file_out.write(public_key)
file_out.close()


# ----------------------------
# Key generation
# ----------------------------
def prepare_keys():
    """Prepares keys for encrypt/decrypt"""
    if os.path.exists(conf.AGENT_PRI_ENCKEY_PATH) and os.path.exists(
        conf.AGENT_PUB_ENCKEY_PATH
    ):
        logger.info(
            "Private & Public keypair found: %s & %s"
            % (conf.AGENT_PRI_ENCKEY_PATH, conf.AGENT_PUB_ENCKEY_PATH)
        )
    else:
        logger.info("Pri/Pub key missing - Generating new pair")
        # First read private key if it exists
        if os.path.exists(conf.AGENT_PRI_ENCKEY_PATH):
            with open(conf.AGENT_PRI_ENCKEY, "rb") as key_file:
                private_key = RSA.import_key(key_file.read())
        # Otherwise generate a fresh one
        else:
            private_key = RSA.generate(2048)

        # Regardless of how private retrieved, generate public
        public_key = private_key.public_key()

        # Store private key
        with open(conf.AGENT_PRI_ENCKEY_PATH, "wb") as file_out:
            file_out.write(private_key.export_key())
            logger.info("Saved: %s" % conf.AGENT_PRI_ENCKEY_PATH)

        # Store public key
        with open(conf.AGENT_PUB_ENCKEY_PATH, "wb") as f:
            f.write(public_key.export_key())
            logger.info("Saved: %s" % conf.AGENT_PUB_ENCKEY_PATH)


def get_public_key(content=True, decode=True):
    with open(conf.AGENT_PUB_ENCKEY_PATH, "rb") as key_file:
        if content:
            public_key = key_file.read()
            if decode:
                public_key = public_key.decode("utf-8", "strict")
        else:
            public_key = RSA.import_key(key_file.read())
    return public_key


def __get_private_key():
    with open(conf.AGENT_PRI_ENCKEY_PATH, "rb") as key_file:
        private_key = RSA.import_key(key_file.read())
    return private_key


def decrypt_payload(enc_cipher_b64):
    private_key = __get_private_key()
    enc_cipher = BytesIO(base64.b64decode(enc_cipher_b64))

    enc_session_key, nonce, tag, ciphertext = [
        enc_cipher.read(x) for x in (private_key.size_in_bytes(), 16, 16, -1)
    ]

    # Decrypt the session key with the private RSA key
    cipher_rsa = PKCS1_OAEP.new(private_key)
    session_key = cipher_rsa.decrypt(enc_session_key)

    # Decrypt the data with the AES session key
    cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)
    data = cipher_aes.decrypt_and_verify(ciphertext, tag)
    return data
