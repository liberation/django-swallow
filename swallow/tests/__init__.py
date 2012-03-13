from django.db import models


class Section(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class ArticleToSection(models.Model):
    article = models.ForeignKey('Article')
    section = models.ForeignKey(Section)
    weight = models.IntegerField()


class Article(models.Model):
    title = models.CharField(max_length=255)
    sections = models.ManyToManyField(Section, through=ArticleToSection)
    primary_sections = models.ManyToManyField(
        Section,
        related_name='highlight_set'
    )
    kind = models.CharField(max_length=255)
    author = models.CharField(max_length=255)

    modified_by = models.CharField(max_length=255)

    def __unicode__(self):
        return self.title


class ModelForBuilderTests(models.Model):
    simple_field = models.IntegerField()
    second_field = models.IntegerField(null=True)
    m2m = models.ManyToManyField('RelatedM2M')


class RelatedM2M(models.Model):
    foreign_m2m = models.ManyToManyField(ModelForBuilderTests)


from models import *
from integration import *
from config import *
from transactions import *
from builder import *
from populator import *
