from django.shortcuts import render, reverse
from django.http import HttpResponse, Http404, HttpResponseRedirect, JsonResponse
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.contrib import messages
from django.contrib.auth import logout  
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.cache import never_cache
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.views.generic.base import TemplateView, ContextMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.core.signing import BadSignature
from django.core.paginator import Paginator
from django.db.models import Q
from .utilities import signer
from .models import SubRubric, Bb, PageHit
from .forms import SearchForm, BbForm, AIFormSet
from .decorators import counted

from .models import AdvUser, Comment, RecentBbs
from .forms import ChangeUserInfoForm, RegisterUserForm, UserCommentForm, GuestCommentForm


def polygon(request):
    if request.method == 'POST':
        sf = SearchForm(request.POST)
        if sf.is_valid():
            keyword = sf.cleaned_data['keyword']
            rubric_id = sf.cleaned_data['rubric'].pk
            bbs = Bb.objects.filter(title__icontains=keyword,
                                    rubric=rubric_id)
            context = {'form':sf, 'bbs':bbs}
            return render(request, 'layout/trash.html', context)
    else:
        sf = SearchForm()
    bbs = Bb.objects.order_by('-created_at')[:10]
    context = {'form':sf, 'bbs':bbs}
    return render(request, 'layout/trash.html', context)

def index(request):
    if request.method == 'POST':
        sf = SearchForm(request.POST)
        if sf.is_valid():
            keyword = sf.cleaned_data['keyword']
            rubric_id = sf.cleaned_data['rubric'].pk
            bbs = Bb.objects.filter(title__icontains=keyword,
                                    rubric=rubric_id)
            context = {'form':sf, 'bbs':bbs}
            return render(request, 'main/index3.html', context)
    else:
        sf = SearchForm()
    bbs = Bb.objects.order_by('-created_at')[:20]
    context = {'form':sf, 'bbs':bbs}
    return render(request, 'main/index3.html', context)


def other_page(request, page):
    try:
        template = get_template('main/' + page + '.html')
    except TemplateDoesNotExist:
        raise Http404
    return HttpResponse(template.render(request=request))


class BBLoginView(LoginView):
    template_name='main/login.html'

@login_required
def profile(request):
    bbs = Bb.objects.filter(author=request.user.pk)
    context = {'bbs':bbs}
    return render(request, 'main/profile_bbs.html', context)

@login_required
def profile_liked(request):
    bbs = Bb.objects.filter(likes=request.user.pk)
    context = {'bbs':bbs}
    return render(request, 'main/profile_liked.html', context)


class BBLogoutView(SuccessMessageMixin, LoginRequiredMixin, LogoutView, ContextMixin):
    template_name = 'main/index3.html'
    success_message = 'Вы успешно вышли из аккаунта'
    sf = SearchForm()
    bbs = Bb.objects.order_by('-created_at')[:20]
    extra_context = {'form':sf, 'bbs':bbs}

