from django.conf import settings
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
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='33Тестовый пост' * 50,
        )

    def test_post_str(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        post = PostModelTest.post
        expected_post_title = post.text[:settings.AMOUNT_TITLE]
        self.assertEqual(expected_post_title, str(post))

    def test_group_str(self):
        """Проверяем, что у модели Group корректно работает __str__."""
        group = PostModelTest.group
        expected_group_title = group.title
        self.assertEqual(expected_group_title, str(group))
