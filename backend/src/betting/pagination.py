from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict


class BettingPagination(PageNumberPagination):
    """
    Кастомная пагинация для betting приложения
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('page_size', self.page_size),
            ('results', data)
        ]))


class GameRoundPagination(BettingPagination):
    """
    Пагинация для игровых раундов
    """
    page_size = 15
    

class BetPagination(BettingPagination):
    """
    Пагинация для ставок
    """
    page_size = 25


class NewsPagination(BettingPagination):
    """
    Пагинация для новостей
    """
    page_size = 20