class ChangeUserInfoView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    model = AdvUser
    template_name = 'main/change_user_info.html'
    form_class = ChangeUserInfoForm
    success_url = reverse_lazy('main:profile')
    success_message = 'Данные пользователя изменены'

    def setup(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().setup(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.user_id)

class BBPasswordChangeView(SuccessMessageMixin, LoginRequiredMixin, PasswordChangeView):
    template_name = 'main/password_change.html'
    success_url = reverse_lazy('main:profile')
    success_message = 'Пароль пользователя изменён'


class RegisterUserView(SuccessMessageMixin, CreateView):
    model = AdvUser
    template_name = 'main/register_user.html'
    form_class = RegisterUserForm
    success_url = reverse_lazy('main:login')
    success_message = 'Пользователь зарегистрирован'

class RegisterDoneView(TemplateView):
    template_name = 'main/register_done.html'


def user_activate(request, sign):
    try:
        username = signer.unsign(sign)
    except BadSignature:
        return render(request, 'main/bad_signature.html')
    user = get_object_or_404(AdvUser, username=username)
    if user.is_activated:
        template = 'main/user_is_activated.html'
    else:
        template = 'main/activation_done.html'
        user.is_active = True
        user.is_activated = True
        user.save()
    return render(request, template)

class DeleteUserView(LoginRequiredMixin, DeleteView):
    model = AdvUser
    template_name = 'main/delete_user.html'
    success_url = reverse_lazy('main:index')

    def setup(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().setup(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        logout(request)
        messages.add_message(request, messages.SUCCESS,
                             'Пользователь удалён')
        return super().post(request, *args, **kwargs)

    def get_object(self, queryset = None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.user_id)

def by_rubric(request, pk):
    rubric = get_object_or_404(SubRubric, pk=pk)
    bbs = Bb.objects.filter(is_active=True, rubric=pk)
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        q = Q(title__icontains=keyword) | Q(content__icontains=keyword)
        bbs = bbs.filter(q)
    else:
        keyword = ''
    form = SearchForm(initial = {'keyword':keyword})
    paginator = Paginator(bbs, 2)
    if 'page' in request.GET:
        page_num = request.GET['page']
    else:
        page_num = 1
    page = paginator.get_page(page_num)
    context = {'rubric':rubric, 'page':page, 'bbs':page.object_list,
               'form':form}
    return render(request, 'main/by_rubric.html', context)

def save_recent_bb(user, bb):
    if not user.is_authenticated:
        pass
    else:
        recent = user.recentbbs_set.all().order_by('attended_at')
        for b in recent:
            if b.bb == bb:
                return None
        if len(recent) < 3:
            RecentBbs.objects.create(user=user, bb=bb)
        else:
            recent[0].delete()
            RecentBbs.objects.create(user=user, bb=bb)

@counted
def detail(request, rubric_pk, pk):
    bb = get_object_or_404(Bb, pk=pk)
    save_recent_bb(user=request.user, bb=bb)
    ais = bb.additionalimage_set.all()
    if request.method == 'POST':
        sf = SearchForm(request.POST)
        if sf.is_valid():
            keyword = sf.cleaned_data['keyword']
            rubric_id = sf.cleaned_data['rubric'].pk
            bbs = Bb.objects.filter(title__icontains=keyword,
                                    rubric=rubric_id)
            context = {'form':sf, 'bbs':bbs}
            return render(request, 'main/index2.html', context)
    else:
        bb.views += 1
        bb.save()
        bbs = Bb.objects.filter(title__icontains=bb.title[0], rubric=bb.rubric).exclude(pk=bb.pk)[:9]
        sf = SearchForm()
        liked = False
        if bb.likes.filter(id=request.user.id).exists():
            liked = True
        count_views = PageHit.objects.get(url=request.path).count
        context = {'liked':liked, 'bb':bb, 'ais':ais, 'form':sf, 'bbs':bbs, 'count_views':count_views}
        return render(request, 'main/detail.html', context)

@login_required
def profile_bb_detail(request, pk):
    bb = get_object_or_404(Bb, pk=pk)
    if bb.author != request.user:
        raise Http404
    save_recent_bb(user=request.user, bb=bb)
    ais = bb.additionalimage_set.all()
    if request.method == 'POST':
        sf = SearchForm(request.POST)
        if sf.is_valid():
            keyword = sf.cleaned_data['keyword']
            rubric_id = sf.cleaned_data['rubric'].pk
            bbs = Bb.objects.filter(title__icontains=keyword,
                                    rubric=rubric_id)
            context = {'form':sf, 'bbs':bbs}
            return render(request, 'main/index2.html', context)
    else:
        bb.views += 1
        bb.save()
        bbs = Bb.objects.filter(title__icontains=bb.title[0], rubric=bb.rubric)[:9]
        sf = SearchForm()
        liked = False
        if bb.likes.filter(id=request.user.id).exists():
            liked = True
        context = {'liked':liked, 'bb':bb, 'ais':ais, 'form':sf, 'bbs':bbs}
        return render(request, 'main/detail.html', context)

@login_required
def profile_bb_add(request):
    if request.method == 'POST':
        form = BbForm(request.POST, request.FILES)
        if form.is_valid():
            bb = form.save()
            formset = AIFormSet(request.POST, request.FILES, instance=bb)
            if formset.is_valid():
                formset.save()
                messages.add_message(request, messages.SUCCESS,
                                     'Объявление добавлено')
                return redirect('main:profile')
        else:
            formset = AIFormSet()
    else:
        form = BbForm(initial={'author':request.user.pk})
        formset = AIFormSet()
    context = {'form':form, 'formset':formset}
    return render(request, 'main/profile_bb_add.html', context)

@login_required
def profile_bb_change(request, pk):
    bb = get_object_or_404(Bb, pk=pk)
    if request.method == 'POST':
        form = BbForm(request.POST, request.FILES, instance = bb)
        if form.is_valid():
            bb = form.save()
            formset = AIFormSet(request.POST, request.FILES, instance=bb)
            if formset.is_valid():
                bb = form.save()
                messages.add_message(request, messages.SUCCESS,
                                     'Объявление исправлено')
                return redirect('main:profile')
    else:
        form = BbForm(instance = bb)
        formset = AIFormSet(instance = bb)
    context = {'form':form, 'formset':formset}
    return render(request, 'main/profile_bb_change.html', context)

@login_required
def profile_bb_delete(request, pk):
    bb = get_object_or_404(Bb, pk = pk)
    if request.method == 'POST':
        bb.delete()
        messages.add_message(request, messages.SUCCESS,
                             'Объявление удалено')
        return redirect('main:profile')
    else:
        context = {'bb':bb}
        return render(request, 'main/profile_bb_delete.html', context)


@login_required
def LikeView(request):
    if request.POST.get('action') == 'post':
        result = ''
        id = int(request.POST.get('bb_id'))
        bb = get_object_or_404(Bb, id=id)
        if bb.likes.filter(id=request.user.id).exists():
            bb.likes.remove(request.user)
            bb.likes_count -= 1
            result = '<i class="far fa-heart" style="color:#009cf0;"></i>\nДобавить в избранное'
        else:
            bb.likes.add(request.user)
            bb.likes_count += 1
            result = '<i class="fas fa-heart" style="color:#009cf0;"></i>\nВ избранном'
        bb.save()
        return JsonResponse({'result': result, })

def foreign_user(request, pk):
    foreignuser = get_object_or_404(AdvUser, pk=pk)
    bbs = Bb.objects.filter(author=foreignuser)
    context = {'fuser':foreignuser, 'bbs':bbs}
    return render(request, 'main/foreign_user.html', context)
