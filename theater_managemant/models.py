from django.db import models

from accounts.models import User

class Theater(models.Model):
    owner                   =       models.ForeignKey(User, on_delete=models.CASCADE)
    name                    =       models.CharField(max_length=255)
    location                =       models.CharField(max_length=255)
    lat                     =       models.DecimalField(max_digits=25, decimal_places=20)
    lng                     =       models.DecimalField(max_digits=25, decimal_places=20)
    email                   =       models.EmailField()
    phone                   =       models.CharField(max_length=20)
    screen_types            =       models.JSONField()
    is_food_and_beverages   =       models.BooleanField(default=False)
    is_parking              =       models.BooleanField(default=False)
    image_url               =       models.URLField(max_length=500, default="")
    is_approved             =       models.BooleanField(default=False)



    def __str__(self):
        return f"{self.name} - {self.location}"


class Screen(models.Model):
    theater         =       models.ForeignKey(Theater, related_name='screens', on_delete=models.CASCADE)
    name            =       models.CharField(max_length=255)
    type            =       models.CharField(max_length=50)
    capacity        =       models.PositiveIntegerField(null=True,default=0)

    def __str__(self):
        return f"{self.name} - {self.theater.name}"
    
class ScreenImage(models.Model):
    screen          =       models.ForeignKey(Screen, related_name='screen_images', on_delete=models.CASCADE)
    image_url       =       models.URLField(max_length=500)

    def __str__(self):
        return f"{self.screen} - {self.image_url}"

    

class Tier(models.Model):
    screen          = models.ForeignKey(Screen, related_name='tiers', on_delete=models.CASCADE, null=True)
    name            = models.CharField(max_length=50)
    price           = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    total_seats     = models.PositiveIntegerField()
    rows            = models.IntegerField(null=True,blank=True)
    columns         = models.IntegerField(null=True,blank=True)
    position        = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} - {self.screen.name} - {self.screen.theater.name}"
    
    def save(self, *args, **kwargs):
        if self.pk:
            previous_tier = Tier.objects.get(pk=self.pk)
            seat_difference = self.total_seats - previous_tier.total_seats
            self.screen.capacity += seat_difference
        else:
            self.screen.capacity += self.total_seats
        

        self.screen.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.screen.capacity -= self.total_seats
        self.screen.save()
        super().delete(*args, **kwargs) 

    

class Seat(models.Model):
    tier            = models.ForeignKey(Tier, related_name='seats', on_delete=models.CASCADE)
    row             = models.CharField(max_length=5)
    column          = models.PositiveIntegerField()
    is_available    = models.BooleanField(default=False)
    identifier      = models.CharField(max_length=5, null=True, blank=True)

    # seat_layout = models.JSONField()

    def __str__(self):
        return f"Seat {self.tier.screen.name} - {self.tier.name} - {self.identifier} - {self.row} - {self.column}"
    



class SnackCategory(models.Model):
    name            =       models.CharField(max_length=255)
    owner           =       models.ForeignKey(User, on_delete=models.CASCADE, related_name="snack_categories")
    created_at      =       models.DateTimeField(auto_now_add=True)
    updated_at      =       models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.name} {self.owner}"



class SnackItem(models.Model):
    category        =       models.ForeignKey(SnackCategory, on_delete=models.CASCADE, related_name="snack_items")
    name            =       models.CharField(max_length=255)
    description     =       models.TextField(blank=True, null=True)
    is_vegetarian   =       models.BooleanField(default=False)
    calories        =       models.PositiveIntegerField(blank=True, null=True)
    created_at      =       models.DateTimeField(auto_now_add=True)
    image_url       =       models.URLField(null=True, blank=True)
    updated_at      =       models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.category} {self.name}"

class TheaterSnack(models.Model):
    theater         =       models.ForeignKey(Theater, on_delete=models.CASCADE, related_name="theater_snacks")
    snack_item      =       models.ForeignKey(SnackItem, on_delete=models.CASCADE, related_name="theater_snack_items")
    price           =       models.DecimalField(max_digits=6, decimal_places=2)
    stock           =       models.PositiveIntegerField()
    expiration_date =       models.DateField(blank=True, null=True)
    is_available    =       models.BooleanField(default=True)
    created_at      =       models.DateTimeField(auto_now_add=True)
    updated_at      =       models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.theater} {self.snack_item}"

