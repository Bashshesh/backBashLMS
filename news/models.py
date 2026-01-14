from django.db import models

class News(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    date = models.DateField(auto_now_add=True)
    image = models.ImageField(
        upload_to='news/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name="Обложка"
    )

    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ['-date']

    def __str__(self):
        return self.title
