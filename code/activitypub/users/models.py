from django.db import models
from django.contrib.auth.models import AbstractUser

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


class User(AbstractUser):
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to="profile_picture/", blank=True, null=True)

    private_key = models.TextField(blank=True, editable=False)
    public_key = models.TextField(blank=True, editable=False)


    def create_private_keys(self):

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        return private_key
    
    def serialize_private_key(self, private_key):
        serialization_private_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )


        return serialization_private_key.decode("utf-8")

    def serialize_public_key(self, private_key):

        public_key = private_key.public_key()

        serialization_public_key = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo)
        
        return serialization_public_key.decode("utf-8")
    

    def save(self, **kwargs):
        if not self.public_key:
            private_key = self.create_private_keys()
            self.private_key = self.serialize_private_key(private_key)
            self.public_key = self.serialize_public_key(private_key)
        
        super().save(**kwargs)
    
    def __str__(self):
        return self.username
