from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager


class NewUserManager(UserManager):
    def create_user(self,email,password=None, **extra_fields):
        if not email:
            raise ValueError('User must have an email address')
        
        email = self.normalize_email(email) 
        user = self.model(email=email, **extra_fields) 
        user.set_password(password)
        user.save(using=self.db)
        return user


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(("email адрес"), unique=True)
    password = models.CharField(verbose_name="Пароль")    
    is_staff = models.BooleanField(default=False, verbose_name="Является ли пользователь менеджером?")
    is_superuser = models.BooleanField(default=False, verbose_name="Является ли пользователь админом?")
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True,
        help_text=('The groups this user belongs to. A user will get all permissions '
                   'granted to each of their groups.'),
        verbose_name=('groups')
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',
        blank=True,
        help_text=('Specific permissions for this user.'),
        verbose_name=('user permissions')
    )

    USERNAME_FIELD = 'email'

    objects = NewUserManager()


class IllnessManager(models.Manager):
    def get_one_illness(self, illness_id):
        return self.get(id=illness_id)

    def active(self):
        return self.filter(status='a')

class Illness(models.Model):
    STATUS_CHOICES = [
        ("a", "Active"), 
        ("d", "Deleted")
    ]
    name = models.CharField(max_length=100)
    description = models.TextField()
    spread = models.TextField()
    photo = models.URLField(blank=True, null=True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=7, default='a')

    objects = IllnessManager()

    def __str__(self):
        return self.name

class DrugManager(models.Manager):
    def get_one_drug(self, drug_id):
        return self.get(id=drug_id)

    def get_total_illnesses(self, drug):
        # Assuming DrugIllness model should track the count or update accordingly
        return drug.drugillness_set.count()

    def active(self):
        return self.filter(status='f')

class Drug(models.Model):
    STATUS_CHOICES = [
        ('dr', "Draft"),
        ('del', "Deleted"), 
        ('f', "Formed"), 
        ('c', "Completed"), 
        ('r', "Rejected")
    ]
    name = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=9, default='dr')
    created_at = models.DateTimeField(auto_now_add=True)
    formed_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    creator = models.ForeignKey(CustomUser, related_name='drugs_created', on_delete=models.SET_NULL, null=True)
    moderator = models.ForeignKey(CustomUser, related_name='drugs_moderated', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['creator'], condition=models.Q(status='dr'), name='unique_draft_per_user')
        ]

    objects = DrugManager()

    def __str__(self):
        return self.name if self.name else f"Drug {self.id}"

class DrugIllness(models.Model):
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE)
    illness = models.ForeignKey(Illness, on_delete=models.CASCADE)
    trial = models.TextField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['drug', 'illness'], name='unique_drug_illness')
        ]

    def __str__(self):
        return f"{self.drug.name} - {self.illness.name}"