from sym_api_client_python.auth.rsa_auth import SymBotRSAAuth
import datetime
import logging
from jose import jwt

class SymBotRSAStringAuth(SymBotRSAAuth):
    def __init__(self, config, string_rsa):
        self.string_rsa = string_rsa
        super().__init__(config)

    def create_jwt(self):
        """
        Create a jwt token with payload dictionary. Encode with
        RSA private key using RS512 algorithm

        :return: A jwt token valid for < 290 seconds
        """
        logging.debug('RSA_auth/getJWT() function started')
        content = self.string_rsa
        private_key = ''.join(content)
        private_key = content
        expiration_date = int(datetime.datetime.now(datetime.timezone.utc)
                              .timestamp() + (5*58))
        payload = {
            'sub': self.config.data['botUsername'],
            'exp': expiration_date
        }
        encoded = jwt.encode(payload, private_key, algorithm='RS512')
        return encoded
