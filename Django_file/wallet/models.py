from django.db import models

from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

# Create your models here.


class Wallet(models.Model):
    balance = models.FloatField()  # DECIMAL
    owner = models.ForeignKey(to=User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.source
