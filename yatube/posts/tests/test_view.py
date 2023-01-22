import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import CommentForm
from ..models import Comment, Follow, Group, Post

TEST_OF_POST = 13
SHOULD_BE = 10
User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PaginatorViewsTest(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='TestName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Test Group',
            slug='test_group',
        )
        bilk_post = []
        for i in range(TEST_OF_POST):
            bilk_post.append(Post.objects.create(
                text=f'Test text {i}',
                group=self.group,
                author=self.user,
            ))
        cache.clear()

    def test_correct_page_context_guest_client(self):
        """Проверка количества постов на первой и второй странице"""
        """Для неавторизованного пользователя"""
        pages = (
            reverse('posts:main_page'),
            reverse(
                'posts:profile', kwargs={'username': f'{self.user.username}'}
            ),
            reverse(
                'posts:posts_by_groups', kwargs={'slug': f'{self.group.slug}'}
            ),
        )

        for page in pages:
            response1 = self.guest_client.get(page)
            response2 = self.guest_client.get(page + '?page=2')
            count_posts1 = len(response1.context['page_obj'])
            count_posts2 = len(response2.context['page_obj'])
            error_name1 = (
                f'Ошибка: {count_posts1} постов'
                f' должно {SHOULD_BE}'
            )
            error_name2 = (
                f'Ошибка: {count_posts2} постов,'
                f'должно {TEST_OF_POST - SHOULD_BE}'
            )

            self.assertEqual(
                count_posts1,
                SHOULD_BE,
                error_name1
            )
            self.assertEqual(
                count_posts2,
                TEST_OF_POST - SHOULD_BE,
                error_name2,
            )

    def test_correct_page_context_authorized_client(self):
        """Проверка количества постов на первой и второй странице"""
        """Для авторизованного клиента"""
        pages = (
            reverse('posts:main_page'),
            reverse(
                'posts:profile', kwargs={'username': f'{self.user.username}'}
            ),
            reverse(
                'posts:posts_by_groups', kwargs={'slug': f'{self.group.slug}'}
            ),
        )

        for page in pages:
            response1 = self.authorized_client.get(page)
            response2 = self.authorized_client.get(page + '?page=2')
            count_posts1 = len(response1.context['page_obj'])
            count_posts2 = len(response2.context['page_obj'])
            error_name1 = (
                f'Ошибка: {count_posts1} постов'
                f' должно {SHOULD_BE}'
            )
            error_name2 = (
                f'Ошибка: {count_posts2} постов,'
                f'должно {TEST_OF_POST - SHOULD_BE}'
            )
            self.assertEqual(
                count_posts1,
                SHOULD_BE,
                error_name1
            )
            self.assertEqual(
                count_posts2,
                TEST_OF_POST - SHOULD_BE,
                error_name2,
            )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='HasNoName')

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

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='22Тестовый пост',
            image=cls.uploaded
        )

        cls.comment = Comment.objects.create(
            author=cls.user,
            post=cls.post,
            text='Cool post'
        )

        cls.user2 = User.objects.create_user(username='HasNoName2')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()  # Неавторизованный пользователь
        self.authorized_client = Client()  # второй клиент
        self.authorized_client.force_login(self.user)  # Авторизуем пользовател
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адресс использует соответствующий шаблон"""
        username = self.user.username
        post_id = self.post.id
        templates_pages_name = {
            'posts/index.html': reverse('posts:main_page'),
            'posts/group_list.html': (
                reverse('posts:posts_by_groups', kwargs={'slug': 'test-slug'})
            ),
            'posts/profile.html': (
                reverse('posts:profile', kwargs={'username': f'{username}'})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail', kwargs={'post_id': f'{post_id}'})
            ),
            'posts/create_post.html': reverse('posts:post_create'),
        }

        for template, reverse_name in templates_pages_name.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_edit_use_correct_template(self):
        """Post_edit использует корректный шаблон"""
        post_id = self.post.id
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': f'{post_id}'})
        )
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_post_detail_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        post_text_0 = {
            response.context['post'].text: self.post.text,
            response.context['post'].group: self.group,
            response.context['post'].author: self.user.username,
            response.context['post'].image: self.small_gif,
            response.context['form']: CommentForm,
            response.context['comments']: self.comment,
        }
        for value, expected in post_text_0.items():
            self.assertEqual(post_text_0[value], expected)

    def test_post_create_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:post_create'),
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        self.assertEqual(response.context.get('title'), 'Новый пост')

    def test_post_added_correctly(self):
        """Пост при создании добавлен корректно"""
        post = Post.objects.create(
            text='Test text. How it added',
            author=self.user,
            group=self.group,
        )

        response_index = self.authorized_client.get(
            reverse('posts:main_page')
        )

        response_group = self.authorized_client.get(
            reverse(
                'posts:posts_by_groups', kwargs={'slug': f'{self.group.slug}'}
            )
        )

        response_profile = self.authorized_client.get(
            reverse(
                'posts:profile', kwargs={'username': f'{self.user.username}'}
            )
        )

        index = response_index.context['page_obj']
        group = response_group.context['page_obj']
        profile = response_profile.context['page_obj']
        self.assertIn(post, index, 'поста нет на главной')
        self.assertIn(post, group, 'поста нет в профиле')
        self.assertIn(post, profile, 'поста нет в группе')

    def test_comment_added_correctly(self):
        """Комментарий появляется на странице поста"""
        comment = Comment.objects.create(
            author=self.user,
            post=self.post,
            text='Cool post'
        )

        response_comment = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': f'{self.post.id}'})
        )

        post_detail = response_comment.context['comments']
        self.assertIn(comment, post_detail, 'Комментарий не добавился')

    def test_post_added_correctly_user2(self):
        """При создании пост не добавляется в профиль другого пользователя"""
        """но виден на главной странице и в группе"""

        group2 = Group.objects.create(
            title='Test group 2',
            slug='test_group2'
        )
        before_posts_count = Post.objects.filter(group=self.group).count()
        post = Post.objects.create(
            text='Popst from another user',
            author=self.user2,
            group=group2,
        )
        response_profile = self.authorized_client.get(
            reverse(
                'posts:profile', kwargs={'username': f'{self.user.username}'}
            )
        )
        after_posts_count = Post.objects.filter(group=self.group).count()
        profile = response_profile.context['page_obj']
        self.assertEqual(
            after_posts_count, before_posts_count, 'поста нет в другой группе',
        )
        self.assertNotIn(post, profile, 'поста нет в профиле другого юзера')

    def test_main_page_uses_correct_context(self):
        """Главная страница использует правильный контекст"""
        response = self.guest_client.get(reverse('posts:main_page'))
        first_object = response.context['page_obj'][0]

        post_text_0 = first_object.text
        post_group_0 = first_object.group
        post_author_0 = first_object.author
        post_image_0 = first_object.image

        page_obj = {
            post_text_0: self.post.text,
            post_group_0: self.post.group,
            post_author_0: self.post.author,
            post_image_0: self.post.image
        }

        for post_0, expected in page_obj.items():
            self.assertEqual(post_0, expected)

        self.assertEqual(response.context.get('title'), 'Main page')
        self.assertEqual(
            response.context.get('text'),
            'Это главная страница проекта Yatube'
        )

    def test_group_page_uses_correct_context(self):
        """Страница постов по группам использует правильный контекст"""
        response = self.guest_client.get(
            reverse(
                'posts:posts_by_groups', kwargs={'slug': f'{self.group.slug}'}
            )
        )

        first_object = response.context['page_obj'][0]

        post_text_0 = first_object.text
        post_group_0 = first_object.group
        post_author_0 = first_object.author
        post_image_0 = first_object.image

        page_obj = {
            post_text_0: self.post.text,
            post_group_0: self.post.group,
            post_author_0: self.post.author,
            post_image_0: self.post.image
        }

        for post_0, expected in page_obj.items():
            self.assertEqual(post_0, expected)

        self.assertEqual(response.context.get('title'), 'Сообщества')
        self.assertEqual(
            response.context.get('group').title,
            self.group.title,
        )
        self.assertEqual(
            response.context.get('group').description,
            self.group.description,
        )

    def test_post_edit_page_uses_correct_context(self):
        """Страница редактирования поста использует корректный контекст"""
        post_id = self.post.id
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': f'{post_id}'})
        )

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        self.assertEqual(response.context.get('title'), 'Редактировать пост')
        self.assertEqual(response.context.get('is_edit'), True)
        self.assertEqual(response.context.get('post_id'), post_id)

    def test_profile_page_uses_correct_context(self):
        """В страницу профиля пользователя передан правильный контекст"""
        post_list = self.user.posts.all()
        posts_count = post_list.count()
        response = self.authorized_client.get(
            reverse(
                'posts:profile', kwargs={'username': f'{self.user.username}'}
            )
        )
        first_object = response.context['page_obj'][0]

        post_text_0 = first_object.text
        post_group_0 = first_object.group
        post_author_0 = first_object.author
        post_image_0 = first_object.image

        page_obj = {
            post_text_0: self.post.text,
            post_group_0: self.post.group,
            post_author_0: self.post.author,
            post_image_0: self.post.image
        }

        for post_0, expected in page_obj.items():
            self.assertEqual(post_0, expected)

        self.assertEqual(
            response.context.get('title'),
            f'Профайл пользователя {self.user.username}'
        )
        self.assertEqual(response.context.get('posts_count'), posts_count)
        self.assertEqual(response.context.get('author'), self.user)
        self.assertEqual(response.context.get('following'), False)
        self.assertEqual(response.context.get('is_not_author'), False)
        self.assertEqual(
            response.context.get('followers'),
            self.user.follower.count(),
        )

    def test_follow_index_uses_correct_context(self):
        """Страница постов подписок использует корректный контекст"""
        self.follow = Follow.objects.create(
            user=self.user2,
            author=self.user
        )
        response = self.authorized_client2.get(
            reverse(
                'posts:follow_index'
            )
        )

        first_object = response.context['page_obj'][0]

        post_text_0 = first_object.text
        post_group_0 = first_object.group
        post_author_0 = first_object.author
        post_image_0 = first_object.image

        page_obj = {
            post_text_0: self.post.text,
            post_group_0: self.post.group,
            post_author_0: self.post.author,
            post_image_0: self.post.image
        }

        for post_0, expected in page_obj.items():
            self.assertEqual(post_0, expected)

        self.assertEqual(response.context.get('title'), 'Following list')
        self.assertEqual(
            response.context.get('text'),
            'Your favorite authors'
        )
