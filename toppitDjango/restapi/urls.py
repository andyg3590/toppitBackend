from django.conf.urls import url, include
from rest_framework import routers
#from restAPI import views
from . import views
from rest_framework.authtoken import views as authviews
from rest_framework.urlpatterns import format_suffix_patterns

router = routers.DefaultRouter()
router.register(r'school', views.SchoolViewSet)
router.register(r'schoolRoster', views.SchoolRosterViewSet)
router.register(r'profile', views.ProfileViewSet)
router.register(r'class', views.ClassViewSet)
router.register(r'classRoster', views.ClassRosterViewSet)
router.register(r'assignment', views.AssignmentViewSet)
router.register(r'assignmentRoster', views.AssignmentRosterViewSet)
router.register(r'task', views.TaskViewSet)
router.register(r'user', views.UserViewSet)
router.register(r'group', views.GroupViewSet)


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^login/', authviews.obtain_auth_token, name="login"),
    url(r'^receive/emailCode/(?P<code>[a-z0-9]+)/', views.receiveEmailCode),
    url(r'^send/emailCode/', views.sendEmailCode),
    url(r'^send/passwordCode/(?P<email>[a-z0-9@.]+)/', views.sendPasswordCode),
    url(r'^changePassword/(?P<code>[a-z0-9]+)/', views.changePassword),
    url(r'^getAssigProgress/(?P<pk>[a-z0-9]+)/', views.getAssigProgressView),
    url(r'^collab/assig/(?P<pk>[a-z0-9]+)/', views.CollabView),
    url(r'^dashboard/', views.DashboardView),
    url(r'^startGroup/', views.startGroupView),
    url(r'^myClasses/', views.MyClassesView),
    # url(r'^auth/(?P<usr>[a-z0-9]+)/(?P<pw>[a-z0-9]+)/$', views.AuthView.as_view()),
]
