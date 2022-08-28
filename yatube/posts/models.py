from django.db import models
from django.contrib.auth import get_user_model
from core.models import CreatedModel

User = get_user_model()


class Post(CreatedModel):
    text = models.TextField(
        verbose_name='Текст',
        help_text='Текст поста'
    )
    """
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        help_text='Дата публикации поста'
    )
    """
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='posts',
        help_text='Автор поста'
    )
    group = models.ForeignKey(
        'Group',
        verbose_name='Группа',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='group',
        help_text='Группа, к которой относится пост'
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='posts/',
        blank=True,
        help_text='Изображение к посту'
    )

    def __str__(self):
        len_to_show: int = 15
        return self.text[:len_to_show]

    class Meta:
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'
        ordering = ['-created']


class Group(models.Model):
    title = models.CharField(
        verbose_name='Заголовок',
        max_length=200,
        help_text='Название группы'
    )
    slug = models.SlugField(
        verbose_name='Слаг',
        unique=True,
        help_text='Адрес для страницы с группой'
    )
    description = models.TextField(
        verbose_name='Описание',
        help_text='Описание группы'
    )

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self):
        return self.title


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        verbose_name='Пост',
        on_delete=models.CASCADE,
        related_name='comments',
        help_text='Ссылка на пост'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор комментария',
        on_delete=models.CASCADE,
        related_name='comments',
        help_text='Автор комментария'
    )
    text = models.TextField(
        verbose_name='Текст',
        help_text='Текст комментария'
    )
    """
    created = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        help_text='Дата публикации комментария'
    )
    """

    def __str__(self):
        len_to_show: int = 15
        return self.text[:len_to_show]

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['-created']


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='follower',
        help_text='Пользователь, который подписывается'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='following',
        help_text='Пользователь, на которого подписываются'
    )

    def __str__(self):
        return f'{self.user}&{self.author}'

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
