import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.form = PostForm()

        cls.user = User.objects.create_user(username='TestName')

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Test Group',
            slug='test_group',
            description='Тестовое описание',
        )

    def test_creation_post(self):
        """Проверка создания поста"""
        posts_count = Post.objects.count()

        form_data = {
            'text': 'New post text into form',
            'group': self.group.id,
            'image': self.uploaded,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        error1 = 'Данные поста не совпадают'
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(Post.objects.filter(
            text=form_data['text'],
            group=form_data['group'],
            image='posts/small.gif',
            author=self.user
        ).exists(), error1)

        error2 = 'Пост не добавлен в базу данных'
        self.assertEqual(Post.objects.count(), (posts_count + 1), error2)

    def test_post_edit(self):
        """Проверка прав редактирования"""
        self.post = Post.objects.create(
            text='Test text',
            author=self.user,
            group=self.group,
        )
        posts_count = Post.objects.count()

        post_v1 = self.post

        self.group2 = Group.objects.create(
            title='Test Group 2',
            slug='test_group_2',
            description='test description',
        )

        form_data = {
            'text': 'New test text',
            'group': self.group2.id,
        }

        response = self.authorized_client.post(
            reverse(
                'posts:post_edit', kwargs={'post_id': post_v1.id}
            ),
            data=form_data,
            follow=True,
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

        error1 = 'Данные обновленного поста не совпадают'

        self.assertTrue(Post.objects.filter(
            text=form_data['text'],
            group=form_data['group'],
            author=self.user,
            pub_date=self.post.pub_date,
        ).exists(), error1)

        error1 = 'Пользователь не может обновить текст поста'
        self.assertNotEqual(post_v1.text, form_data['text'], error1)
        error2 = 'Пользователь не может изменить группу поста'
        self.assertNotEqual(post_v1.group, form_data['group'], error2)
        error2 = 'При редактировании поста создались еще посты'
        self.assertEqual(Post.objects.count(), posts_count, error2)

    def test_group_null(self):
        """Проверка возможности не указывать группу"""
        self.post = Post.objects.create(
            text='Test text',
            author=self.user,
            group=self.group,
        )
        post_v1 = self.post

        form_data = {
            'text': 'Edited post text',
            'group': '',
        }

        response = self.authorized_client.post(
            reverse(
                'posts:post_edit', kwargs={'post_id': post_v1.id}
            ),
            data=form_data,
            follow=True,
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        error = 'Пользователь не может оставить группу пустой'
        self.assertNotEqual(post_v1.group, form_data['group'], error)

    def test_redirect_guest_client(self):
        """проверка редиректа неавторизованного пользователя"""
        self.post = Post.objects.create(
            text='Test text',
            author=self.user,
            group=self.group,
        )

        form_data = {
            'text': 'Edited post text',
            'group': self.group.id
        }

        response = self.guest_client.post(
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ),
            data=form_data,
            follow=True,
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )

    def test_guest_client_cant_create(self):
        """Проверка запрета на coздание постов"""
        """неавторизованным пользователем"""
        posts_count = Post.objects.count()

        form_data = {
            'text': 'Post text',
            'group': self.group.id
        }

        response = self.guest_client.post(
            reverse(
                'posts:post_create'
            ),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        error = 'Неавторизованный пользователь смог создать пост'
        self.assertEqual(Post.objects.count(), posts_count, error)


class CommentFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='TestName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.guest_client = Client()
        self.post = Post.objects.create(
            text='Test text',
            author=self.user
        )

    def test_comment_rights(self):
        """Проверка прав комментирования"""
        comments_count = Comment.objects.count()

        form_data = {'text': 'Cool Post'}

        self.guest_client.post(
            reverse('posts:comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comments_count)
        self.authorized_client.post(
            reverse('posts:comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(
            Comment.objects.count(),
            comments_count + 1
        )
