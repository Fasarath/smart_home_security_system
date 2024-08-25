from django.db import models

class AuthorizedPerson(models.Model):
    name = models.CharField(max_length=100)
    face_encoding = models.BinaryField()

class AuthLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    authenticated = models.BooleanField()