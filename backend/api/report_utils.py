from django.db.models import Sum
from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from recipes.models import IngredientRecipe


@action(
    detail=False, permission_classes=[IsAuthenticated]
)
def download_shopping_cart(self, request):
    ingredients = IngredientRecipe.objects.filter(
        recipe__shopping_cart__user=request.user
    ).values(
        'ingredient__name',
        'ingredient__measurement_unit'
    ).annotate(amount_sum=Sum('amount'))
    shop_list = '\n'.join([
        f'* {row["ingredient__name"]} '
        f'({row["ingredient__measurement_unit"]})'
        f' - {row["amount_sum"]}'
        for row in ingredients])
    return HttpResponse(shop_list, content_type='text/plain')
