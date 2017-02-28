#models
from django.contrib.auth.models import *
from rest_framework.authtoken.models import Token
from restapi.models import *
#serializers
from restapi.serializers import *
#viewsets
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.viewsets import ViewSet
#classviews
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import detail_route, list_route, api_view, authentication_classes, permission_classes
#generic classes
from rest_framework import generics
#authentication
from django.contrib.auth import authenticate
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.authentication import TokenAuthentication
#permissions
from rest_framework import permissions
from restapi.permissions import *
#filters
from rest_framework import filters
#from rest_framework.filters import DjangoFilterBackend
#dates
from django.utils import timezone
import datetime
#email
from django.core.mail import send_mail
import hashlib, random
#For converting google oAuth code
from rest_framework_social_oauth2.views import ConvertTokenView
#time
from datetime import *
from django.utils import timezone
#group endpoint
from django.apps import apps

#verify a user's e-mail given a code
@api_view(['post'])
def receiveEmailCode(request, code):
    user = request.user
    profile = user.profile
    if code == profile.emailCode:
        profile.verified = True
        profile.save()
        return Response({'status': user.email + ' verified'})
    else:
        return Response({'status': 'wrong code provided'},status=status.HTTP_400_BAD_REQUEST)

#send a user a new code to verify their e-mail
@api_view(['post'])
def sendEmailCode(request):
    user = request.user
    profile = user.profile
    code = genCode(user.username)
    profile.emailCode = code
    profile.save()
    #e-mail start
    subject = 'Neat E-mail Verification'
    body = 'Here is your code: ' + code
    fromEmail = 'gfern022@fiu.edu'
    send_mail(
        subject,
        body,
        fromEmail,
        [request.user.email],
        fail_silently=False,
    )
    return Response({'status': 'E-mail code sent'})

#send a user a new code to reset or change their password
@api_view(['post'])
@authentication_classes([])
@permission_classes([])
def sendPasswordCode(request, email):
    user = User.objects.filter(email=email)
    if user.count() is 0:
        return Response({'error': 'E-mail provided not in database'},status=status.HTTP_400_BAD_REQUEST)
    user = user[0]
    profile = user.profile
    code = genCode(user.username)
    profile.passwordCode = code
    profile.save()
    #e-mail start
    subject = 'Neat Password Code'
    body = 'Here is your code: ' + code
    fromEmail = 'gfern022@fiu.edu'
    send_mail(
        subject,
        body,
        fromEmail,
        [email],
        fail_silently=False,
    )
    return Response({'status': 'Password code sent'})

#change user's password given a code
@api_view(['post'])
@authentication_classes([])
@permission_classes([])
def changePassword(request, code):
    serializer = SimpleUserSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = User.objects.filter(email=request.data.get('email'))
        if user.count() is 0:
            return Response({'error': 'e-mail provided not in database'},status=status.HTTP_400_BAD_REQUEST)
        user = user[0]
        passcode = user.profile.passwordCode
        if passcode != code:
            return Response({'status': 'wrong code provided'},status=status.HTTP_400_BAD_REQUEST)
        user.set_password(request.data.get('password'))
        user.save()
        return Response({'status': 'password set'})
    else:
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)
        
def genCode(username):
    salt = hashlib.sha256()
    salt.update(str(random.random()).encode('utf-8')[:5])
    salt.update(username.encode('utf-8'))
    return salt.hexdigest()[:5]

