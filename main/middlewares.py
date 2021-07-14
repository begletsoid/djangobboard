from .models import SubRubric
from .models import SuperRubric
from .forms import SearchForm

def bboard_context_processor(request):
    context = {}
    context['rubrics'] = SubRubric.objects.all()
    context['keyword'] = ''
    context['all'] = ''
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            context['keyword'] = '?keyword' + keyword
            context['all'] = context['keyword']
    if 'page' in request.GET:
        page = request.GET['page']
        if page != '1':
            if context['all']:
                context['all'] += '&page=' + page
            else:
                context['all'] = '?page' + page
    return context

def add_superrubrics(request):
    return {'superrubrics': SuperRubric.objects.all().exclude(name='Все'),
            'form':SearchForm()}