from django.db import models


class Booking(models.Model):
   name = models.CharField(max_length=200)    
   reservation_date = models.DateField()
   reservation_slot = models.SmallIntegerField(default=10)
   guest_number = models.IntegerField()
   comment = models.CharField(max_length=1000)

   def __str__(self):
      return self.name


class Menu(models.Model):
   name = models.CharField(max_length=200)
   price = models.IntegerField()
   description = models.TextField(max_length=1000, default="")

   def __str__(self):
      return self.name