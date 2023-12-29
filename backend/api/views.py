from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (SAFE_METHODS, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Follow, User

from .filters import IngredientsSearchFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAdminOrReadOnly
from .report_utils import download_shopping_cart
from .serializers import (CreateRecipeSerializer, FollowSerializer,
                          IngredientSerializer, RecipeSerializer,
                          ShortRecipeSerializer, TagSerializer,
                          UsersSerializer)


class UsersViewSet(UserViewSet):
    """Реализовывает подписки пользователя."""

    queryset = User.objects.all()
    serializer_class = UsersSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, **kwargs):
        id = self.kwargs.get('id')
        author = get_object_or_404(User, id=id)
        serializer = FollowSerializer(
            data={'user': request.user.id, 'author': author.id}
        )

        if request.method == 'POST':
            serializer = FollowSerializer(
                author,
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            Follow.objects.create(user=request.user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        subscription = get_object_or_404(Follow,
                                         user=request.user, author=author)
        self.perform_destroy(subscription)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=request.user)
        subscriptions = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            subscriptions, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(viewsets.ModelViewSet):
    """Работа с ингредиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientsSearchFilter


class TagViewSet(viewsets.ModelViewSet):
    """Работа с тегами."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrReadOnly]


class RecipeViewSet(viewsets.ModelViewSet):
    """Работа с рецептами."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAdminOrReadOnly, IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return CreateRecipeSerializer

    def add_method(self, model, request, pk):
        if model.objects.filter(user=request.user, recipe__id=pk).exists():
            return Response(
                {'Уже существует.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=request.user, recipe=recipe)
        serializer = ShortRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_method(self, model, request, pk):
        objects = model.objects.filter(user=request.user, recipe__id=pk)
        if objects.exists():
            objects.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Не найден.'},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            return self.add_method(ShoppingCart, request, pk)
        return self.delete_method(ShoppingCart, request, pk)

    @action(
        detail=False, permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        return download_shopping_cart(self, request)

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        if request.method == 'POST':
            return self.add_method(Favorite, request, pk)
        return self.delete_method(Favorite, request, pk)
