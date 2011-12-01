from django.db import models


class Copy(models.Model):
    title = models.CharField(max_length=250)
    text = models.TextField()
