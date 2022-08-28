from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus
from django.core.cache import cache

from posts.models import Group, Post

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.post_author,
            text='Тестовый текст поста',
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author_client = Client()
        self.post_author_client.force_login(TaskURLTests.post_author)

    def test_guest_client_urls(self):
        """Проверка URLs для гостя."""
        urls_asset = {
            '/': HTTPStatus.OK,
            f'/group/{TaskURLTests.group.slug}/': HTTPStatus.OK,
            f'/profile/{TaskURLTests.post_author.username}/': HTTPStatus.OK,
            f'/posts/{TaskURLTests.post.id}/': HTTPStatus.OK,
            f'/posts/{TaskURLTests.post.id}/edit/': HTTPStatus.FOUND,
            '/create/': HTTPStatus.FOUND,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
            '/follow/': HTTPStatus.FOUND,
            f'/profile/{TaskURLTests.post_author.username}/follow/': HTTPStatus.FOUND,
            f'/profile/{TaskURLTests.post_author.username}/follow/': HTTPStatus.FOUND,
        }
        for url, status_code in urls_asset.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_authorized_client_urls(self):
        """Проверка URLs для авторизованного пользователя."""
        urls_asset = {
            '/': HTTPStatus.OK,
            f'/group/{TaskURLTests.group.slug}/': HTTPStatus.OK,
            f'/profile/{TaskURLTests.post_author.username}/': HTTPStatus.OK,
            f'/posts/{TaskURLTests.post.id}/': HTTPStatus.OK,
            f'/posts/{TaskURLTests.post.id}/edit/': HTTPStatus.FOUND,
            '/create/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
            '/follow/': HTTPStatus.OK,
            f'/profile/{TaskURLTests.post_author.username}/follow/': HTTPStatus.FOUND,
            f'/profile/{TaskURLTests.post_author.username}/follow/': HTTPStatus.FOUND,
        }
        for url, status_code in urls_asset.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_post_author_client_urls(self):
        """Проверка URLs для автора поста."""
        urls_asset = {
            '/': HTTPStatus.OK,
            f'/group/{TaskURLTests.group.slug}/': HTTPStatus.OK,
            f'/profile/{TaskURLTests.post_author.username}/': HTTPStatus.OK,
            f'/posts/{TaskURLTests.post.id}/': HTTPStatus.OK,
            f'/posts/{TaskURLTests.post.id}/edit/': HTTPStatus.OK,
            '/create/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
            '/follow/': HTTPStatus.OK,
            f'/profile/{TaskURLTests.post_author.username}/follow/': HTTPStatus.FOUND,
            f'/profile/{TaskURLTests.post_author.username}/unfollow/': HTTPStatus.FOUND,
        }
        for url, status_code in urls_asset.items():
            with self.subTest(url=url):
                response = self.post_author_client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names_for_author = {
            '/': 'posts/index.html',
            f'/group/{TaskURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{TaskURLTests.post_author.username}/':
            'posts/profile.html',
            f'/posts/{TaskURLTests.post.id}/': 'posts/post_detail.html',
            f'/posts/{TaskURLTests.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/unexisting_page/': 'core/404.html',
            '/follow/': 'posts/index.html',
        }
        for address, template in templates_url_names_for_author.items():
            with self.subTest(address=address):
                response = self.post_author_client.get(address)
                self.assertTemplateUsed(response, template)

        cache.clear()
        templates_url_names_for_guest = {
            '/': 'posts/index.html',
            f'/group/{TaskURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{TaskURLTests.post_author.username}/':
            'posts/profile.html',
            f'/posts/{TaskURLTests.post.id}/': 'posts/post_detail.html',
            '/unexisting_page/': 'core/404.html',
        }
        for address, template in templates_url_names_for_guest.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
