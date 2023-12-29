from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole:
    USER = 'user'
    ADMIN = 'admin'
    choices = [
        (USER, 'USER'),
        (ADMIN, 'ADMIN'),
    ]


class User(AbstractUser):
    """Модель пользователя."""

    username = models.CharField(
        max_length=150,
        unique=True,
        blank=False,
        null=False,
        verbose_name='Логин',
    )

    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='Адрес email',
    )

    first_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Имя',
    )

    last_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Фамилия',
    )

    role = models.TextField(
        choices=UserRole.choices,
        default=UserRole.USER,
        verbose_name='Статус',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    @property
    def is_user(self):
        return self.role == UserRole.USER

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN or self.is_superuser

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return self.username


class Follow(models.Model):
    """Определяет модель для подписки на авторов ."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Кто подписывается',
        db_index=False,
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='На кого подписывается',
        db_index=False,
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author'),
        ]

    def __str__(self):
        return f'{self.user} подписался на {self.author}'
