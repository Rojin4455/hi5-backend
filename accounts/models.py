from django.db import models
from django.contrib.auth.models import AbstractBaseUser,PermissionsMixin,BaseUserManager
from random import randint
from django.utils import timezone
from datetime import timedelta




def RandNumber():
    return f'Unknown{randint(100000, 999999)}'



class Manager(BaseUserManager):
    def create_user(self, email=None, password=None, phone=None, first_name=None, last_name=None, **extra_fields):
        if email:
            email = self.normalize_email(email)
        if not (email or phone):
            raise ValueError('A phone number or email address is required.')
        user = self.model(email=email, phone=phone, first_name=first_name, last_name=last_name, **extra_fields)

        if not first_name:
            user.first_name = RandNumber()
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user
    

    def create_superuser(self, email, password, phone=None, first_name=None, last_name=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)

        if password is None:
            raise ValueError('Superuser must have a password')

        return self.create_user(email, password, phone, first_name, last_name, **extra_fields)
    

    def create_staff(self, email, password=None, phone=None, first_name=None, last_name=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_superuser', False)

        if password is None:
            raise ValueError('Staff must have a password')

        return self.create_user(email, password, phone, first_name, last_name, **extra_fields)
    


class User(AbstractBaseUser,PermissionsMixin):
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    phone = models.CharField(max_length=12,null=True,blank=True)
    email = models.EmailField(max_length=254,unique=True, blank=True, null=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True,blank=True,null=True)
    is_owner = models.BooleanField(default=False, blank=True, null=True)
    business_name = models.CharField(max_length=50, null=True, blank=True)
    is_approved = models.BooleanField(default=False, blank=True, null=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_groups',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )


    objects = Manager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email or self.phone


class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,blank=True, null=True)
    phone = models.CharField(max_length=12,null=True,blank=True)
    email = models.EmailField(max_length=254,unique=True, blank=True, null=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(blank=True,null=True)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = self.created_at + timedelta(minutes=2)
        super(OTP, self).save(*args, **kwargs)

    def is_valid(self):
        return timezone.now() < self.expires_at

    def __str__(self):
        return f"OTP for {self.email,self.phone}"





class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="user_profile")
    # profile_pic = models.ImageField(
    #     upload_to='user/profile_pic/', null=True, blank=True)
    
    image_url = models.URLField(max_length=500,default="")

    def __str__(self):
        return str(self.user.first_name)
    

class UserLocation(models.Model):
    user =  models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_location")
    location = models.CharField(max_length=255)
    lat = models.DecimalField(max_digits=25, decimal_places=20)
    lng = models.DecimalField(max_digits=25, decimal_places=20)


    def __str__(self):
        return f"{self.user.email} - {self.location.split(" ")[0]}"
        
