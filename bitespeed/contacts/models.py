from django.db import models

class Contact(models.Model):
    phoneNumber = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    linkedId = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    linkPrecedence = models.CharField(max_length=10, choices=[('primary', 'primary'), ('secondary', 'secondary')])
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    deletedAt = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.email} - {self.phoneNumber} ({self.linkPrecedence})"
