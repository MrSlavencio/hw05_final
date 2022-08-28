import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from posts.forms import PostForm
from posts.models import Post, Comment
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_author = User.objects.create_user(username='auther')
        cls.form = PostForm()
        cls.post = Post.objects.create(
            author=cls.post_author,
            text='Тестовый текст поста',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='authorized')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author_client = Client()
        self.post_author_client.force_login(PostCreateFormTests.post_author)

    def test_create_post_by_authored_user(self):
        """Валидная форма, заполненная авторизованным пользователем,
        создает запись в Post."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст из формы',
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username':
                                             self
                                             .user.username}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(Post.objects.get(author=self.user).text,
                         form_data['text'])

    def test_create_post_by_guest(self):
        """Валидная форма, заполненная гостем,
        не создает запись в Post."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст из формы',
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             f"{reverse('users:login')}?next=%2Fcreate%2F")
        self.assertEqual(Post.objects.count(), post_count)

    def test_edit_post_by_post_author(self):
        """Валидная форма, заполненная автором поста, меняет запись в Post."""
        post_count = Post.objects.count()
        post_to_edit = Post.objects.get(pk=PostCreateFormTests.post.pk)
        new_form_data = {
            'text': 'Новый текст тестового поста',
        }
        response = self.post_author_client.post(
            reverse('posts:post_edit', kwargs={'pk': post_to_edit.pk}),
            data=new_form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id':
                                             PostCreateFormTests.post.pk}))
        self.assertEqual(Post.objects.get(pk=PostCreateFormTests.post.pk).text,
                         new_form_data['text'])
        self.assertEqual(post_count, Post.objects.count())

    def test_edit_post_by_authorized_client(self):
        """Авторизованный пользователь (не автор) не может
        редактировать пост."""
        post_count = Post.objects.count()
        post_to_edit = Post.objects.get(pk=PostCreateFormTests.post.pk)
        new_form_data = {
            'text': 'Новый текст тестового поста',
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'pk': post_to_edit.pk}),
            data=new_form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id':
                                             PostCreateFormTests.post.pk}))
        self.assertEqual(Post.objects.get(pk=PostCreateFormTests.post.pk).text,
                         PostCreateFormTests.post.text)
        self.assertEqual(post_count, Post.objects.count())

    def test_edit_post_by_guest(self):
        """Авторизованный пользователь (не автор) не может
        редактировать пост."""
        post_count = Post.objects.count()
        post_to_edit = Post.objects.get(pk=PostCreateFormTests.post.pk)
        new_form_data = {
            'text': 'Новый текст тестового поста',
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'pk': post_to_edit.pk}),
            data=new_form_data,
            follow=True
        )
        self.assertRedirects(response,
                             (f"{reverse('users:login')}?next=%2Fposts%2F"
                              f"{PostCreateFormTests.post.pk}%2Fedit%2F"))
        self.assertEqual(Post.objects.get(pk=PostCreateFormTests.post.pk).text,
                         PostCreateFormTests.post.text)
        self.assertEqual(post_count, Post.objects.count())

    def test_create_post_with_image(self):
        """Валидная форма с изображением, заполненная авторизованным
        пользователем, создает запись в Post."""
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст из формы',
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username':
                                             self
                                             .user.username}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(Post.objects.get(author=self.user).text,
                         form_data['text'])

    def test_comments_by_authorized_client(self):
        """Комментировать посты может авторизованный пользователь.
        После заполнения формы с комментарием, комментарий добавляется в БД."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый текст комментария',
        }
        self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': PostCreateFormTests.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(comments_count + 1, Comment.objects.count())
        self.assertEqual(Comment.objects
                         .get(post_id=PostCreateFormTests.post.id).text,
                         form_data['text'])

    def test_comments_by_guest_client(self):
        """Неавторизованный пользователь не может комментировать посты.
        После заполнения формы с комментарием,
        комментарий не добавляется в БД."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый текст комментария',
        }
        self.guest_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': PostCreateFormTests.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(comments_count, Comment.objects.count())
