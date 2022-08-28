import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from itertools import islice
from posts.models import Group, Post, Comment, Follow
from django.core.cache import cache

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.post_author,
            text='Тестовый текст поста',
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.post.author,
            text='Тестовый текст комментария'
        )

        cls.posts_assets = [
            cls.post,
        ]

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author_client = Client()
        self.post_author_client.force_login(PostURLTests.post_author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names_for_author = {
            reverse('posts:index'): 'posts/index.html',
            (reverse('posts:group_list',
                     kwargs={'slug': PostURLTests.group.slug})):
            'posts/group_list.html',
            (reverse('posts:profile',
                     kwargs={'username': PostURLTests.post.author.username})):
            'posts/profile.html',
            (reverse('posts:post_detail',
                     kwargs={'post_id': PostURLTests.post.id})):
            'posts/post_detail.html',
            (reverse('posts:post_edit',
                     kwargs={'pk': PostURLTests.post.id})):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/index.html',
        }
        for reverse_name, template in templates_pages_names_for_author.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.post_author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
        cache.clear()
        templates_pages_names_for_guest = {
            reverse('posts:index'): 'posts/index.html',
            (reverse('posts:group_list',
                     kwargs={'slug': PostURLTests.group.slug})):
            'posts/group_list.html',
            (reverse('posts:profile',
                     kwargs={'username': PostURLTests.post.author.username})):
            'posts/profile.html',
            (reverse('posts:post_detail',
                     kwargs={'post_id': PostURLTests.post.id})):
            'posts/post_detail.html',
        }
        for reverse_name, template in templates_pages_names_for_guest.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        """Шаблон home сформирован с правильным контекстом."""
        response = self.post_author_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        self.assertEqual(post_text_0, PostURLTests.post.text)
        if first_object.group:
            post_group_0 = first_object.group.title
            self.assertEqual(post_group_0, PostURLTests.post.group.title)
        post_author_0 = first_object.author
        self.assertEqual(post_author_0, PostURLTests.post.author)
        post_created_date_0 = first_object.created
        self.assertEqual(post_created_date_0, PostURLTests.post.created)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = (self.post_author_client
                    .get(reverse('posts:group_list',
                                 kwargs={'slug': PostURLTests.group.slug})))
        if response.context['page_obj']:
            first_object = response.context['page_obj'][0]
            post_text_0 = first_object.text
            self.assertEqual(post_text_0, PostURLTests.post.text)
            post_group_0 = first_object.group.title
            self.assertEqual(post_group_0, PostURLTests.post.group.title)
            group_description_0 = first_object.group.description
            self.assertEqual(group_description_0,
                             PostURLTests.post.group.description)
            post_author_0 = first_object.author
            self.assertEqual(post_author_0, PostURLTests.post.author)
            post_created_date_0 = first_object.created
            self.assertEqual(post_created_date_0, PostURLTests.post.created)

    def test_group_list_correct_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом.
        В тестовой группе №2 нет записей.
        """
        response = (self.post_author_client
                    .get(reverse('posts:group_list',
                                 kwargs={'slug': PostURLTests.group_2.slug})))
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (self.post_author_client
                    .get(reverse('posts:profile',
                                 kwargs=({
                                     'username':
                                     PostURLTests.post_author.username
                                 }))))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        self.assertEqual(post_text_0, PostURLTests.post.text)
        if first_object.group:
            post_group_0 = first_object.group.title
            self.assertEqual(post_group_0, PostURLTests.post.group.title)
        post_author_0 = first_object.author
        self.assertEqual(post_author_0, PostURLTests.post.author)
        post_created_date_0 = first_object.created
        self.assertEqual(post_created_date_0, PostURLTests.post.created)
        user_num_posts_0 = len(response.context['page_obj'])
        self.assertEqual(user_num_posts_0, len(PostURLTests.posts_assets))

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.post_author_client.
                    get(reverse('posts:post_detail',
                                kwargs={'post_id': PostURLTests.post.id})))
        self.assertEqual(response.context.get('post').created,
                         PostURLTests.post.created)
        self.assertEqual(response.context.get('post').text,
                         PostURLTests.post.text)
        self.assertEqual(response.context.get('post').author,
                         PostURLTests.post.author)
        self.group = response.context.get('post').group
        if self.group:
            self.assertEqual(self.group, PostURLTests.post.group)
        self.comment = response.context.get('comments')
        if self.comment:
            self.first_comment = self.comment[0]
            self.assertEqual(self.first_comment.text,
                             PostURLTests.comment.text)

    def test_edit_post_page_show_correct_context(self):
        """Шаблон edit_post сформирован с правильным контекстом."""
        response = self.post_author_client.get(reverse('posts:post_edit',
                                                       kwargs={
                                                           'pk':
                                                           PostURLTests.post
                                                           .id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.post_author_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_with_group_exist_in_index_page(self):
        """Если создать пост, в котором указана группа,
        он попадет на главную страницу."""
        response = self.post_author_client.get(reverse('posts:index'))
        posts_num = len(response.context['page_obj'])
        self.post = Post.objects.create(
            author=PostURLTests.post_author,
            text='Тестовый текст поста',
            group=PostURLTests.group,
        )
        cache.clear()
        self.assertEqual(posts_num + 1,
                         len(self.post_author_client
                             .get(reverse('posts:index')).context['page_obj']))

    def test_post_with_group_exist_in_group_list_page(self):
        """Если создать пост, в котором указана группа,
        он попадет на страницу постов группы."""
        response = self.post_author_client.get(reverse('posts:group_list',
                                                       kwargs={'slug':
                                                               PostURLTests
                                                               .group.slug}))
        posts_num = len(response.context['page_obj'])
        self.post = Post.objects.create(
            author=PostURLTests.post_author,
            text='Тестовый текст поста',
            group=PostURLTests.group,
        )
        self.assertEqual(posts_num + 1,
                         len(self.post_author_client
                             .get(reverse('posts:group_list',
                                          kwargs={'slug':
                                                  PostURLTests.group.slug}))
                                 .context['page_obj']))

    def test_post_with_group_exist_in_profile_page(self):
        """Если создать пост, в котором указана группа,
        он попадет на страницу профиля автора."""
        response = self.post_author_client.get(reverse('posts:profile',
                                                       kwargs={'username':
                                                               PostURLTests
                                                               .post_author}))
        posts_num = len(response.context['page_obj'])
        self.post = Post.objects.create(
            author=PostURLTests.post_author,
            text='Тестовый текст поста',
            group=PostURLTests.group,
        )
        self.assertEqual(posts_num + 1,
                         len(self.post_author_client
                             .get(reverse('posts:profile',
                                          kwargs={'username':
                                                  PostURLTests.post_author}))
                                 .context['page_obj']))

    def test_post_added_to_correct_group(self):
        """Если создать пост, в котором указана группа,
        он попадет в правильную группу."""
        group_num_post = Post.objects.filter(group=PostURLTests.group).count()
        group_num_post_2 = (Post.objects.filter(group=PostURLTests.group_2)
                            .count())
        self.post = Post.objects.create(
            author=PostURLTests.post_author,
            text='Тестовый текст поста',
            group=PostURLTests.group,
        )
        self.assertEqual(group_num_post + 1,
                         Post.objects.filter(group=PostURLTests.group).count())
        self.assertEqual(group_num_post_2,
                         Post.objects.filter(group=PostURLTests.group_2)
                         .count())

    def test_follow_function(self):
        """Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок."""
        num_follows = Follow.objects.count()
        self.authorized_client.get(reverse('posts:profile_follow',
                                   kwargs={'username': PostURLTests
                                           .post_author}))
        self.assertEqual(num_follows + 1, Follow.objects.count())
        self.authorized_client.get(reverse('posts:profile_unfollow',
                                   kwargs={'username': PostURLTests
                                           .post_author}))
        self.assertEqual(num_follows, Follow.objects.count())

    def test_posts_for_followers(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан."""
        self.user_follower = User.objects.create_user(username='follower')
        self.follower_client = Client()
        self.follower_client.force_login(self.user_follower)
        self.post_author2 = User.objects.create_user(username='post_author2')
        self.author2_client = Client()
        self.author2_client.force_login(self.post_author2)
        Follow(user=self.user, author=PostURLTests.post_author).save()
        Follow(user=self.user_follower, author=PostURLTests.post_author).save()
        Follow(user=self.user_follower, author=self.post_author2).save()
        response_user_before = (self.authorized_client
                                .get(reverse('posts:follow_index')))
        first_object_user_before = response_user_before.context['page_obj'][0]
        self.assertEqual(first_object_user_before.text, PostURLTests.post.text)
        response_follower_before = (self.follower_client
                                    .get(reverse('posts:follow_index')))
        first_object_follower_before = (response_follower_before
                                        .context['page_obj'][0])
        self.assertEqual(first_object_follower_before.text,
                         PostURLTests.post.text)
        self.post_for_followers = Post.objects.create(
            author=self.post_author2,
            text='Тестовый текст поста для подписчиков')
        response_user_after = (self.authorized_client
                               .get(reverse('posts:follow_index')))
        first_object_user_after = response_user_after.context['page_obj'][0]
        self.assertNotEqual(first_object_user_after.text,
                            self.post_for_followers.text)
        response_follower_after = (self.follower_client
                                   .get(reverse('posts:follow_index')))
        first_object_follower_after = (response_follower_after
                                       .context['page_obj'][0])
        self.assertEqual(first_object_follower_after.text,
                         self.post_for_followers.text)

    def test_cache_index(self):
        """Тестирование кэширования главной страницы."""
        self.new_post = Post.objects.create(
            author=PostURLTests.post_author,
            text='Новый тестовый текст')
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        self.new_post.delete()
        response_old = self.authorized_client.get(reverse('posts:index'))
        posts_old = response_old.content
        self.assertEqual(posts, posts_old)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        posts_new = response_new.content
        self.assertNotEqual(posts, posts_new)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.OBJS_IN_PAGE = 10
        cls.post_author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        batch_size = 100
        objs = (Post(text='Тестовый текст поста %s' % i,
                     author=cls.post_author,
                     group=cls.group) for i in range(12))
        while True:
            batch = list(islice(objs, batch_size))
            if not batch:
                break
            Post.objects.bulk_create(batch, batch_size)

    def setUp(self):
        cache.clear()
        self.post_author_client = Client()
        self.post_author_client.force_login(PaginatorViewsTest.post_author)

    def test_home_page_contains_ten_records(self):
        """Домашняя страница содержит не более 10 записей."""
        response = self.post_author_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']),
                         PaginatorViewsTest.OBJS_IN_PAGE)

    def test_group_list_page_contains_ten_records(self):
        """На странице группы содержится не более 10 записей."""
        response = self.post_author_client.get(reverse('posts:group_list',
                                                       kwargs={
                                                           'slug':
                                                           PaginatorViewsTest
                                                           .group
                                                           .slug}))
        self.assertEqual(len(response.context['page_obj']),
                         PaginatorViewsTest.OBJS_IN_PAGE)

    def test_profile_page_contains_ten_records(self):
        """На странице профиля содержится не более 10 записей."""
        response = (self.post_author_client
                    .get(reverse('posts:profile',
                                 kwargs={'username': PaginatorViewsTest
                                         .post_author.username})))
        self.assertEqual(len(response.context['page_obj']),
                         PaginatorViewsTest.OBJS_IN_PAGE)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostImagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.post_author,
            text='Тестовый текст поста',
            group=cls.group,
            image=cls.image
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.post_author_client = Client()
        self.post_author_client.force_login(PostImagesTests.post_author)

    def test_index_page_contain_img(self):
        """Шаблон index содержит изображение."""
        response = self.post_author_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_img_0 = first_object.image
        self.assertEqual(post_img_0, PostImagesTests.post.image)

    def test_profile_page_contain_img(self):
        """Шаблон profile содержит изображение."""
        response = self.post_author_client.get(reverse('posts:profile',
                                                       kwargs={'username':
                                                               PostImagesTests
                                                               .post_author
                                                               .username}))
        first_object = response.context['page_obj'][0]
        post_img_0 = first_object.image
        self.assertEqual(post_img_0, PostImagesTests.post.image)

    def test_group_list_page_contain_img(self):
        """Шаблон с постами группы содержит изображение."""
        response = self.post_author_client.get(reverse('posts:group_list',
                                                       kwargs={'slug':
                                                               PostImagesTests
                                                               .group
                                                               .slug}))
        first_object = response.context['page_obj'][0]
        post_img_0 = first_object.image
        self.assertEqual(post_img_0, PostImagesTests.post.image)

    def test_post_detail_page_contain_img(self):
        """Шаблон с постом содержит изображение."""
        response = (self.post_author_client.
                    get(reverse('posts:post_detail',
                                kwargs={'post_id': PostImagesTests.post.id})))
        self.assertEqual(response.context.get('post').image,
                         PostImagesTests.post.image)
