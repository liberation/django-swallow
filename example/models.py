from django.db import models


class FeedItem(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
