from http import HTTPStatus

from django.test import Client, TestCase


class StaticPagesURLTest(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_about_pages(self):
        """Проверка доступности адресов about/author и about/tech"""
        url_names = {
            '/about/author/': HTTPStatus.OK.value,
            '/about/tech/': HTTPStatus.OK.value,
        }

        for address, value in url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, value)

    def test_about_pages_templates(self):
        """Проверка использования корректного шаблона URL приложения about"""
        template_url_names = {
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/',
        }

        for template, address in template_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
