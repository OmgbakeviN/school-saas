from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    use_in_migrations=True
    def _create_user(self,email,password,**extra):
        if not email: raise ValueError("Email obligatoire")
        email=self.normalize_email(email)
        user=self.model(email=email,username=email,**extra)
        user.set_password(password); user.save(using=self._db); return user
    def create_user(self,email,password=None,**extra):
        extra.setdefault("is_staff",False); extra.setdefault("is_superuser",False)
        return self._create_user(email,password,**extra)
    def create_superuser(self,email,password=None,**extra):
        extra.setdefault("is_staff",True); extra.setdefault("is_superuser",True)
        return self._create_user(email,password,**extra)

class User(AbstractUser):
    email=models.EmailField(unique=True)
    username=models.CharField(max_length=254,unique=True)
    USERNAME_FIELD="email"
    REQUIRED_FIELDS=[]
    objects=UserManager()

class SchoolMembership(models.Model):
    class Role(models.TextChoices):
        OWNER="OWNER","Propriétaire"
        DIRECTOR="DIRECTOR","Directeur"
        MANAGER="MANAGER","Gestionnaire"
        TEACHER="TEACHER","Enseignant"
        ACCOUNTANT="ACCOUNTANT","Comptable"
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name="school_memberships")
    school=models.ForeignKey("tenants.School",on_delete=models.CASCADE,related_name="memberships")
    role=models.CharField(max_length=32,choices=Role.choices)
    is_active=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together=("user","school")
