from django.urls import path
from .views import other_page, BBLoginView, index, BBLogoutView, profile
from .views import ChangeUserInfoView, BBPasswordChangeView, RegisterUserView
from .views import RegisterDoneView, user_activate, DeleteUserView, by_rubric, by_superrubric
from .views import detail, profile_bb_detail, profile_bb_add
from .views import profile_bb_change, profile_bb_delete, polygon, profile_liked
from .views import LikeView, foreign_user


app_name = 'main'
urlpatterns = [
    path('polygon/', polygon, name='polygon'),
    path('user/<int:pk>/', foreign_user, name='foreign_user'),
    path('accounts/register/activate/<str:sign>/', user_activate, name='register_activate'),
    path('accounts/register/done/', RegisterDoneView.as_view(), name='register_done'),
    path('accounts/register/', RegisterUserView.as_view(), name='register'),
    path('accounts/logout/', BBLogoutView.as_view(), name='logout'),
    path('accounts/profile/liked/', profile_liked, name='profile_liked'),
    path('accounts/profile/delete/', DeleteUserView.as_view(), name='profile_delete'),
    path('accounts/password/change/', BBPasswordChangeView.as_view(), name='password_change'),
    path('accounts/profile/change/', ChangeUserInfoView.as_view(),
                                        name='profile_change'),
    path('accounts/profile/change/<int:pk>/', profile_bb_change,
                                                name='profile_bb_change'),
    path('accounts/profile/delete/<int:pk>/', profile_bb_delete,
                                                name='profile_bb_delete'),
    path('accounts/profile/add/', profile_bb_add, name='profile_bb_add'),
    path('accounts/profile/<int:pk>/', profile_bb_detail, name='profile_bb_detail'),
    path('accounts/profile/', profile, name='profile'),
    path('accounts/login/', BBLoginView.as_view(), name='login'),
    path('like_bb/', LikeView, name='like_bb'),
    path('<int:rubric_pk>/<int:pk>/', detail, name='detail'),
    path('<int:pk>/', by_rubric, name='by_rubric'),
    path('super/<int:pk>/', by_superrubric, name='by_superrubric'),
    path('<str:page>/', other_page, name='other' ),
    path('', index, name='index'),
]