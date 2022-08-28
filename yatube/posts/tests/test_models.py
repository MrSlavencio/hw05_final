from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=('Тестовый пост, который должен быть '
                  'больше 15 символов, т.к. __str__ должен '
                  'вернуть именно столько!'),
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        show_first = 15
        post = PostModelTest.post
        self.assertEqual(post.__str__(), post.text[:show_first])
        group = PostModelTest.group
        self.assertEqual(group.__str__(), group.title)

    def test_post_verbose_name(self):
        """verbose_name модели Post совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст',
            'created': 'Дата создания',
            'author': 'Автор',
            'group': 'Группа',
            'image': 'Картинка'
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_group_verbose_name(self):
        """verbose_name модели Group совпадает с ожидаемым."""
        group = PostModelTest.group
        field_verboses = {
            'title': 'Заголовок',
            'slug': 'Слаг',
            'description': 'Описание',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name, expected_value)

    def test_post_help_text(self):
        """help_text модели Post в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Текст поста',
            'created': 'Дата создания',
            'author': 'Автор поста',
            'group': 'Группа, к которой относится пост',
            'image': 'Изображение к посту'
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)

    def test_group_help_text(self):
        """help_text модели Group в полях совпадает с ожидаемым."""
        group = PostModelTest.group
        field_help_texts = {
            'title': 'Название группы',
            'slug': 'Адрес для страницы с группой',
            'description': 'Описание группы',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).help_text, expected_value)
