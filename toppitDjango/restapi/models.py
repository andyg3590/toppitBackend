from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Task(models.Model):
    #FK
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='tasks')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')

    #fields
    name = models.CharField(max_length=255)
    isDone = models.BooleanField(default=False)
    isApproved = models.BooleanField(default=False)
    hoursPlanned = models.PositiveSmallIntegerField(null=True)
    hoursCompleted = models.PositiveSmallIntegerField(null=True)
    startDate = models.DateTimeField(default=timezone.now)
    endDate = models.DateTimeField(null=True)
    dueDate = models.DateTimeField(null=True)

    #weight
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    DIFFICULTY_CHOICES = (
        (LOW, 'low'),
        (MEDIUM, 'medium'),
        (HIGH, 'high'),
    )
    difficulty = models.CharField(max_length=6,
                                      choices=DIFFICULTY_CHOICES,
                                      default=MEDIUM)
    
    class Meta:

        unique_together = ('assignment', 'user', 'name')

        #add, change, delete already exist by default
        permissions = (
            ('view_task', 'View tasks'),
        )

    def __str__(self):
        return self.name

class Profile(models.Model):
    #FK
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    #fields
    grade = models.PositiveSmallIntegerField(null=True)
    age = models.PositiveSmallIntegerField(null=True)
    gender = models.CharField(max_length=50, null=True)
    
    #email verification
    verified = models.BooleanField(default=False)
    emailCode = models.CharField(max_length=40, null=True)
    #keyExpiration = models.DateTimeField(null=True)

    passwordCode = models.CharField(max_length=40, null=True)

    class Meta:
        #add, change, delete already exist by default
        permissions = (
            ('view_profile', 'View user profile'),
        )

    def __str__(self):
        return "User Info: \nGrade:"  + str(self.grade) + "\nAge: " + str(self.age) + "\nGender: " + self.gender \
               + "\nUser: " + "" if self.user is None else str(self.user)