#Get user progress for an assignment, given assignment pk
@api_view(['get'])
def getAssigProgressView(request, pk):
    assig = Assignment.objects.filter(pk=pk)
    if assig.count() is 0:
        return Response({'error': 'assignment provided not in database'},status=status.HTTP_400_BAD_REQUEST)
    else:
        data = getAssignmentData(assig[0], request.user, True)
        if not data:
            return Response({'error': 'this user has no tasks in this assignment'},status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(data)

#Get assignment statistics, given assignment pk
@api_view(['get'])
def CollabView(request, pk):
    assig = Assignment.objects.filter(pk=pk)
    total, count = 0.0 , 0
    array = []
    if assig.count() is 0:
        return Response({'error': 'assignment provided not in database'},status=status.HTTP_400_BAD_REQUEST)
    else:
        for rosterObj in AssignmentRoster.objects.filter(assignment=assig[0]):
            data = getAssignmentData(assig[0], rosterObj.user, False)
            if data:
                total += data[0]['progress']
                count += count + 1
        return Response({'average' : total/count})


#Compute assignment percentages, weights
#if detailed = True , smart status is computed
def getAssignmentData(assig, user, detailed):
    weights = [0.5, 1.0, 1.5]
    total, progress = 0.0 , 0.0
    data = []
    tasks = assig.tasks.filter(user=user)
    for task in tasks:
        difficulty = task.difficulty
        if difficulty == 'medium':
            weight = weights[1]
        elif difficulty == 'low':
            weight = weights[0]
        else:
            weight = weights[2]
        if task.isDone == True:
            state = 1
        else:
            state = 0
        data += [{'task pk' : task.pk, 'weight' : weight, 'state' : state}]
        total += weight
    if total == 0:
        return data
    for task in data:
        task['percentage'] = task['weight']/total
        task['contribution'] = (task['weight']*task['state'])/total
        progress += task['contribution']
    expected = getExpected(assig.startDate, assig.dueDate)
    if detailed:
        status = getSmartStatus(progress, expected)
        data.insert(0,{'progress' : progress, 'expected' : expected, 'smart status' : status})
    else:
        data.insert(0,{'progress' : progress, 'expected' : expected})
    return data

def getExpected(startDate, dueDate):
    now = timezone.now()
    totalTime = dueDate-startDate
    timePassed = now-startDate
    return timePassed/totalTime


def getSmartStatus(current, expected):
    result = ['Not Tracking Yet', 'On Track', 'Slightly Behind', 'Considerably Behind', 'Significantly Behind']
    milestone = [0.3, 0.6, 0.9]
    diff = expected - current
    #not tracking
    if current < milestone[0]:
        return result[0]
    #ahead of expected
    elif diff <= 0:
        return result[1]
    #first milestone range
    elif milestone[0] <= current < milestone[1]:
        threshold = [0.15, 0.25]
        if diff < threshold[0]:
            return result[2]
        elif threshold[0] <= diff < threshold[1]:
            return result[3]
        else:
            return result[4]
    #second milestone range
    elif milestone[1] <= current < milestone[2]:
        threshold = [0.1, 0.2]
        if diff < threshold[0]:
            return result[2]
        elif threshold[0] <= diff < threshold[1]:
            return result[3]
        else:
            return result[4]
    #third milestone range
    else:
        threshold = [0.05, 0.15]
        if diff < threshold[0]:
            return result[2]
        elif threshold[0] <= diff < threshold[1]:
            return result[3]
        else:
            return result[4]

#get classes users belongs to, and if class is public, get assignments
@api_view(['get'])
def MyClassesView(request):
    queryset = (Class.objects.filter(roster__user=request.user)).order_by('pk')
    serializer = MyClassesSerializer(queryset, many=True, context={'request': request})
    data = serializer.data
    return Response(data)

#Get user dashboard info, given token
#Also calculate additional task information & smart status
@api_view(['get'])
def DashboardView(request):
    queryset = (Assignment.objects.filter(roster__user=request.user)).order_by('pk')
    serializer = DashboardSerializer(queryset, many=True, context={'request': request})
    data = serializer.data
    for assig in data:
        subdata = getAssignmentData(Assignment.objects.get(pk=assig['pk']), request.user, True)
        if subdata:
            assig.update(subdata.pop(0))
            for x, y in zip(assig['tasks'], subdata):
                y.pop('task pk')
                y.pop('state')
                x.update(y)
    return Response(data)


class UserViewSet(viewsets.ModelViewSet):
    #No authentication required
    authentication_classes = ()
    permission_classes = ()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('email', 'first_name', 'last_name', 'groups', 'profile')
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer

    @list_route(methods=['get'],authentication_classes=[TokenAuthentication],permission_classes=[permissions.IsAuthenticated])
    def getFromToken(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class SchoolViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, IsCreatorCanEdit,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('name', 'identifier')
    queryset = School.objects.all()
    serializer_class = SchoolSerializer

class SchoolRosterViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, IsCreatorCanView,)
    filter_backends = (filters.DjangoObjectPermissionsFilter,filters.DjangoFilterBackend,)
    filter_fields = ('school', 'user', 'year')
    queryset = SchoolRoster.objects.all()
    serializer_class = SchoolRosterSerializer


class ProfileViewSet(viewsets.ModelViewSet):
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('grade', 'age', 'gender', 'verified', 'emailCode', 'passwordCode')
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    

class ClassViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, IsCreatorCanEdit,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('name', 'identifier', 'school', 'isPublic')
    queryset = Class.objects.all()
    serializer_class = ClassSerializer


class ClassRosterViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, IsCreatorCanView,)
    filter_backends = (filters.DjangoObjectPermissionsFilter,filters.DjangoFilterBackend,)
    filter_fields = ('classFK', 'user')
    queryset = ClassRoster.objects.all()
    serializer_class = ClassRosterSerializer

class AssignmentRosterViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, IsCreatorCanView,)
    filter_backends = (filters.DjangoObjectPermissionsFilter,filters.DjangoFilterBackend,)
    filter_fields = ('assignment', 'user')
    queryset = AssignmentRoster.objects.all()
    serializer_class = AssignmentRosterSerializer

class AssignmentViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, IsCreatorCanEdit,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('name', 'startDate', 'dueDate', 'classFK', 'isPublic')
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer

class TaskViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, IsCreatorCanView,)
    filter_backends = (filters.DjangoObjectPermissionsFilter,filters.DjangoFilterBackend,)
    filter_fields = ('assignment', 'user', 'name', 'isDone', 'hoursPlanned', 'hoursCompleted', 'startDate', 'endDate', 'isApproved', 'dueDate', 'difficulty')
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

@api_view(['post'])
@authentication_classes([])
@permission_classes([])
def startGroupView(request):
    group, created = Group.objects.get_or_create(name='student')
    if created:
        appList = ['restAPI', 'auth', 'authtoken', 'contenttypes', 'corsheaders', 'guardian', 'sessions', 'oauth2_provider', 'social_auth']
        for app in appList:
            models = apps.get_app_config(app).get_models()
            for model in models:
                content_type = ContentType.objects.get_for_model(model)
                permissions = Permission.objects.filter(content_type=content_type)
                for permission in permissions:
                    group.permissions.add(permission)
        return Response({"status" : "group created"})
    else:
        return Response({'error': 'group already exists'},status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def oauth_code(request):
   g_code = request.GET['code']
   return Response(g_code)
