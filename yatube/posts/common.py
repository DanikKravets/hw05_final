from django.core.paginator import Paginator


def paginator(request, post_list, AMOUNT):

    paginator = Paginator(post_list, AMOUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj
