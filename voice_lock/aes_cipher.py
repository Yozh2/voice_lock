# Cryptography AES imports
import hashlib
from Crypto import Random
from Crypto.Cipher import AES
from copy import deepcopy

class AESCipher(object):
    '''Class for easy AES cryptography'''

    def __init__(self, key, iv=None):
        self.key = hashlib.sha256(key).digest()

        if iv is None:
            self.iv = Random.new().read(AES.block_size)
        else:
            self.iv = iv

    def save_iv(self, path):
        '''Save new init vector for decoding'''
        with open(path, 'wb') as ivfile:
            ivfile.write(self.iv)

    def load_iv(self, path):
        '''Load AES init vector for decoding'''
        with open(path, 'rb') as ivfile:
            self.iv = ivfile.read()

    def encrypt(self, raw):
        _cipher = AES.new(self.key, AES.MODE_CFB, self.iv)
        return self.iv + _cipher.encrypt(raw)

    def decrypt(self, enc):
        _cipher = AES.new(self.key, AES.MODE_CFB, self.iv)
        return _cipher.decrypt(enc[AES.block_size:])

    def save_data(self, data, filename):
        with open(filename, 'wb') as f:
            f.write(self.encrypt(data))

    def load_data(self, filename):
        with open(filename, 'rb') as encrypted_file:
            data_enc = encrypted_file.read()
        return self.decrypt(data_enc)

if __name__ == '__main__':
    key = b'Sixteen byte key'
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(key, AES.MODE_CFB, iv)
    msg = iv + cipher.encrypt(b'Attack at dawn')
    print(cipher.decrypt(msg)[AES.block_size:])