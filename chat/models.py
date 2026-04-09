from django.db import models

class UserProfile(models.Model):
    user_id = models.BigIntegerField(unique=True, verbose_name="Telegram ID")
    first_name = models.CharField(max_length=255, null=True, blank=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    current_mode = models.CharField(
        max_length=50, 
        default="default", 
        verbose_name="Hozirgi rejim"
    )
    language = models.CharField(max_length=10, default="uz")

    def __str__(self):
        return f"{self.user_id} - {self.current_mode}"

class ChatHistory(models.Model):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('model', 'AI Model'),
    )
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="history")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.user_id}: {self.role} - {self.text[:30]}"